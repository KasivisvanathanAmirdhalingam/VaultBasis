# VaultBasis Case Model

## 1. Definition of a Case
A **VaultBasis Case** is a bounded reconciliation activity in which declared evidence sources (such as Form 1099-DA broker reports and Koinly tax-ledger records) are evaluated under a defined VaultBasis semantic ruleset, producing deterministic agreements, material differences, unresolved items, cryptographic provenance, and a signed Outcome Receipt.

A Case is:
- **Not** the entire client entity.
- **Not** the completed tax return.
- **Not** a full compliance determination.
- **A bounded evidence assurance evaluation** for a declared client engagement and tax year.

---

## 2. Structural Hierarchy
```
Practice / Firm
  └── Client / Entity (e.g., Redwood Consulting LLC, CL-0042)
       └── Tax Year / Engagement (e.g., 2025 Digital Asset Review)
            ├── Reconciliation Case 1 (Coinbase 1099-DA ↔ Koinly Ledger)
            │    ├── Source A: Broker Evidence
            │    ├── Source B: Tax-Ledger Evidence
            │    ├── Deterministic Engine Execution
            │    ├── Findings (Agreements, Differences, Unresolved)
            │    └── Outcome Receipt (Ed25519 Signed)
            └── Reconciliation Case 2 (Kraken 1099-DA ↔ Ledger)
```

---

## 3. Case Lifecycle States
1. `CREATED`: Case context (Client Reference, Tax Year, Case ID) initialized.
2. `SOURCES_INGESTED`: Both required evidence sources (Broker & Tax-Ledger) received, fingerprinted (SHA-256), and validated for structural readiness.
3. `RECONCILED`: Deterministic reconciliation engine evaluated all transaction records under the declared semantic version.
4. `RECEIPT_ISSUED`: Cryptographic Ed25519 Outcome Receipt signed by the local installation key.

---

## 4. Invariants
- **VB-UX-INV-002 (Context Before Mechanics):** Every reconciliation case must establish client context, tax year, and source evidence roles before exposing execution mechanics.
- **Bounded Determinism:** Re-running a case with identical sources must yield identical deterministic results.
