# VaultBasis MMP-1.5 Production Claims Evidence Ledger (LEGAL-010)

**Document ID:** `VB-CLAIMS-MMP15-001` (Control Ref: `LEGAL-010` under `MMP15-LEGAL-RISK-QUAL-001`)  
**Release Target:** VaultBasis Edge v1.5.0-rc3 & VaultBasis Public Web  
**Classification:** Canonical Control Plane for Public, Marketing, Technical & Legal Claims  
**Policy:** No marketing, technical, security, or regulatory claim may be published or presented as fact unless backed by an immutable, qualified evidence artifact and explicitly approved under this canonical taxonomy.

---

## 1. Canonical Claims Taxonomy & Control Matrix

| Canonical Claim ID | Former / Alias ID | Exact Approved Public Wording | Claim Type | Surfaces | Technical Evidence / Test Artifact | Legal Review Req? | Counsel Decision Ref | Owner | Status | Revalidation Triggers |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **`CLAIM-LOCAL-01`** | *(Canonical)* | *"VaultBasis Edge processes client reconciliation and evidence locally on your computer. Client tax records and ledger data are not uploaded to VaultBasis cloud services for normal Edge case processing."* | Data Boundary / Privacy | Marketing (`/`, `/trust`, `/pricing`), Edge UI footer, Technical guides | Continuous socket trace (SEC-01 supporting) + `test_uat28_offline_air_gapped_journey.py` | **YES** | LEGAL-001 / LEGAL-005 | Security Lead | **PRE-LAUNCH IMPLEMENTATION PASS** (GA Surface Check Pending) | Edge data-flow change, telemetry addition, cloud licensing |
| **`VERIFY-01`** | `CLAIM-CRYPTO-01`, `CLAIM-DISCLAIM-01` | *"Cryptographically signed evidence receipts using Ed25519 with SHA-256 canonical digest under Evidence Contract v0.1. Receipt integrity is verified; tax correctness is NOT determined."* | Cryptography & Tax Boundary | Edge UI, Verifier Guide, Schema docs, Verifier UI | `apps/verifier/verify_receipt.py` line 128 assertion & `test_uat24_standalone_offline_verifier.py` | **YES** | LEGAL-009 / Circular 230 | Crypto & Legal Lead | **PRE-LAUNCH IMPLEMENTATION PASS** (Counsel Review Pending) | Key size change, signature algorithm change, tax ruleset change |
| **`TAX-01`** | `CLAIM-DETERM-01`, `CLAIM-BOX2-01` | *"Deterministic reconciliation engine: identical canonical inputs under the same approved ruleset produce identical deterministic reconciliation facts, including comparison states and exact numeric variances."* | Algorithmic Determinism | Marketing (`/`), Whitepaper, Edge UI, Product Guide | `test_adversarial_reconciliation_vectors.py`, `test_uat12_box2_unreported_basis.py`, & `test_reconciliation_engine_semantic_equivalence.py` | **YES** | LEGAL-008 | Algorithm & Tax Lead | **PASS — QUALIFIED** | Engine code refactor, IRS Form 1099-DA schema revisions |
| **`SEC-01`** | `CLAIM-OFFLINE-01` | *"Qualified Edge reconciliation and evidence workflows can operate without Internet connectivity within the tested scope."* | Operational Boundary | Marketing (`/trust`), Verifier Guide, IT Security Pack | `test_uat28_offline_air_gapped_journey.py` (Functional Offline PASS; Raw PCAP Security Milestone PENDING) | No | N/A | Security Lead | **PRE-LAUNCH IMPLEMENTATION PASS** (UAT-28 PASS; Raw PCAP PENDING) | Socket binding changes, network library changes |
| **`REG-01`** | `CLAIM-TRADEMARK-01` | *"IRS Form 1099-DA is a tax form published by the Internal Revenue Service. Koinly, CoinTracker, and other referenced third-party product names are trademarks of their respective owners. Reference to them is solely for descriptive format compatibility and does not imply affiliation, sponsorship, or endorsement."* | Trademark / Fair Use | Marketing footer, Terms of Service, Edge Help | `apps/web-marketing/partials/footer.html`, `terms-of-service.html` | **YES** | LEGAL-008 | Legal Lead / Counsel | **PRE-LAUNCH IMPLEMENTATION PASS** (Counsel Review Pending) | Addition of new third-party connector parsers |
| **`CLAIM-NO-AI-01`** | *(New Distinct)* | *"VaultBasis MMP1.5 deterministic reconciliation does not use AI to determine reconciliation facts."* | Determinism / Integrity | Marketing (`/`), Trust Center | Code audit of `edge/assurance/reconciliation_engine.py` proving 0 LLM dependencies | No | N/A | Architecture Lead | **PASS — QUALIFIED** (MMP-1.5 scope) | AI feature introduced, AI provider introduced, AI processing path changed |
| **`CLAIM-DURABILITY-01`**| *(New Distinct)* | *"VaultBasis is designed to preserve customer case data in the user data directory across supported upgrades and routine uninstall/reinstall workflows; final Windows qualification remains pending."* | Data Integrity | Install Guide, IT Security Pack | `tests/unit/test_mmp15_data_durability.py` & PLAT-MAC-01 | No | N/A | Platform Lead | **PRE-SIGN PASS — MAC** (PENDING — WINDOWS) | Installer script update, path changes |
| **`CLAIM-SHUTDOWN-01`**  | *(New Distinct)* | *"VaultBasis performs a graceful shutdown and database checkpoint in the qualified normal shutdown path."* | System Integrity | Edge UI, IT Security Pack | `edge/api/app.py` & `test_uat27_crash_recovery_wal_durability.py` | No | N/A | Platform Lead | **PASS — QUALIFIED** | Daemon lifecycle changes |

---

## 2. Revalidation Triggers & Policy

Any of the following events triggers an immediate re-evaluation and mandatory re-approval of the affected claims in this ledger:
1. **Edge Data-Flow Change:** Any modification to local socket, SQLite, or file persistence paths.
2. **Telemetry Introduction:** Any proposed addition of diagnostic telemetry or crash reporting.
3. **Support Provider Change:** Integrating third-party ticketing, chat, or support desk tools.
4. **AI Introduction (MMP-2):** Incorporating generative AI, LLM parsing, or explanation models.
5. **Licensing / Cloud Integration:** Alterations to Paddle, license activation, or device verification.
6. **New Jurisdiction / Sales Territory:** Expanding commercial distribution beyond initial scope.
7. **Regulatory Pack Expansion:** Upgrading from `VB_US_1099DA_2025_R1` to future IRS tax years.

---

## 3. Publication Allowlist Rule

No marketing copy, sales deck, technical documentation, UI string, or press release may state or imply a claim that is not listed with status `PASS — QUALIFIED` or approved by founder and counsel in this ledger.
