# VB-GOV-001 — Task execution and documentation standard

Authority: founder's standing instruction and [implementation](handover/directives/04-controlled-implementation.txt)/[promotion](handover/directives/05-branch-ci-promotion.txt) directives. Applies automatically to every implementation, fix, documentation task and qualification task. A task ID identifies work; a commit SHA identifies its implementation. “Tagged with commit ID” means linked full SHAs, not a Git release tag for every task.

## Required task record

Each task has a unique immutable ID, title, stage, owner or unassigned role, scope, dependencies, acceptance criteria, state, implementation SHAs, evidence/closeout path and documentation dispositions. `docs/task_registry.json` is the authoritative commit index; stage Markdown ledgers explain scope. Existing historical IDs remain stable. Newly assigned legacy IDs identify old rows without asserting new verification. Unresolved historical mappings are explicit migration gaps, not fabricated commits.

Task IDs appear in commit messages, e.g. `fix(MMP11-A11Y-001): contain and restore dialog focus`. Full implementation SHA(s) are recorded after the commit exists. A second `docs(MMP11-A11Y-001): record implementation traceability` commit records the first SHA, tests and documentation matrix. The second commit's identity is discoverable in Git; no self-referential hash or endless amend cycle is required. If implementation spans multiple commits, record all materially contributing SHAs and the final tested SHA. Record merge SHA, CI run, immutable deployment/package identity and acceptance separately when applicable.

## Documentation maintained beside every task

| Category | Required disposition | Canonical starting point |
|---|---|---|
| Technical documents | Actual behavior, API/state/deployment/testing changes; or specific no-impact rationale | Relevant technical guide plus [technical change register](technical_change_register.md) |
| Knowledge base | Decisions, operational lessons, known limitations and troubleshooting | [Knowledge base](knowledge_base.md) |
| Status documents | Current scoped state, blockers, evidence identity, next gate | [Current status](status.md); historical status files point here |
| ADR | New/superseding decision for architectural changes; otherwise linked reviewed ADR and no-change rationale | [ADR index](adr/README.md) |
| Internal audit | Before/after requirement, implementation SHAs, validation, risks and evidence links | [Internal audit index](audit/internal/README.md), per-task closeout, [traceability](audit/traceability-matrix.md) |
| External audit | Accurate audience-safe summary/limitations and publishable evidence references; no-change rationale if irrelevant | [External audit summary](audit/external/README.md), maintained as local draft |

All six categories are evaluated for every task. A no-change disposition must explain why; blank entries and generic “N/A” do not close a task. A frozen ADR is not rewritten for a routine CSS change. Operational/security-sensitive evidence remains internal or in controlled storage; external disclosure is separately authorized.

## Closeout gates

1. Update task ID/requirements before implementation and review protected-path impact.
2. Execute applicable tests and record exact scope, commands/results, environment and limitations. Documentation-only work gets document/traceability checks, not an invented product PASS.
3. Update all six documentation categories and the active task/defect state; record pending human/security/native gates explicitly.
4. Create bounded implementation commit(s), record full SHAs in a follow-up evidence commit, and check that each SHA resolves in Git. Never substitute HEAD for an unverified historical attribution.
5. Run `python3 scripts/check_task_traceability.py`. It checks unique IDs, commit resolution and complete documentation dispositions for current implemented tasks. It does not test product behavior, independently verify human decisions, or enforce remote branch protection. Historical imports are flagged separately and do not acquire qualification by passing this check.
6. A task is implementation-closed only when traceability is complete. A release task remains unqualified until its actual-boundary evidence exists. Reporting “IMPLEMENTED” is not permission to promote.

This standard does not authorize unrelated commits, publishing, email, deployment or promotion. Preserve untracked `.claude/` and unrelated user work. Local evidence drafts are not external publication. Standing documentation updates within an already authorized task require no repeated confirmation.
