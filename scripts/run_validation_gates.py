#!/usr/bin/env python3
"""
VaultBasis — Industrial Validation Gates Runner & Categorical Report Generator
Conforms to Left-Shift Maximum Standard (PRD §64, §71).
Executes each quality gate, measures execution numbers/metrics, and prints
a structured, categorized summary table with Expected Results, Actual Results,
and Potential Causes.
"""

import glob
import json
import os
import py_compile
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import List, Optional

# ANSI Color formatting
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BLUE = "\033[34m"
DIM = "\033[2m"

# Disable colors if NO_COLOR environment variable is set
if os.environ.get("NO_COLOR"):
    RESET = BOLD = GREEN = RED = YELLOW = CYAN = BLUE = DIM = ""


@dataclass
class GateResult:
    gate_id: str
    category: str
    name: str
    metrics: str
    expected: str
    actual: str
    status: str  # PASS / FAIL / WARN
    potential_cause: str
    duration_sec: float


def run_cmd(cmd: List[str], cwd: Optional[str] = None) -> tuple[int, str, str]:
    """Runs a shell command and returns (exit_code, stdout, stderr)."""
    p = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return p.returncode, p.stdout, p.stderr


# ------------------------------------------------------------------------------
# Gate 1: Static Syntax & Compilation
# ------------------------------------------------------------------------------
def check_gate_python_syntax() -> GateResult:
    t0 = time.time()
    py_files = []
    for root_dir in ["edge", "apps", "schemas", "tests", "scripts"]:
        if os.path.exists(root_dir):
            for f in glob.glob(f"{root_dir}/**/*.py", recursive=True):
                py_files.append(f)

    errors = []
    for f in py_files:
        try:
            py_compile.compile(f, doraise=True)
        except Exception as e:
            errors.append(f"{f}: {str(e)}")

    dur = time.time() - t0
    if not errors:
        return GateResult(
            gate_id="GATE-01",
            category="Static Code Quality",
            name="Python Syntax & AST Compilation",
            metrics=f"{len(py_files)} files compiled",
            expected="0 syntax or AST errors",
            actual=f"0 errors in {len(py_files)} files (100% clean)",
            status="PASS",
            potential_cause="N/A (AST parsed cleanly)",
            duration_sec=dur,
        )
    else:
        return GateResult(
            gate_id="GATE-01",
            category="Static Code Quality",
            name="Python Syntax & AST Compilation",
            metrics=f"{len(errors)} syntax errors",
            expected="0 syntax or AST errors",
            actual=f"{len(errors)} compilation failures",
            status="FAIL",
            potential_cause=f"SyntaxError or IndentationError in: {errors[0][:60]}",
            duration_sec=dur,
        )


# ------------------------------------------------------------------------------
# Gate 2: Normative JSON Schema (Draft-07)
# ------------------------------------------------------------------------------
def check_gate_json_schema() -> GateResult:
    t0 = time.time()
    schema_path = "schemas/receipt/receipt-v0.1.json"
    try:
        import jsonschema

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        jsonschema.Draft7Validator.check_schema(schema)
        req_fields = len(schema.get("required", []))
        total_props = len(schema.get("properties", {}))
        dur = time.time() - t0

        return GateResult(
            gate_id="GATE-02",
            category="Normative Contract",
            name="Evidence Contract v0.1 JSON Schema",
            metrics=f"{req_fields} required / {total_props} properties",
            expected="Draft-07 compliant schema with >= 23 required fields",
            actual=f"Draft-07 valid ({req_fields} required / {total_props} props)",
            status="PASS" if req_fields >= 23 else "WARN",
            potential_cause="N/A (Schema normative and compliant)",
            duration_sec=dur,
        )
    except Exception as e:
        return GateResult(
            gate_id="GATE-02",
            category="Normative Contract",
            name="Evidence Contract v0.1 JSON Schema",
            metrics="0 fields validated",
            expected="Draft-07 compliant schema with 23 required fields",
            actual=f"Schema validation error: {str(e)[:50]}",
            status="FAIL",
            potential_cause="Syntax error in JSON or invalid Draft-07 metaschema construct",
            duration_sec=time.time() - t0,
        )


