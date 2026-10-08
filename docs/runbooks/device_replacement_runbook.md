# VaultBasis Edge — Device Replacement & License Migration Runbook
**Document ID:** VB-RUNBOOK-DEV-001  
**Target Product:** VaultBasis Edge v1.5.0 (MMP-1.5)  
**Classification:** Standard Operating Procedure (Support & Operations)  
**Policy:** VaultBasis uses zero-cloud offline cryptographic entitlements. Device replacement is handled via cryptographic reissuance, not cloud DRM.

---

## 1. Scope & Trigger Conditions

This runbook applies when an existing licensed customer:
1. Experiences hardware failure, loss, or theft of their primary workstation.
2. Migrates to a new PC or Mac workstation.
3. Performs a clean OS reinstall resulting in a new installation keypair.

---

## 2. Architecture & Invariants

- **Zero Cloud DRM:** VaultBasis Edge does not require an active internet connection to validate or migrate licenses.
- **Local Keypair Isolation:** Every fresh installation generates an isolated local Ed25519 installation keypair in `keys/`.
- **Cryptographic Lineage:** Commercial license tokens are signed by the offline VaultBasis Commercial Authority and bound to the firm's license lineage.
- **Data Portability:** Historical cases and signed receipts are stored in the local SQLite database (`vaultbasis.db`), which can be restored from offline backup.

---

## 3. Step-by-Step Replacement Workflow

```
Customer Contact (Reports New Machine)
       ↓
Verify Order & License Lineage (Order ID / Firm Legal Name)
       ↓
Customer Installs Fresh VaultBasis Edge on New Machine
       ↓
Customer Copies New Installation Key ID from Edge UI
       ↓
Operator Generates Replacement Token with Offline Signer
       ↓
Customer Installs New Token → Fully Licensed
       ↓
(Optional) Customer Restores Historical Database / Cases
```

### Step 1: Identity & Order Verification
1. Support agent receives request from authenticated customer email on file.
2. Verify original purchase:
   - **Order Reference:** (e.g., `ORD-2026-XXXXX` or Paddle transaction ID)
   - **Firm / Entity Name:** Matches commercial billing records.
   - **Seat Quota:** Verify plan tier (Practitioner 1 seat, Firm 5 seats, Enterprise Custom).

### Step 2: Obtain New Installation Key ID
1. Customer downloads and installs official VaultBasis installer on the replacement machine.
2. In VaultBasis Edge, customer navigates to:
   - **Help → Installation Details** OR clicks **+ New Case → Commercial License**
3. Customer copies the **Installation Key ID** (64-character hex string).

### Step 3: Authorize Replacement in Commercial Registry
1. Operator records the replacement event in the internal commercial ledger:
   ```json
   {
     "order_id": "ORD-2026-0042",
     "action": "DEVICE_REPLACEMENT",
     "previous_installation_id": "a1b2c3d4...",
     "new_installation_id": "e5f6g7h8...",
     "replacement_reason": "Hardware upgrade to M4 Mac",
     "authorized_by": "Ops-Lead",
     "authorized_at": "2026-10-08T11:00:00Z"
   }
   ```
2. The old installation ID is recorded as `REPLACED_HISTORICAL`.

### Step 4: Issue Replacement License Token
1. Using the air-gapped Offline Commercial Token Generator, produce a new signed license token:
   ```bash
   python3 scripts/generate_license.py \
       --order-id "ORD-2026-0042" \
       --tier "PRACTITIONER" \
       --customer-name "Acme CPA Partners" \
       --installation-id "e5f6g7h8..." \
       --revision 2 \
       --out "Acme_CPA_VaultBasis_License_Rev2.txt"
   ```
2. Send the signed license file/token to the customer.

### Step 5: Customer Activates Replacement Machine
1. In VaultBasis Edge on the new machine:
   - Open **+ New Case** or **License Settings**
   - Click **Install License**
   - Paste or upload the new signed license token
2. Status updates immediately to `LICENSED (Practitioner / Firm / Enterprise)`.

---

## 4. Historical Case & Receipt Recovery

If the customer has access to backups from the old machine:
1. **Windows:** Copy `vaultbasis.db` and `keys/` from `%LOCALAPPDATA%\VaultBasis\` to the new machine's `%LOCALAPPDATA%\VaultBasis\`.
2. **macOS:** Copy `vaultbasis.db` and `keys/` from `~/Library/Application Support/VaultBasis/` to the new machine.
3. If only exported evidence packages (`.zip`) or receipts (`.json`) were backed up, they can be imported or independently validated anytime using the built-in Offline Verifier.

---

## 5. Security & Anti-Abuse Rules

- **No Mass Issuance:** Maximum of 2 device replacement authorizations per seat per calendar year without supervisory approval.
- **Immutable Log:** Every issued token is hash-chained and permanently recorded in the offline issuance ledger.
- **Key Separation:** Commercial issuing keys are stored in an offline, air-gapped HSM/vault and are never present on the customer machine or in Git.
