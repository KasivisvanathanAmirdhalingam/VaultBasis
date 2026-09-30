# ADR-007 — Task traceability and evidence lifecycle

Status: ACCEPTED — founder-directed process requirement. Task: VB-GOV-001. Date: 2026-09-30. Scope: engineering workflow, not assurance semantics.

## Context

Historical records mix implementation, CI, UX acceptance and production qualification; some tasks lack stable IDs or exact commits. The founder requires documentation and audit evidence to evolve with every task without repeated prompting.

## Decision

Use a stable task ID and full implementation commit IDs, with the six-category documentation closeout defined in [the execution standard](../task_execution_standard.md). Preserve accepted planning artifacts as a committed baseline. Distinguish internal operational evidence from external-facing factual summaries. Keep a machine-readable registry and validate it before task closure.

Record an implementation SHA in a subsequent evidence commit rather than attempting a self-referential hash. Follow-up evidence commits identify the task in their subject; their own identity is supplied by Git. Do not create per-task release tags. Qualified release tags retain their separate promotion meaning.

Documentation no-impact decisions require a rationale. Routine implementation does not require a new architecture decision; architecture-affecting work does. Protected ADRs/contracts are unchanged. Historical evidence remains attributed and unresolved where identity cannot be established.

## Consequences

Small evidence follow-up commits are expected. Audit readiness becomes an explicit task gate, with current status and disclosure boundaries, rather than a retrospective exercise. The local checker helps detect missing links; it is not a remote CI/protection guarantee or independent certification. New evidence must still be verified at the correct runtime boundary.