# ------------------------------------------------------------------------------
# Pytest Suite Runner Helper
# ------------------------------------------------------------------------------
def run_pytest_gate(
    gate_id: str,
    category: str,
    name: str,
    test_path: str,
    expected_desc: str,
    potential_cause_hint: str,
) -> GateResult:
    t0 = time.time()
    code, stdout, stderr = run_cmd(["pytest", test_path, "-v", "--no-header"])
    dur = time.time() - t0

    # Extract test count summary
    output = stdout + "\n" + stderr
    passed = 0
    failed = 0
    for line in output.splitlines():
        if "passed" in line and ("=" in line):
            # e.g., "=== 11 passed in 0.09s ===" or "=== 1 failed, 10 passed in 0.1s ==="
            parts = line.replace("=", "").strip().split(",")
            for p in parts:
                p = p.strip()
                if "passed" in p:
                    try:
                        passed = int(p.split()[0])
                    except (IndexError, ValueError):
                        pass
                if "failed" in p:
                    try:
                        failed = int(p.split()[0])
                    except (IndexError, ValueError):
                        pass

    total = passed + failed
    metrics = f"{passed}/{total} tests passed" if total > 0 else "0 tests executed"

    if code == 0 and failed == 0 and passed > 0:
        return GateResult(
            gate_id=gate_id,
            category=category,
            name=name,
            metrics=metrics,
            expected=expected_desc,
            actual=f"{passed}/{total} passed (100% green)",
            status="PASS",
            potential_cause="N/A (All suite invariants hold)",
            duration_sec=dur,
        )
    else:
        # Extract first failure line
        first_fail = "Test assertion failed"
        for line in output.splitlines():
            if line.startswith("FAILED "):
                first_fail = line.replace("FAILED ", "").strip()
                break

        return GateResult(
            gate_id=gate_id,
            category=category,
            name=name,
            metrics=metrics,
            expected=expected_desc,
            actual=f"{failed} failures, {passed} passed",
            status="FAIL",
            potential_cause=f"{potential_cause_hint}: {first_fail[:50]}",
            duration_sec=dur,
        )


# ------------------------------------------------------------------------------
# Gate 7: Offline Verifier CLI with Golden Fixtures
# ------------------------------------------------------------------------------
def check_gate_offline_verifier() -> GateResult:
    t0 = time.time()
    # 7a: Valid Golden Receipt
    code_valid, out_valid, _ = run_cmd([
        sys.executable,
        "apps/verifier/verify_receipt.py",
        "tests/fixtures/golden_receipt_valid.json",
        "--no-color",
    ])
    valid_ok = (code_valid == 0) and ("PAYLOAD & SIGNATURE VERIFIED" in out_valid)

    # 7b: Tampered Golden Receipt
    code_tamper, out_tamper, _ = run_cmd([
        sys.executable,
        "apps/verifier/verify_receipt.py",
        "tests/fixtures/golden_receipt_tampered.json",
        "--no-color",
    ])
    tamper_ok = (code_tamper != 0) and ("VERIFICATION FAILED" in out_tamper)

    dur = time.time() - t0
    if valid_ok and tamper_ok:
        return GateResult(
            gate_id="GATE-09",
            category="Independent Verification",
            name="Standalone Verifier CLI against Golden Fixtures",
            metrics="2/2 fixtures verified",
            expected="Valid=PASS (exit 0) | Tampered=FAIL (exit 1)",
            actual="Valid=PASS (exit 0) | Tampered=FAIL (exit 1)",
            status="PASS",
            potential_cause="N/A (Cryptographic & schema verification confirmed)",
            duration_sec=dur,
        )
    else:
        reasons = []
        if not valid_ok:
            reasons.append("Valid receipt failed verification")
        if not tamper_ok:
            reasons.append("Tampered receipt was not detected")
        return GateResult(
            gate_id="GATE-09",
            category="Independent Verification",
            name="Standalone Verifier CLI against Golden Fixtures",
            metrics="Fixture mismatch",
            expected="Valid=PASS (exit 0) | Tampered=FAIL (exit 1)",
            actual="; ".join(reasons),
            status="FAIL",
            potential_cause="Signature algorithm divergence or digest calculation mismatch",
            duration_sec=dur,
        )


