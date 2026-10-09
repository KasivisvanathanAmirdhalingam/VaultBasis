# VaultBasis MMP-1.5 Commercial Consistency & Alignment Matrix (LEGAL-012)

**Document ID:** `MMP15-COMM-MATRIX-001` (Control Ref: `LEGAL-012` under `MMP15-LEGAL-RISK-QUAL-001`)  
**Status:** `PRE-LAUNCH IMPLEMENTATION PASS`  
**Purpose:** Verify alignment across all commercial touchpoints (Pricing page, Terms of Service, Paddle catalog, License Engine, Edge UI, and Support documentation).

---

## 1. Cross-Surface Consistency Matrix

| Commercial Dimension | Pricing Page (`/pricing`) | Terms of Service (`/terms`) | Paddle / Billing Store (`billing-store.js`) | Local License Engine (`license_engine.py`) | Edge Dashboard UI (`index.html`) | Support / FAQ (`contact.html`) | Alignment Finding |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **Evaluation Tier** | 3-Day Eval (Up to 3 Client Cases + Samples — $0) | Design-partner / Evaluation terms | Internal ID: `TRIAL` ($0) | Enforces 3-case cap on unactivated installs | Displays Evaluation badge & case counter | Free evaluation inquiry instructions | **ALIGNED** |
| **Practitioner Tier** | Practitioner ($499 / year — Up to 10 Client Cases) | Annual subscription term | Internal ID: `SOLO` ($499.00 USD, 10 cases, 365 days) | Enforces 10-case cap | Displays Practitioner badge | Pricing & entitlement inquiries | **ALIGNED** |
| **Firm Tier** | Firm ($1,499 / year — Up to 50 Client Cases) | Annual subscription term | Internal ID: `PRACTICE` ($1,499.00 USD, 50 cases, 365 days) | Enforces 50-case cap | Displays Firm badge | Multi-seat firm inquiry support | **ALIGNED** |
| **Enterprise Tier** | Enterprise (Custom Case Volume — Contact us) | Managed enterprise agreement | Internal ID: `ENTERPRISE` (Assisted inquiry, `isSelfServe: false`) | Custom capacity token | Routes to contact/inquiry flow | Managed support & deployment | **ALIGNED** |
| **Term Duration** | 1 Year (365 Days) | 1 Year annual term | `termDurationDays: 365` | Checks token expiration against current date | Displays license expiration date in Settings | Annual renewal FAQ | **ALIGNED** |
| **Grace Period** | No grace period | Immediate expiration on term end | Term ends strictly at $T + 365\text{d}$ | Rejects case creation after `term_end` date | Warns 30 days prior; blocks creation on expiry | Explains renewal steps | **ALIGNED** |
| **Post-Expiry Behavior** | Existing local cases preserved | Existing local data remains practitioner property | Zero remote case revocation | Existing cases viewable/exportable; new cases blocked | Read-only mode on expired cases; banner prompts renewal | Confirms zero data deletion on expiry | **ALIGNED** |
| **Upgrade Semantics** | Pro-rated mid-term upgrade | Immediate tier upgrade via billing | Upgrades issue new token with combined capacity | Replaces token immediately without restart | Updates tier badge and capacity counter | Upgrade inquiry support | **ALIGNED** |
| **Refund Policy** | 14-day evaluation / refund policy | Standard refund terms | Processed via Paddle Merchant of Record | License deactivation on refund; local data preserved | Prompts re-activation if token revoked | Refund request routing | **ALIGNED** |

---

## 2. Contradiction Analysis Findings

- **Contradictions Identified:** `0` material contradictions identified across pricing, terms, license engine, and dashboard representations.
- **Invariant Preserved:** `ORDER ≠ LICENSE ≠ DOWNLOAD TOKEN`. Commercial billing stores customer order identities; the local Edge license engine verifies cryptographic tokens; neither system touches taxpayer financial evidence.
