# ADR 006: Industrial Validation Gates & Categorical Execution Strategy

## Status
Accepted

## Context
As the VaultBasis implementation advances across multiple workstreams (Quality, Security, Compliance, UI/UX), the definition of "Left-Shift Maximum" and "Granite-level standard" necessitates an immutable pre-commit validation pipeline. Initially, a Bash script (`validate_before_commit.sh`) orchestrated tests. However, as the number of gates expanded (ATDD, BDD, TDD, DDD, Unit, Verifier, Build, Security), bash's linear failure mode and text parsing lacked the structured reporting, telemetry, and exact tabular categorization required for a deterministic industrial quality audit.

## Decision
We implemented a robust Python-based runner (`scripts/run_validation_gates.py`) that executes 11 distinct quality and security gates as independent, hermetic sub-processes. The runner acts as the single source of truth for the entire pipeline, replacing fragmented Bash logic.

Key aspects:
1. **Categorical ASCII Reporting**: Outputs a strict matrix with columns for Gate ID, Category, Metrics, Expected Result, Actual Result, Status, and Potential Cause.
2. **Deterministic Pre-conditions**: Ensures compliance with Draft-07 JSON Schema and RFC 8785 without ambiguous toolchain failures.
3. **Fail-Fast vs. Aggregate Reporting**: The runner collects results across all 11 gates and only emits a final status based on total aggregation, ensuring complete visibility before exit.

## Consequences
- **Positive**: Complete transparency into the test suite and build pipeline before any code is committed. Immediate alignment with the "Left-Shift Maximum" philosophy.
- **Negative**: Adds a slight overhead to local pre-commit checks (approx 8.5 seconds), which is an acceptable tradeoff for zero-drift assurance.
