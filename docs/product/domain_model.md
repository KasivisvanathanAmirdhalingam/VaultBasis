# VaultBasis Domain Model

## 1. Domain Entities & Responsibilities

| Entity | Domain Role | Cardinality | Privacy / Storage Boundary |
|---|---|---|---|
| **Practice / Firm** | The professional tax or accounting organization performing reviews. | 1 per license/installation | Local / Installation Configuration |
| **Client** | Local organizational container for taxpayer entity (e.g. Acme Holdings LLC). | 1:N per Practice | Local Edge SQLite only; not leaked into signed receipts. |
| **Engagement / Tax Year** | The tax reporting period and scope of professional review (e.g. 2025). | 1:N per Client | Local Edge & Receipt Metadata (`tax_year`). |
| **Reconciliation Case** | Bounded reconciliation container comparing declared evidence sources. | 1:N per Engagement | Local Edge & Receipt (`case_id`). |
| **Evidence Source** | Ingested electronic artifact (Broker 1099-DA or Tax-Ledger CSV). | Exactly 2+ per Case | Raw file stored locally in SQLite; SHA-256 fingerprint in Receipt. |
| **Canonical Transaction** | Normalized transaction record extracted from raw source data. | 1:N per Source | Local SQLite database. |
| **Reconciliation Finding** | Classified result of comparing Source A and Source B records. | 1:N per Case | Serialized in Outcome Receipt (`material_differences`, `unresolved_items`). |
| **Outcome Receipt** | Cryptographically signed portable JSON record of deterministic outcome. | 1 per Case | Signed with Ed25519; zero financial values in core payload. |

---

## 2. Invariants & Protections
- **Deterministic Assurance Kernel:** No client management logic or metering logic may alter matching, rounding, decimal arithmetic, or receipt canonicalization.
- **Privacy Separation:** Taxpayer identifiers (names, SSNs) remain local to the practitioner's Edge environment. Receipts preserve cryptographic digests (SHA-256) and record locators.
