# VaultBasis working instructions

## Standing task and documentation contract

Apply this automatically to every task; do not wait for the founder to request documentation or traceability again. Follow `docs/task_execution_standard.md`, `docs/audit/git-and-evidence-governance.md`, and the current stage ledger. Use `docs/task_registry.json` as the machine-readable task/commit index.

1. Before work, identify or create a unique task ID in the appropriate ledger and registry. Define scope, acceptance evidence and dependencies. Do not turn planned roadmap items into implementation authorization.
2. Include task IDs in implementation commit subjects and PRs. Keep changes bounded. Never mark a task implemented with an empty, invented or pending commit reference.
3. Update technical documentation, `docs/knowledge_base.md`, `docs/status.md`, relevant ADRs/index, internal audit records and the external audit summary as part of the same task. Each task's closeout records a linked update or explicit no-change rationale for every category. Do not create meaningless ADRs or duplicate sensitive information merely to tick a box.
4. Commit the implementation and documentation. Then record its actual full SHA in the registry, task ledger and closeout record in a follow-up evidence commit. A commit cannot contain its own hash; never amend repeatedly to simulate that. Every follow-up evidence commit names its task ID; Git history identifies that evidence commit without another recursive ledger update. Multi-commit tasks list all implementation SHAs; integration/deployment identity stays separate.
5. Before declaring implementation complete, run `python3 scripts/check_task_traceability.py`; run applicable product/qualification gates. No task closure while required documentation or commit evidence is missing. Report implementation, automated validation, human acceptance and production verification separately.
6. External audit docs contain bounded factual claims and publishable references only: no credentials, private keys, taxpayer evidence, private topology, confidential findings or internal operator paths. Updating a local external-facing draft is not permission to publish/send it.

## Current scope and release boundaries

The founder accepted the takeover audit as the planning baseline and authorized controlled MMP-1.1 convergence. Baseline commit is recorded in `docs/status.md`. Application implementation starts on verified `fix/mmp11-ux-001` from `release/mmp-1.1`, never on this handover branch or main. Fetch/compare remote state before branch changes; report deviations before altering branches. Preserve and independently qualify Edge `fix/mmp11-dist-mac-001`; rejected PRES-003 is history only. No force pushes/history rewrites or speculative merges.

Do not modify reconciliation, decimal/canonicalization/parser/supported-source/provenance semantics, receipt schema/signing/verification, Golden Corpus or deterministic vectors during UX recovery. Browser verification algorithms embedded in UI files are protected too. Stop a proposal requiring protected changes, weakened access/entitlement, unsupported tax behavior, fake provisioning, production-first testing or unrelated infrastructure for architectural review.

Exact source → CI → protected pre-production → automated and human qualification → founder acceptance → release integration/requalification → immutable promotion → production smoke → accepted main. Edge separately requires exact packaged recipient-path evidence per OS. Only the founder assigns FOUNDER_UX_ACCEPTED. A planning-baseline acceptance is not UI acceptance.

MMP-1.5 is planned; MMP-2 is isolated research/lab; MMP-2.1/2.5 are planned; MMP-3 is directional. No future feature implementation is authorized in MMP-1.1 recovery. Do not spawn agents unless the user separately requests delegation.
