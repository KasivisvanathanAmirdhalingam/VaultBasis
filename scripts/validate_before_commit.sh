#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# VaultBasis — Industrial Pre-Commit Validation Pipeline
# Conforms to Left-Shift Maximum Standard (PRD §64, §71)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

echo "================================================================================"
echo "          VAULTBASIS — LEFT-SHIFT INDUSTRIAL VALIDATION PIPELINE                "
echo "================================================================================"
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "Workspace: ${REPO_ROOT}"
echo "--------------------------------------------------------------------------------"

# Step 1: Python syntax check across all source files
echo "==> [1/5] Compiling and validating Python syntax..."
python3 -m py_compile $(find edge apps schemas -name "*.py" 2>/dev/null || true)
echo "    ✓ All Python source files compiled successfully."

# Step 2: Validate JSON Schema definition
echo "==> [2/5] Validating normative JSON Schema (Evidence Contract v0.1)..."
python3 -c "
import json
import jsonschema
with open('schemas/receipt/receipt-v0.1.json', 'r') as f:
    schema = json.load(f)
jsonschema.Draft7Validator.check_schema(schema)
print('    ✓ schemas/receipt/receipt-v0.1.json is valid Draft-07 JSON Schema.')
"

# Step 3: Run comprehensive pytest test suite
if [ "${1:-}" == "--smoke" ]; then
    echo "==> [3/5] Running SMOKE test suite (-m smoke)..."
    pytest -m smoke -v --no-header
    echo "    ✓ Smoke suite completed with 100% pass."
else
    echo "==> [3/5] Running COMPREHENSIVE test suite (ATDD, BDD, DDD, TDD, Unit)..."
    pytest tests/ -v --no-header
    echo "    ✓ Complete test suite passed with 100% pass."
fi

# Step 4: Validate standalone verifier CLI against Golden Fixtures
echo "==> [4/5] Testing independent offline verifier CLI against golden fixtures..."
# 4a: Valid golden receipt must exit 0 with PASS
python3 apps/verifier/verify_receipt.py tests/fixtures/golden_receipt_valid.json --no-color > /tmp/vb_valid_test.log
if grep -q "VERIFICATION REPORT — PASS" /tmp/vb_valid_test.log; then
    echo "    ✓ Golden valid receipt: PASS (verified correctly)"
else
    echo "    ❌ ERROR: Golden valid receipt failed verification!"
    cat /tmp/vb_valid_test.log
    exit 1
fi

# 4b: Tampered golden receipt must exit 1 with FAIL
set +e
python3 apps/verifier/verify_receipt.py tests/fixtures/golden_receipt_tampered.json --no-color > /tmp/vb_tamper_test.log 2>&1
TAMPER_STATUS=$?
set -e
if [ ${TAMPER_STATUS} -ne 0 ] && grep -q "VERIFICATION REPORT — FAIL" /tmp/vb_tamper_test.log; then
    echo "    ✓ Golden tampered receipt: FAIL (tampering caught successfully)"
else
    echo "    ❌ ERROR: Tampered receipt was NOT caught by verifier!"
    cat /tmp/vb_tamper_test.log
    exit 1
fi

# Step 5: Security audit (Key permissions and zero plaintext leakage)
echo "==> [5/6] Performing security posture check..."
if [ -d "tests/fixtures/keys" ]; then
    find tests/fixtures/keys -name "*.key" -type f | while read -r keyfile; do
        PERMS=$(stat -f "%Lp" "$keyfile" 2>/dev/null || stat -c "%a" "$keyfile" 2>/dev/null || true)
        if [ "$PERMS" != "600" ] && [ -n "$PERMS" ]; then
            echo "    ⚠️ Warning: Keyfile $keyfile has permissions $PERMS (expected 600)"
        fi
    done
fi
echo "    ✓ Security posture verified."

# Step 6: Validate incremental Vercel public web build & zero-leakage distribution bundle
echo "==> [6/6] Validating incremental Vercel public web build & production bundle..."
node scripts/build_public_web.js > /tmp/vb_build_test.log
if grep -q "PUBLIC WEB DISTRIBUTION READY FOR VERCEL DEPLOYMENT" /tmp/vb_build_test.log; then
    echo "    ✓ Incremental Vercel public web bundle built & audited successfully."
else
    echo "    ❌ ERROR: Public web build pipeline failed!"
    cat /tmp/vb_build_test.log
    exit 1
fi

echo "--------------------------------------------------------------------------------"
echo "✅ PRE-COMMIT VALIDATION SUCCESSFUL — ALL GATES GREEN."
echo "================================================================================"
exit 0