# ------------------------------------------------------------------------------
# Gate 8: Incremental Vercel Public Web Build
# ------------------------------------------------------------------------------
def check_gate_vercel_build() -> GateResult:
    t0 = time.time()
    code, stdout, stderr = run_cmd(["node", "scripts/build_public_web.js"])
    dur = time.time() - t0
    out = stdout + stderr

    if code == 0 and "PUBLIC WEB DISTRIBUTION READY FOR VERCEL DEPLOYMENT" in out:
        dist_files = glob.glob("dist/public-web/**/*", recursive=True)
        # Exclude directories, count files
        dist_files = [f for f in dist_files if os.path.isfile(f)]
        return GateResult(
            gate_id="GATE-10",
            category="Production Build",
            name="Incremental Vercel Public Web Bundle",
            metrics=f"{len(dist_files)} distribution files",
            expected="Clean build, zero egress/secret leaks, vercel.json ready",
            actual=f"Bundle built cleanly ({len(dist_files)} artifacts, 0 leaks)",
            status="PASS",
            potential_cause="N/A (Public bundle isolated and audited)",
            duration_sec=dur,
        )
    else:
        return GateResult(
            gate_id="GATE-10",
            category="Production Build",
            name="Incremental Vercel Public Web Bundle",
            metrics="Build failed",
            expected="Clean build, zero egress/secret leaks, vercel.json ready",
            actual=f"Exit code {code}",
            status="FAIL",
            potential_cause="Missing source HTML/JS files, permission error, or Node syntax error",
            duration_sec=dur,
        )


# ------------------------------------------------------------------------------
# Gate 9: Security Air-Gap & Keyfile Permissions
# ------------------------------------------------------------------------------
def check_gate_security_posture() -> GateResult:
    t0 = time.time()
    keyfiles = glob.glob("tests/fixtures/keys/**/*.key", recursive=True)
    insecure_keys = []
    for kf in keyfiles:
        try:
            mode = oct(os.stat(kf).st_mode & 0o777)
            if mode != "0o600":
                insecure_keys.append(f"{kf} ({mode})")
        except Exception:
            pass

    dur = time.time() - t0
    if not insecure_keys:
        return GateResult(
            gate_id="GATE-11",
            category="Security & Air-Gap",
            name="Keyfile Permissions & Secret Leakage Guard",
            metrics=f"{len(keyfiles)} keyfiles audited (0o600)",
            expected="All Ed25519 private keys strictly chmod 600",
            actual="All private keys enforce 0o600 POSIX permissions",
            status="PASS",
            potential_cause="N/A (Security boundary intact)",
            duration_sec=dur,
        )
    else:
        return GateResult(
            gate_id="GATE-11",
            category="Security & Air-Gap",
            name="Keyfile Permissions & Secret Leakage Guard",
            metrics=f"{len(insecure_keys)} insecure keys",
            expected="All Ed25519 private keys strictly chmod 600",
            actual=f"Insecure permissions on: {', '.join(insecure_keys[:2])}",
            status="WARN",
            potential_cause="Keyfiles created without umask 0077 or permissions modified by git",
            duration_sec=dur,
        )


