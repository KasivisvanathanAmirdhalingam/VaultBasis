# MMP15-PRACTICE-001 — Client / Engagement / Case Architecture

> **Status:** FUTURE DESIGN RECORD (MMP-1.5 SPECIFICATION) — NOT IMPLEMENTED IN MMP-1.1

## 1. Practice Hierarchy
```
Practice / Firm Workspace
  └── Client Registry (Create / Read / Update / Archive)
       └── Tax Year / Engagement Workpapers
            ├── Cases (Broker ↔ Ledger Comparisons)
            ├── Reviewer Lifecycle Queue
            └── Exported Assurance Workpaper Bundles
```

---

## 2. Client Lifecycle Considerations
- **Non-Destructive Archiving:** In an evidence-assurance product, client records and associated receipts must support archiving rather than immediate hard deletion to preserve accounting record-retention requirements.
- **Preparer → Reviewer Workflow:**
  - `Preparer Stage:` Ingests sources, validates readiness, runs reconciliation, tags initial notes.
  - `Reviewer Stage:` Reviews material differences, confirms workpaper disposition, issues signed Outcome Receipt.

---

## 3. Privacy & PII Boundary
Client display names and notes remain strictly local to the practitioner's installation database and must never be leaked into portable receipts or external verifier logs.
