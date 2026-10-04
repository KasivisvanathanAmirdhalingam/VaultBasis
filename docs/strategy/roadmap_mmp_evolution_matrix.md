# VaultBasis — Unified Roadmap & Evolution Matrix (MMP-1.1 through MMP-5)

> **Document Type:** Strategic Technical & Commercial Evolution Map  
> **Standard:** Granite-Grade / Left-Shift Maximum / Multi-Year System of Record  
> **Horizon:** 2026 – 2030 (Durable Record Continuity)

---

## 1. The Strategic Thesis: Beyond the October 15 Seasonal Trap

VaultBasis is **not** an "October-15-only tax file converter". While the IRS tax extension deadline on October 15 creates a sharp, recurring demand surge, treating VaultBasis as seasonal software mischaracterizes the core problem.

### 1.1 The IRS Digital-Asset Mandate & Form 1099-DA Reality
Under IRS regulations for Tax Year 2025 and 2026, brokers and digital-asset exchanges are required to furnish Form 1099-DA (reporting gross proceeds). Crucially:
- **Missing Cost Basis:** The IRS explicitly recognizes that many 1099-DA forms will omit acquisition dates and cost basis (non-covered transactions, wallet transfers, decentralized exchanges).
- **Burden of Proof:** Taxpayers and tax professionals bear strict legal responsibility to reconstruct cost basis across fragmented wallets, exchanges, and tax software ledgers, and must maintain detailed records to support every return position ([IRS Digital Asset Guidance](https://www.irs.gov/filing/digital-assets)).
- **Multi-Year Asset Holding:** An asset acquired in 2024 or 2025 and sold in 2029 requires defensible basis evidence spanning five or more years.

```
       [Fragmented Source Records]                [IRS Form 1099-DA Broker Reports]
       (Exchanges, Wallets, Ledgers)                 (Gross Proceeds Only / Missing Basis)
                     │                                            │
                     └────────────────────┬───────────────────────┘
                                          ▼
                         ┌─────────────────────────────────┐
                         │      VAULTBASIS EDGE ENGINE     │
                         │   • Deterministic Comparison    │
                         │   • Exact Decimal Arithmetic    │
                         │   • Zero-Egress Air-Gap Privacy │
                         └────────────────┬────────────────┘
                                          ▼
                      ┌───────────────────────────────────────┐
                      │    PORTABLE SIGNED OUTCOME RECEIPT    │
                      │  • Ed25519 Cryptographic Attestation  │
                      │  • Multi-Year Evidence Bundle         │
                      │  • Free Clean-Machine Verifier        │
                      └───────────────────────────────────────┘
```

The durable business model is **maintaining defensible multi-year basis history, preserving evidence lineage, and enabling third-party verification**.

---

## 2. Five-Year Horizon: Multi-Year Workload & Value Map (2026–2030)

| Calendar Year | Primary Tax-Year Workload | Why VaultBasis Remains Indispensable | CPA / EA / Firm Buyer Need | Dominant Product Layer |
|---|---|---|---|---|
| **2026** | TY2024 cleanup + TY2025 filing & extension work | Historical data migrations, missing 1099-DA basis, multi-wallet reconciliation | Rescue messy clients before Oct 15; generate defensible workpapers & evidence bundles | **MMP-1.1** (Deterministic engine) + **MMP-1.5** (Commercial control plane) |
| **2027** | TY2026 filing + prior-year amendments | Prior basis directly affects current disposals; recurring client books gain 2nd year of history | Roll prior closing basis forward automatically instead of manual re-creation | **MMP-1.5** (Workspace identity) + **MMP-2.5** (Multi-year carry-forward) |
| **2028** | TY2027 + IRS notices, audits, amendments | 3+ years of transaction lineage becomes impossible to audit without provenance | Search historical calculations, answer IRS inquiries, resolve disputed transfer chains | **MMP-2** (Evidence-grounded intelligence) |
| **2029** | TY2028 + ongoing compliance | Firms require standardized digital-asset workpaper processes across multi-seat teams | Standardize preparer/reviewer workflows, approval queues, firm-wide policy enforcement | **MMP-3** (Firm-scale operations & RBAC) |
| **2030** | TY2029 + 5-year cumulative basis history | 5-year persistent basis history becomes an irreplaceable asset; switching costs peak | Persistent multi-year basis ledger, tamper-evident audit trails, seamless staff handoff | **MMP-4** (Continuous system of record) + **MMP-5** (Ecosystem platform) |

---

## 3. Product Roadmap: MMP Scope × Technical Evolution × Release Evolution

```
MMP-1.1 (Credibility)       ───> Deterministic Reconciliation & Offline Ed25519 Receipts
         │
         ▼
MMP-1.5 (Sellability)       ───> Offline Licensing, Firm Identity, Diagnostic Isolation
         │
         ▼
MMP-2.0 (Productivity)      ───> AI/RAG Explanation Layer Grounded in Deterministic Evidence
         │
         ▼
MMP-2.5 (Retention)         ───> Multi-Year Carry-Forward, Lineage Chains & Reviewer Queues
         │
         ▼
MMP-3.0 (Enterprise Scale)  ───> RBAC, Policy Engine, Multi-Office Firm Operations
         │
         ▼
MMP-4.0 (Year-Round System) ───> Continuous Data Layer & Persistent Historical Replay
         │
         ▼
MMP-5.0 (Ecosystem Platform)───> External APIs, Verification SDK, Institutional Connectors
```

### 3.1 Detailed Evolution Matrix

| Stage | Product Role | Target Personas | Core Capabilities | Technical Architecture | Target Release | Commercial Milestone |
|---|---|---|---|---|---|---|
| **MMP-1.1** | Deterministic Foundation | CPA, EA, Tax Preparer, Reviewer | Ingestion, normalization, 13 outcome states, signed outcome receipt, evidence export, offline verification | Local deterministic engine, RFC 8785 canonicalization, Ed25519 signatures, Python/PyInstaller onedir, Win/Mac packaging | `v1.0.0-rc.x` / `v1.0.0` | **Credibility:** Proves VaultBasis produces mathematically verifiable, reproducible tax workpapers |
| **MMP-1.5** | Commercial Control Plane | Firm Admin, IT Ops, Senior Partner | Offline Ed25519 license tokens, tiers, firm/workspace identity, version/channel controls, diagnostic exporter, commercial audit log | Air-gapped license evaluator, PII-scrubbed support packager, local SQLite commercial tables, admin CLI | `v1.5.0` | **Sellability & Operability:** Enables multi-tier sales, support, and administrative control without cloud dependency |
| **MMP-2.0** | Intelligence-Assisted Review | CPA, EA, Reviewer, Forensic Accountant | Finding explanations, evidence-gap investigation, provenance trace, client-question drafting, risk summaries | Optional RAG/NLP layer over immutable evidence, strict grounding IDs, model policy toggle (zero mutation of math) | `v2.0.0` | **Productivity Advantage:** Slashes CPA review time while guaranteeing 100% deterministic ground truth |
| **MMP-2.5** | Multi-Year Continuity | CPA Firms, CAS Teams, Review Managers | Prior-year basis roll-forward, year-over-year deltas, amended return support, reviewer queues | Carry-forward contracts, multi-period state models, immutable historical state replay, change-set diffing | `v2.5.0` | **Retention & Moat:** Converts single-season users into multi-year persistent firm infrastructure |
| **MMP-3.0** | Firm-Scale Operations | Regional/National CPA Firms | Multi-preparer seats, manager review/approval workflows, workspace segmentation, standardized firm policies | RBAC, local/shared deployment modes, signed policy bundles, enterprise audit events | `v3.0.0` | **Enterprise Expansion:** Unlocks 5-figure and 6-figure firm-wide annual licensing contracts |
| **MMP-4.0** | Continuous System of Record | Accounting Teams, Family Offices | Ongoing transaction intake, quarterly reconciliation, year-round exception tracking, historical audit replay | Append-only event lineage, incremental reconciliation engine, persistent multi-year basis store | `v4.0.0` | **Year-Round Dependence:** Eliminates revenue seasonality by providing year-round basis maintenance |
| **MMP-5.0** | Ecosystem & Platform | Software Partners, Custodians, Auditors | External API, verification SDK, signed interchange formats, institutional tax software connectors | Public SDKs, versioned interchange schemas, OAuth/service auth, delegated verification network | `v5.0.0` | **Ecosystem Leverage:** VaultBasis becomes the standard verification protocol for the accounting industry |

---

## 4. Multi-Persona Value Matrix

| Persona | Initial Hook (Why Buy Year 1) | Recurring Moat (Why Keep Paying Year 2+) | Key Capabilities Used |
|---|---|---|---|
| **CPA / Tax Preparer** | Fix a nightmare crypto client before filing extension deadline | Instant annual reconciliation, automatic basis roll-forward, defensible workpapers | Ingestion, 1099-DA Matcher, Evidence Bundle Export |
| **Enrolled Agent (EA)** | Reconstruct missing cost basis for complex multi-wallet taxpayer | Support amended returns, IRS audit defense, non-covered transaction notices | Provenance Lineage, Difference Explanations, Audit Receipts |
| **Tax Reviewer / Manager** | Review preparer's calculations without re-running spreadsheets | Standardized workpaper packages, exception checklists, non-repudiable sign-off | Reviewer Workflow, Risk Summaries, Discrepancy Highlighting |
| **Forensic Accountant** | Reconstruct historical activity across disconnected exchanges | End-to-end evidence lineage, exact decimal preservation, disputed lot tracing | Exact Math Engine, Provenance Graph, Historical Replay |
| **Bookkeeper / CAS Team** | Normalize messy client CSV exports into clean ledgers | Continuous data intake, clean year-end handoff to CPA tax teams | Intake Dispatcher, Preflight Readiness Reports |
| **Firm Operations / IT** | Deploy secure software without data leak or cloud compliance risk | License management, version stability, PII-safe diagnostic support | Offline Licensing, Channel Control, Air-Gap Support Bundles |
| **Independent Auditor / IRS** | Verify taxpayer calculations without purchasing software | **Always 100% Free** offline verification; builds viral trust across ecosystem | GUI Offline Verifier, CLI Verifier, Web Verifier |

---

## 5. Three-Layer Recurring Revenue Architecture

```
Layer 3: Firm Infrastructure & Operations (Annual Firm License, Multi-Seat, Diagnostics, Channels)
   ▲
Layer 2: Multi-Year Basis Continuity (Prior-Year Roll-Forward, Lineage, Amendments, History)
   ▲
Layer 1: Core Annual Reconciliation (Completed Case Capacity, 1099-DA Verification, Evidence Bundles)
```

1. **Layer 1: Core Reconciliation Workload:** Bounded annual practice capacity based on completed reconciliation cases issuing signed Outcome Receipts.
2. **Layer 2: Multi-Year Persistent Client History:** High switching barrier as prior-year closing states, basis lots, and evidence chains roll forward into successive tax years.
3. **Layer 3: Firm Operational Infrastructure:** Multi-preparer seats, reviewer governance, diagnostic packagers, and administrative control plane that operate year-round.
