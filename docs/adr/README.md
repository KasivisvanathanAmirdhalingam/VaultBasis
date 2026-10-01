# VaultBasis — Architecture Decision Records (ADR)

This directory documents all architecturally significant decisions made for VaultBasis in accordance with the Nygard / MADR format. These decisions are frozen and binding for MMP-1 execution per PRD §0.2 and §6.4.

## ADR Register

| ADR ID | Title | Date | Status | PRD Reference |
| :--- | :--- | :--- | :--- | :--- |
| [ADR-001](ADR-001-evidence-contract-dependency-order.md) | Evidence Contract v0.1 as First Normative Engineering Artifact | 2026-09-23 | **ACCEPTED / FROZEN** | §0.2, §6.5, §13.2 |
| [ADR-002](ADR-002-deterministic-exact-decimal-vs-floating-point.md) | Strict Decimal Arithmetic and First-Class Unresolved State | 2026-09-23 | **ACCEPTED / FROZEN** | §2.1, §2.2, §15.1 |
| [ADR-003](ADR-003-zero-token-bleed-and-local-edge-boundary.md) | Zero Token Bleed and Customer-Premises Local Edge Boundary | 2026-09-23 | **ACCEPTED / FROZEN** | §2.4, §18.1, §21.1 |
| [ADR-004](ADR-004-per-installation-ed25519-signing-key.md) | Per-Installation Ed25519 Signing Keypair Model | 2026-09-23 | **ACCEPTED / FROZEN** | §6.4(B), §13.5, §44.3 |
| [ADR-005](ADR-005-named-tax-adapter-koinly-and-generic-fallback.md) | Koinly Capital Gains CSV as Sole Named Tax Adapter for Preview | 2026-09-23 | **ACCEPTED / FROZEN** | §0.2, §6.4(A) |

| [ADR-007](ADR-007-task-traceability-and-evidence-lifecycle.md) | Task traceability and evidence lifecycle | 2026-09-30 | **ACCEPTED — founder process directive** | VB-GOV-001 |

---

## Governance Rules
1. Decisions marked **ACCEPTED / FROZEN** cannot be superseded or modified during MMP-1 preview without a formal PRD amendment and version bump.
2. Every implementation module, schema, and test suite must comply with all recorded ADRs.

3. Every task records ADR impact under [the execution standard](../task_execution_standard.md). Add a decision for architecture changes; otherwise link the reviewed decision and explain no change. ADR-007 governs process and does not amend frozen assurance semantics.

First implementation batch disposition (MMP11-EXEC-001, 2026-10-01): reviewed ADR-003 and ADR-007; presentation/routing/test changes do not change assurance semantics or authorization authority. No new ADR required; detailed rationale in per-task closeouts.
