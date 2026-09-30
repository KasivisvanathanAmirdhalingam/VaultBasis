# VaultBasis audit evidence index

Updated: 2026-09-30. **Evidence organized for review; not a claim of audit certification or release readiness.**

Use [side-by-side traceability](traceability-matrix.md) to compare requirements, protected product truth, founder observations, implementation history and verification gaps. Use [change governance](git-and-evidence-governance.md) to maintain that comparison whenever work changes. The three evidence classes remain separate even when displayed in the same row.

| Audit lens | Primary material | What is established | What remains open |
|---|---|---|---|
| Product / practitioner acceptance | [Experience map](../ux/current-experience-map.md), [blueprint](../ux/canonical-ux-blueprint.md) | Current-source inventory, limited live observations, proposed IA | Full native/authenticated audit, blueprint decision, unfamiliar-practitioner evaluation, founder acceptance |
| Architecture / deterministic integrity | [Protected evidence](../ux/evidence-register.md), [ADRs](../adr), [semantics](../reconciliation-semantics-v0.1.md) | Protected contracts identified and unchanged by this work | Exact-candidate regression and qualified evidence chain |
| Security / access control | [Traceability](traceability-matrix.md), root [API](../../api), [NFR Q10](../non_functional_requirements.md) | Source boundaries identified; observed anonymous verifier redirect | Full production negative tests, real delivery, entitlements, fixture-key disposition |
| Privacy / data handling | [Scope](../scope_and_limitations_v0.1.md), [NFR Q06/Q15/Q19](../non_functional_requirements.md) | Local/web/distribution boundaries documented | Actual-candidate network inventory, data flows/retention confirmation and appropriate policy review |
| Accessibility / usability | [MMP11-A11Y-001 ledger](../non_functional_requirements.md), live modal capture | A reproducible production keyboard failure | Full WCAG 2.2 AA evidence, VoiceOver, supported browsers/devices; no ADA claim |
| Release / supply chain / distribution | [Git governance](git-and-evidence-governance.md), [handover](../handover/VAULTBASIS_ENGINEERING_HANDOVER_2026-09-30.md) | Local refs and contradictory local artifact identity recorded | Fresh remote/CI/deployment attestation, exact recipient bytes, OS qualification and production smoke |
| Operational resilience / continuity | [NFR Q07/Q08/Q11/Q12/Q18](../non_functional_requirements.md) | Required failure/persistence/installation cases specified | Execution on qualified packages and actual service workflow |
| Product evolution / AI governance | [Roadmap](../roadmap/VAULTBASIS_PRODUCT_ROADMAP.md), five task ledgers | Proposed stage boundaries and evidence requirements | Practitioner prioritization, architecture approval, future implementation/qualification |

## Evidence provenance and handling

The founder's three controlling briefs are preserved verbatim in [directives](../handover/directives). They express requirements and reported history, not measured results. This audit's [production observations](../ux/evidence/2026-09-30/production-observations.json), screenshots, capture script and hash manifest are a dated developer evidence packet. Screenshots contain public pages only; no credentials or taxpayer evidence were submitted.

Historical files retain their original claims for auditability. Where superseded or conflicting, this index and the traceability matrix identify the discrepancy; do not silently rewrite history to imply it passed. The current founder directives control scope; frozen semantic contracts control engine behavior; implementation and deployment identity require actual evidence. Conflicts in protected semantics go to architectural review.

Each change must update its requirement/defect row, decision, affected surfaces, tests/evidence and release state side by side with the implementation. Record an explicit owner by role until a named assignee accepts it. Record pending and failed checks as prominently as passed checks. A missing timestamp/hash/identity is a gap, not something to infer from a branch name.

Public-facing reports must exclude secrets, access tokens, installation private keys, taxpayer evidence and personal data. Restricted evidence should be referenced by controlled location and digest, with access owner and retention policy; never copy it into a public repository for completeness. Retention periods and repository visibility are not determined by this packet. Record actual legal/contractual requirements with the responsible owner before setting them. A SHA-256 manifest detects changed captured files; it is not a signature, independent timestamp or attestation of the claims inside them.

Documentation maintenance is now specified, but no automated enforcement, continuous audit service, regulatory certification or guarantee of being “always audit-ready” is claimed.

Packet checks: [documentation validation](validation-2026-09-30.json) and [unsigned SHA-256 manifest](documentation-manifest.json). Validation found no broken new-packet links or missing required task fields; the three archived directives match the supplied originals byte for byte. These checks validate documentation integrity, not product behavior or release readiness.
