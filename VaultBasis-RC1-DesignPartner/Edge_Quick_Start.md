# VaultBasis Edge Quick Start (Design Partner Preview)

Welcome to the VaultBasis RC1 Design-Partner Preview.

## Installation
1. Ensure you are on a Mac (macOS 14+).
2. Ensure you have Python 3.13 installed.
3. Open your Terminal.
4. Navigate to this directory: `cd /path/to/VaultBasis-RC1-DesignPartner`
5. Run the launch script: `bash scripts/launch.sh`

## Running a Case
1. Once launched, open your browser to `http://127.0.0.1:8000`.
2. Upload the `broker_1099da_sample.csv` and `tax_ledger_sample.csv` provided during the session.
3. Review the reconciliation findings.
4. Click **Generate Outcome Receipt**.

## Verification
You can independently verify the receipt at `https://vaultbasis.vercel.app/verifier.html` using the `.receipt.json` file.
