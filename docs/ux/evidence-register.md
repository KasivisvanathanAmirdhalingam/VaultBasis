# Evidence register

## 1. Protected product truth

These define the system's boundaries. Existing presentation is not authoritative.

| ID | Evidence | Protection / permitted interpretation |
|---|---|---|
| P01 | [Reconciliation semantics](../reconciliation-semantics-v0.1.md), [canonical models](../../schemas/canonical), [engine](../../edge/assurance/reconciliation_engine.py), [connectors](../../edge/connectors) | Preserve matching, exact decimals, supported-source interpretation, outcome states, provenance and unresolved information. Do not invent resolution in UI. |
| P02 | [Receipt contract](../../schemas/receipt), [signing implementation](../../edge/receipts), [independent verifier](../../apps/verifier/verify_receipt.py) | Preserve schema, canonicalization, signing and verification algorithms. Browser verification routines are protected too, even when embedded in a presentation file. |
| P03 | [ADRs](../adr), [Scope & Limitations](../scope_and_limitations_v0.1.md) | Local evidence processing; separate web/access and distribution activities. Integrity under a declared key does not independently authenticate installation identity, source truth, tax correctness or legal compliance. |
| P04 | [Golden Corpus](../../tests/quality/golden), [canonical vectors](../../tests/fixtures/canonical_vectors_v0.1.json), [equivalence projection](../../schemas/receipt/equivalence-projection-v0.1.json) | Frozen regression evidence; no changed expectations, weakened assertions, or expanded supported limits to make UX pass. |
| P05 | [Entitlement](../../api/entitlement-store.js), [download](../../api/download.js), [preview access](../../api/preview-access-store.js), [session](../../api/verifier-session.js), [page gate](../../api/verifier-page.js), [build](../../scripts/build_public_web.js) | Server-side access enforcement. Preview credentials authorize Web Verifier sessions; separate artifact-bound entitlements authorize downloads. Do not publish static verifier HTML as a bypass. |
| P06 | [Seven gates](../preview_gates_certification.md), [offline ceremony](../AC06_Offline_Ceremony_Evidence.md), [egress record](../AC07_OS_Level_Egress_Evidence.md) | Retain as historical engineering evidence with original scope. Seven-gate report is dated Sept 26; offline ceremony Sept 27. Egress report names RC1 and leaves package hash pending. None qualifies today's deployed site or current native candidate. No fresh test PASS is asserted here. |

Normative documents can contain historical wording broader than the current founder boundary. In particular, the verification specification's reference to origin from the declared installation key must not become an independently authenticated installation claim. Flag semantic conflicts for architecture review; do not edit the verifier contract during presentation work.

## 2. Founder acceptance evidence

| ID | Evidence / provenance | Meaning and limit |
|---|---|---|
| F01 | Current founder request and supplied MMP11-UX-001 directive | Repeated confusion, redundant navigation, unprofessional presentation, and the need for a coherent practitioner journey are acceptance requirements. These observations are not invalidated by passing tests. |
| F02 | [Prior handover §§2–5, 13](../handover/VAULTBASIS_ENGINEERING_HANDOVER_2026-09-30.md) | Records founder rejection of PRES-003 and prior Mac defects. Original founder screenshot files were not supplied with this request or located in the inspected documentation/artifact paths. Preserve the report as attributed testimony, not an independently inspected screenshot. |
| F03 | [Live browser capture](evidence/2026-09-30/production-observations.json) and adjacent PNGs | New developer observations, not founder observations or founder approval. Records URL, timestamp, browser, viewport, headings, links, console errors and screenshots. Anonymous/read-only; no access request or email sent. |

The founder's verdict remains **not accepted** until the founder explicitly reviews the exact deployed candidate. Screenshots may support that review but cannot issue it. Each future founder observation should record URL or package hash, timestamp, device, task, expected behavior, observed behavior, attachment, severity and acceptance decision.

## 3. Implementation history

Read-only local Git inspection on Sept 30; remote-tracking refs were not freshly fetched.

| Item | Observed / reported identity | Interpretation |
|---|---|---|
| Current checkout | `docs/engineering-handover-2026-09-30` at `70606ff` | Documentation handover branch; source review in this packet uses this checkout unless marked otherwise. |
| Main / release baseline | Local `main` and `release/mmp-1.1` at `73a4523` | History, not proof of what production serves. |
| Rejected presentation candidate | Local `586a83c`; cached remote ref `73a4523` | Do not cherry-pick it as the design specification. |
| Mac remediation candidate | Local/cached remote `83d78db` | Source contains `/offline-verifier` and explicit external destinations. Source changes do not prove recipient-path behavior. |
| Local Mac manifest | `dist/VaultBasis-RC3-macOS-arm64.manifest.json` declares `98b7e6fa…`, unsigned, unqualified | Not the named `83d78db` candidate. Local manifest claims are not an independently verified artifact hash. Do not substitute this package for current candidate qualification. |
| Windows | Handover references `5dc4962`; CI/artifact identity unresolved | Establish fresh run ID, SHA, artifact/container digest, inner ZIP hash and supported Windows version before qualification. |
| Production | Live anonymous HTTPS checked Sept 30 | HTML build metadata can help attribution; exact immutable deployment ID, alias mapping and source attestation still require deployment records. Public marketing access is not itself a security failure. |
| Initial working tree | Untracked `.claude/` | Left untouched. No worktree cleanup, checkout, merge, deployment or promotion. |

A material handover discrepancy: §7 describes request access writing a preview-access record. The inspected root `api/request-access.js` instead creates an artifact entitlement, sends through Ethereal, and does not call preview-access creation. `api/verifier-session.js` explicitly requires a separate preview credential. Root API source is the implementation evidence; the handover description cannot be treated as proof of an end-to-end access workflow.

CI and deployment claims remain historical until tied to an exact candidate. Record source SHA → build/run ID → immutable deployment URL or inner package hash → browser/native evidence → human sign-off → promotion → production smoke. Do not infer Windows parity from a Mac pass.
