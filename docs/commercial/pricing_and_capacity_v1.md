# VaultBasis Commercial Policy Contract: Pricing, Capacity & Entitlement Semantics (v1.0)

> **Document Status:** NORMATIVE COMMERCIAL CONTRACT  
> **Release Target:** MMP-1.5 Production Commercial Readiness  
> **Governing Implementation:** `edge/commercial/policy.py` (`CommercialPolicyService`), `edge/commercial/models.py` (`LicenseToken`), `tools/issue_license.py`

---

## 1. Core Principles & Cryptographic Invariants

1. **Equal Mathematical Truth Across All Tiers:**  
   Every tier—from free Evaluation through Enterprise—receives the exact same deterministic reconciliation math, precision Decimal arithmetic, Evidence Contract v0.1 schema rules, and cryptographic Ed25519 outcome verification. Commercial tiers differentiate strictly by **production case capacity, practitioner workflow, and support operations**, never by "better tax truth."
2. **Independent Verification is Unmetered and Free:**  
   Verifying any signed Outcome Receipt (via offline CLI or browser WebCrypto) is free, unmetered, and requires no license or network connection.
3. **No Ransom of Historical Workpapers:**  
   An expired license prevents the creation of *new* production cases, but **never locks, deletes, or ransoms existing cases, audit logs, or exported evidence**. Historical work remains 100% readable, inspectable, and exportable locally forever.

---

## 2. Commercial Tier Catalog

| Dimension | Free Evaluation | Solo Practitioner (Essential) | Practice Firm (Most Popular) | Enterprise & Firm |
|---|---|---|---|---|
| **Annual Fee** | **$0** (No credit card) | **$499** / license term | **$1,499** / license term | **$3,999+** / license term |
| **Target Persona** | Exploring math & testing verifier | Solo CPAs, EAs, boutique practices | Multi-preparer CPA & EA firms | High-volume tax practices & enterprises |
| **Included Capacity** | Bundled sample cases (`CASE-SAMPLE-2025`) | **10 production cases** per term | **50 production cases** per term | **250+ production cases** (customizable) |
| **Supported Ingestion** | Preloaded sample 1099-DA & ledger | Supported 1099-DA & tax ledger CSVs | Supported 1099-DA & tax ledger CSVs | Supported 1099-DA & tax ledger CSVs |
| **Receipt Export** | Signed sample receipts | Ed25519 signed outcome receipts | Ed25519 signed outcome receipts | Ed25519 signed outcome receipts |
| **Firm Identity** | Not applicable | Standard local preparer info | Firm & preparer identity on receipts | Multi-office / firm profile metadata |
| **Durability & Recovery**| SQLite WAL mode | SQLite WAL + recovery | SQLite WAL + recovery | SQLite WAL + recovery |
| **Support Channel** | Public documentation & FAQ | Email support (`support@vaultbasis.com`)| Priority email support | Dedicated support & IT deployment pack |
| **CTA on Website** | `Start Evaluation` | `Request Solo License` | `Request Practice License` | `Contact Enterprise` |

---

## 3. Case Capacity & Counting Semantics

### 3.1 What Counts as a Production Case?
- A case consumes **one licensed capacity slot** when a user creates a non-sample case (`case_kind = PRODUCTION`).
- Ingesting multiple source documents into that case, re-running reconciliation with identical or updated files, inspecting differences, and exporting outcome receipts do **NOT** consume additional capacity slots.

### 3.2 What is Excluded from Case Capacity?
- **Bundled Evaluation Cases:** Pre-loaded samples (e.g. `CASE-SAMPLE-2025`) are authenticated via cryptographic definition digests (`KNOWN_AUTHENTIC_SAMPLE_DIGESTS`) and are **completely unmetered**.
- **Independent Verification:** Running `apps/verifier/` on exported receipt bundles does **not** interact with the local license store or consume capacity.
- **Diagnostic Bundles:** Exporting sanitized `diagnostic.zip` for customer support is unmetered.

### 3.3 Deletion, Archival & Anti-Laundering Rule
- **Deleting or archiving a production case does NOT restore or refund consumed capacity.**
- *Rationale:* If deleting a case refunded capacity, a user could process a client's tax year, export the signed outcome receipt, delete the case, and process another client using the same single slot ("capacity laundering"). Once allocated, a capacity slot remains consumed for that license term.

---

## 4. License Lifecycle, Term Expiration & Renewal

### 4.1 License Validity Period
- Each commercial license token contains explicit ISO-8601 timestamps:
  - `not_before`: Timestamp before which the license is not yet valid.
  - `expires_at`: Timestamp when the active term ends (typically 365 days).
  - `grace_until`: Grace period timestamp (typically 30 days past `expires_at`) allowing continued reconciliation with a prominent renewal reminder.

### 4.2 Expiration State Matrix

| Operation | Active License (`ACTIVE`) | Grace Period (`GRACE`) | Expired License (`EXPIRED`) |
|---|---|---|---|
| **Open & View Existing Cases** | **YES** | **YES** | **YES** |
| **Inspect Historical Discrepancies** | **YES** | **YES** | **YES** |
| **Export Signed Evidence Bundles** | **YES** | **YES** | **YES** |
| **Offline Independent Verification** | **YES** | **YES** | **YES** |
| **Generate Sanitized Diagnostics** | **YES** | **YES** | **YES** |
| **Re-reconcile Existing Case** | **YES** | **YES** | **NO** (`LICENSE_EXPIRED`) |
| **Create New Production Case** | **YES** (if under capacity) | **YES** (with notice) | **NO** (`LICENSE_EXPIRED`) |

### 4.3 Renewal Semantics
- When a practitioner installs a renewed license token for a new term, the new token establishes the **permitted capacity for the new term**.
- Historical cases created under the previous term remain in the local database and **do NOT consume capacity from the new term's quota**.

---

## 5. Single Installation & Single Seat Boundary (MMP-1.5)

- In MMP-1.5, a license token is bound to a single local installation instance (`installation_id`).
- Multi-seat synchronized floating licenses and cross-machine RBAC are deferred to future major releases.
- Practices requiring multiple preparer laptops acquire individual installation licenses or an Enterprise bundle containing multiple standalone installation tokens.