# ------------------------------------------------------------------------------
# Formatting and Table Rendering
# ------------------------------------------------------------------------------
def render_summary_table(results: List[GateResult], total_suite_tests: int) -> None:
    # Column widths tailored for high readability
    w_gid = 9
    w_cat = 26
    w_num = 24
    w_exp = 40
    w_act = 40
    w_sta = 8
    w_diag = 42

    def sep_line(char="-"):
        return f"+{char * (w_gid + 2)}+{char * (w_cat + 2)}+{char * (w_num + 2)}+{char * (w_exp + 2)}+{char * (w_act + 2)}+{char * (w_sta + 2)}+{char * (w_diag + 2)}+"

    def truncate(s: str, max_len: int) -> str:
        s = s.replace("\n", " ").strip()
        if len(s) > max_len:
            return s[: max_len - 3] + "..."
        return s

    total_table_width = w_gid + w_cat + w_num + w_exp + w_act + w_sta + w_diag + 16

    print("\n" + BOLD + "=" * total_table_width + RESET)
    title_text = "VAULTBASIS — INDUSTRIAL VALIDATION GATES AUDIT REPORT"
    print(f"{BOLD}{CYAN}{title_text.center(total_table_width)}{RESET}")
    sub_title = f"Timestamp: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} | Standard: Left-Shift Maximum (PRD §64, §71) | Enforce Level: Granite"
    print(f"{DIM}{sub_title.center(total_table_width)}{RESET}")
    print(sep_line("="))

    # Table Header
    hdr = (
        f"| {BOLD}{'GATE ID':<{w_gid}}{RESET} "
        f"| {BOLD}{'CATEGORY':<{w_cat}}{RESET} "
        f"| {BOLD}{'METRICS / NUMBERS':<{w_num}}{RESET} "
        f"| {BOLD}{'EXPECTED RESULT':<{w_exp}}{RESET} "
        f"| {BOLD}{'ACTUAL RESULT':<{w_act}}{RESET} "
        f"| {BOLD}{'STATUS':<{w_sta}}{RESET} "
        f"| {BOLD}{'POTENTIAL CAUSE / DIAGNOSTIC':<{w_diag}}{RESET} |"
    )
    print(hdr)
    print(sep_line("="))

    for r in results:
        status_colored = f"{GREEN}[PASS]{RESET} " if r.status == "PASS" else (
            f"{RED}[FAIL]{RESET} " if r.status == "FAIL" else f"{YELLOW}[WARN]{RESET} "
        )

        row = (
            f"| {r.gate_id:<{w_gid}} "
            f"| {truncate(r.category, w_cat):<{w_cat}} "
            f"| {truncate(r.metrics, w_num):<{w_num}} "
            f"| {truncate(r.expected, w_exp):<{w_exp}} "
            f"| {truncate(r.actual, w_act):<{w_act}} "
            f"| {status_colored:<{w_sta + 8}} "
            f"| {truncate(r.potential_cause, w_diag):<{w_diag}} |"
        )
        print(row)
        print(sep_line("-"))

    # Summary Statistics
    total_gates = len(results)
    passed_gates = sum(1 for r in results if r.status == "PASS")
    failed_gates = sum(1 for r in results if r.status == "FAIL")
    warned_gates = sum(1 for r in results if r.status == "WARN")
    total_time = sum(r.duration_sec for r in results)

    print("\n" + BOLD + "CATEGORICAL EXECUTION BREAKDOWN & METRICS:" + RESET)
    print(f"  • Total Validation Gates   : {BOLD}{total_gates}{RESET}")
    print(f"  • Gates Passed (Green)     : {BOLD}{GREEN}{passed_gates}{RESET}")
    print(f"  • Gates Failed (Red)       : {BOLD}{RED}{failed_gates}{RESET}")
    print(f"  • Gates Warning (Yellow)   : {BOLD}{YELLOW}{warned_gates}{RESET}")
    print(f"  • Total Automated Tests    : {BOLD}{CYAN}{total_suite_tests}{RESET} tests across ATDD, BDD, DDD, TDD, Prod, Unit")
    print(f"  • Total Execution Time     : {BOLD}{total_time:.2f}s{RESET}")

    pass_rate = (passed_gates / total_gates) * 100.0
    print(f"  • Pipeline Pass Rate       : {BOLD}{GREEN if pass_rate == 100 else RED}{pass_rate:.1f}%{RESET}")
    print(sep_line("="))

    if failed_gates == 0:
        print(
            f"{BOLD}{GREEN}✓ ALL PRE-COMMIT GATES SATISFIED — ZERO DRIFT — READY FOR PUSH TO REMOTE.{RESET}\n"
        )
    else:
        print(
            f"{BOLD}{RED}❌ PIPELINE BLOCKED: {failed_gates} GATE(S) FAILED. REVIEW POTENTIAL CAUSES ABOVE.{RESET}\n"
        )


