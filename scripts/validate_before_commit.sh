#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# VaultBasis — Industrial Pre-Commit Validation Pipeline
# Conforms to Left-Shift Maximum Standard (PRD §64, §71)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# Verify mandatory change classification policy under REGRESSION-COVERAGE-001
python3 scripts/check_change_classification.py

# Delegate industrial validation to the Python-based Categorical Runner
# This outputs the structured 11-Gate matrix table with numerical metrics
python3 scripts/run_validation_gates.py "$@"

