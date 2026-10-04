# MMP-2 Persistence & Zero-Drift Upgrade Invariant

> **Specification Ref:** `MMP2-UPG-001`, `MMP2-IDX-001`  
> **Core Concept:** Preserving Existing Localhost Customer Data Across All MMP-2 Upgrades

---

## 1. Canonical vs. Derived Storage Hierarchy

MMP-2 maintains a strict boundary between immutable canonical customer data and disposable AI indexes:

```
CANONICAL DATA (AUTHORITATIVE & PERMANENT)
├── data/vaultbasis.db       (SQLite: Cases, Sources, Transactions, Receipts, Firm Identity)
└── data/evidence/           (Raw CSVs, Broker 1099-DAs, PDF Statements)

DERIVED DATA (DISPOSABLE & REBUILDABLE CACHE)
└── intelligence/
    ├── indexes/case_vectors/       (Chroma / FAISS vector index of active case)
    ├── indexes/regulatory_vectors/ (IRS knowledge base vectors)
    ├── cache/model_kv_cache/       (Local inference prompt cache)
    └── models/                     (Installed GGUF model weights)
```

### The Disposable Rebuild Invariant:
If the entire `intelligence/` directory is deleted, corrupted, or wiped:
- Zero customer financial data or case state is lost.
- The Core Daemon functions without interruption.
- The Intelligence Sidecar automatically rebuilds the vector indexes from canonical SQLite tables.

---

## 2. Upgrade Path for Existing Installations

When an existing MMP-1.1 / MMP-1.5 practitioner upgrades to MMP-2:

```
EXISTING MMP-1.x INSTALLATION (data/vaultbasis.db)
                     │
                     ▼
          MMP-2 UPGRADE DETECTOR
                     │
                     ├─ 1. Create Pre-Upgrade Backup (PRAGMA backup API)
                     ├─ 2. Run Database Integrity Check (PRAGMA integrity_check)
                     ├─ 3. Execute Transactional Migrations (schema_migrations)
                     ├─ 4. Verify Existing Receipts & File Hashes UNCHANGED
                     ├─ 5. Mount Intelligence Sidecar on Loopback
                     └─ 6. Build Initial Derived Vector Indexes in Background
```

### Immutable Upgrade Invariant:
All existing signed outcome receipts (`receipt_id`, Ed25519 signature, SHA-256 evidence digests) must evaluate to byte-for-byte identical verification results before and after the MMP-2 upgrade.
