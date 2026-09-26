# VaultBasis — Architecture Decision Records (ADR)

This directory documents all architecturally significant decisions made for VaultBasis in accordance with the Nygard / MADR format. These decisions are frozen and binding for MMP-1 execution per PRD §0.2 and §6.4.

## ADR Register

| ADR ID | Title | Date | Status | PRD Reference |
| :--- | :--- | :--- | :--- | :--- |
| [ADR-001](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/adr/ADR-001-evidence-contract-dependency-order.md) | Evidence Contract v0.1 as First Normative Engineering Artifact | 2026-09-23 | **ACCEPTED / FROZEN** | §0.2, §6.5, §13.2 |
| [ADR-002](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/adr/ADR-002-deterministic-exact-decimal-vs-floating-point.md) | Strict Decimal Arithmetic and First-Class Unresolved State | 2026-09-23 | **ACCEPTED / FROZEN** | §2.1, §2.2, §15.1 |
| [ADR-003](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/adr/ADR-003-zero-token-bleed-and-local-edge-boundary.md) | Zero Token Bleed and Customer-Premises Local Edge Boundary | 2026-09-23 | **ACCEPTED / FROZEN** | §2.4, §18.1, §21.1 |
| [ADR-004](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/adr/ADR-004-per-installation-ed25519-signing-key.md) | Per-Installation Ed25519 Signing Keypair Model | 2026-09-23 | **ACCEPTED / FROZEN** | §6.4(B), §13.5, §44.3 |
| [ADR-005](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/adr/ADR-005-named-tax-adapter-koinly-and-generic-fallback.md) | Koinly Capital Gains CSV as Sole Named Tax Adapter for Preview | 2026-09-23 | **ACCEPTED / FROZEN** | §0.2, §6.4(A) |

---

## Governance Rules
1. Decisions marked **ACCEPTED / FROZEN** cannot be superseded or modified during MMP-1 preview without a formal PRD amendment and version bump.
2. Every implementation module, schema, and test suite must comply with all recorded ADRs.