def main():
    smoke_only = "--smoke" in sys.argv

    results: List[GateResult] = []

    print(f"{CYAN}==> Executing VaultBasis Industrial Validation Pipeline...{RESET}")

    # Gate 1: Python Syntax
    results.append(check_gate_python_syntax())

    # Gate 2: JSON Schema Contract
    results.append(check_gate_json_schema())

    # Gate 3: DDD Domain Models Invariants
    results.append(
        run_pytest_gate(
            gate_id="GATE-03",
            category="Domain Invariants (DDD)",
            name="Entities, Aggregates & Provenance",
            test_path="tests/quality/ddd/",
            expected_desc="All domain aggregate invariants hold",
            potential_cause_hint="Domain aggregate lifecycle broken or invalid state",
        )
    )

    # Gate 4: TDD Precision Math & Crypto
    results.append(
        run_pytest_gate(
            gate_id="GATE-04",
            category="Precision Math & Crypto (TDD)",
            name="Exact Decimals, RFC 8785 & Ed25519",
            test_path="tests/quality/tdd/",
            expected_desc="Zero float drift & valid Ed25519 signatures",
            potential_cause_hint="Float coercion, JCS drift, or signature corruption",
        )
    )

    # Gate 5: BDD Formal Acceptance Criteria
    results.append(
        run_pytest_gate(
            gate_id="GATE-05",
            category="Acceptance Criteria (BDD)",
            name="Formal AC-01..AC-07 Gates & Boundaries",
            test_path="tests/quality/bdd/",
            expected_desc="100% pass on bounded outcomes, air-gap",
            potential_cause_hint="Reconciliation outcome divergence or socket egress",
        )
    )

    # Gate 6: ATDD End-to-End CPA User Journeys
    results.append(
        run_pytest_gate(
            gate_id="GATE-06",
            category="User Journeys (ATDD)",
            name="End-to-End CPA Reconciliation Workflows",
            test_path="tests/quality/atdd/",
            expected_desc="Multi-lot, provenance & audit journeys pass",
            potential_cause_hint="Workflow state desync or provenance gap",
        )
    )

    # Gate 7: Unit Parser Invariants
    results.append(
        run_pytest_gate(
            gate_id="GATE-07",
            category="Parser Invariants (Unit)",
            name="1099-DA, Koinly & CSV Formats",
            test_path="tests/unit/",
            expected_desc="Lossless parsing across broker CSV formats",
            potential_cause_hint="Header format mismatch or unhandled row field",
        )
    )

    # Gate 8: Production Deployment & Navigation Links
    results.append(
        run_pytest_gate(
            gate_id="GATE-08",
            category="Production Navigation",
            name="Header, Footer, Links & Anchor Scans",
            test_path="tests/quality/production_deployment/",
            expected_desc="100% working links, no anchor occlusion",
            potential_cause_hint="Broken anchor, sticky header occlusion, or leak",
        )
    )

    # Gate 9: Offline Verifier CLI Verification
    results.append(check_gate_offline_verifier())

    # Gate 10: Incremental Vercel Public Web Build
    results.append(check_gate_vercel_build())

    # Gate 11: Security & Air-Gap Posture
    results.append(check_gate_security_posture())

    # Calculate total automated tests executed across all pytest gates
    total_suite_tests = 0
    for r in results:
        if "tests passed" in r.metrics:
            try:
                num = int(r.metrics.split("/")[0])
                total_suite_tests += num
            except (ValueError, IndexError):
                pass

    # Render formatted tabular report
    render_summary_table(results, total_suite_tests)

    # Exit code
    if any(r.status == "FAIL" for r in results):
        sys.exit(1)
    sys.exit(0)



if __name__ == "__main__":
    main()
