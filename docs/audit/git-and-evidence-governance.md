# Git, qualification and evidence governance

Effective directive: founder's Sept 30 roadmap/Git brief. Scope: document policy now; implement branch/protection changes only within an authorized bounded task. No branch, tag, remote setting, merge or release change was made by this documentation work.

## Branch purpose beside evidence state

| Line | Meaning | Allowed | Excluded / evidence required |
|---|---|---|---|
| `main` | Integrated product accepted through applicable gates | Qualified integration | Not automatically production verified; never means newest code |
| `release/mmp-1.1` | Controlled practitioner stabilization | UX, accessibility, distribution/security fixes required for current scope | No AI, new semantics, billing, analytics, CRM, speculative refactors or future workflows |
| `fix/mmp11-ux-001` (proposed) | Bounded convergence after blueprint review | Presentation/navigation/state integration | Start from verified release baseline; protect assurance modules; not created here |
| `fix/mmp11-dist-mac-001` | Existing Mac remediation line | Bounded native-distribution work | `83d78db` source is not recipient qualification |
| `fix/mmp11-pres-003` | Rejected historical candidate | Inspection, explicitly justified selective reuse | No wholesale resurrection; any reuse requalified against new blueprint |
| `develop/mmp-1.5` → feature lines → `release/mmp-1.5` | Future workflow stage | Approved tasks from qualified base | Not created until implementation starts; never build on active stabilization line |
| `lab/mmp-2-ai` | Experimental laboratory | Isolated research, model/mapping/extraction evaluation | Not release authority; no direct merge of experimental AI into kernel |
| Future develop/release lines | Stage-specific work when needed | Approved scope and qualification plan | No speculative branch forest |

Before any branch mutation: freshly inspect remote refs, local dirty state, unpushed commits and worktrees; compare with handover; record conflicts; preserve newer work. Current packet records cached refs only. Future branch names should encode bounded intent, e.g. `feature/mmp15-case-readiness`, `feature/mmp2-schema-mapping`, `fix/mmp11-access-email`.

## Change record kept beside each implementation

For every PR/change record: task/requirement ID, practitioner problem, before/after behavior, current source/base SHA, scope/plane, protected-path impact, decision/alternatives when material, affected routes/states/platforms, test IDs and evidence, negative controls where required, limitations, accountable reviewer, acceptance status and rollout/rollback identity. Update the traceability and stage task rows in the same change. Do not copy tokens, keys, taxpayer records or private CI/environment contents into evidence.

Assurance-plane changes require explicit architecture review and contract/version impact assessment. Presentation files that contain verification algorithms still contain protected code. Kernel tests are not allowed to be weakened to accommodate UI. Human annotations and AI suggestions cannot rewrite historical machine findings, provenance or signed receipts.

## Promotion and state model

Feature/fix → automated and applicable human validation → release line → release qualification → accepted main. Runtime promotion separately records source SHA → CI run → artifact identity → protected pre-production → browser/native/security/human evidence → qualified immutable candidate → promotion → production smoke. If integration changes source bytes or build identity, requalify the affected candidate; do not borrow acceptance from an earlier branch build.

| State | Minimum evidence required |
|---|---|
| IMPLEMENTED | Specific committed behavior and scoped diff |
| AUTOMATED_VALIDATION_PASS | Exact source/test version, commands/results, environment and relevant negative controls |
| BUILD_VERIFIED | CI run, source identity, platform/architecture, package/build checks and digest |
| PREPROD_DEPLOYED | Immutable deployment identity, URL, source/build linkage and protection boundary |
| PREPROD_QUALIFIED | Required browser, access, accessibility, UX evidence and applicable human decisions on that identity |
| DISTRIBUTION_QUALIFIED | Exact inner ZIP hash and recipient-path native evidence per OS; container digest separately recorded |
| PRODUCTION_PROMOTED | Exact qualified candidate alias/publication evidence; no rebuild substituted |
| PRODUCTION_VERIFIED | Actual public-boundary smoke and downloaded-byte identity |
| PRACTITIONER_QUALIFIED | Recorded Associate/CPA task evidence and bounded acceptance |

States are scoped per component and may be independently pending, failed, or not applicable with rationale. Git push/green CI does not confer a later state. Founder acceptance is a separate explicit decision by the founder, never a developer-generated label. Public informational pages need not inherit hosted capability authentication; protected pre-production review remains distinct from production app-level access enforcement.

Release tags identify qualified states with attached evidence (including qualified release-candidate stages), not every build attempt. Artifact identity includes stage, source SHA, CI run ID, OS/architecture, container digest where applicable, inner artifact SHA-256 and qualification state. Never instruct recipients to use “latest main.” Rollback uses a previously qualified immutable deployment/artifact, with actual-boundary smoke afterward.

## Ongoing audit maintenance

At each change, release decision and external review, reconcile traceability rows with actual files/refs/deployments. Keep dated evidence append-only in practice; corrections add an explanatory record rather than erase a failure. Hash captured artifacts and record capture tooling/environment. Enforce permissions/retention through the responsible repository/evidence system; Markdown alone does not provide immutable storage or access enforcement.

Maintain separate read-only auditor packets for product/UX, architecture, security/privacy, accessibility, native distribution, operational behavior and future AI governance. Each packet points to the same authoritative evidence rather than divergent copied PASS statements. Missing evidence stays visible. Record revocation/supersession when a candidate changes or a prior claim is disproved.
