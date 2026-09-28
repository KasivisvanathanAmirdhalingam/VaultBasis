# VaultBasis Edge Quick Start Guide

## What VaultBasis Does
VaultBasis is an independent assurance tool that runs entirely inside your local network. It takes two sets of tax records—such as a broker's Form 1099-DA and a taxpayer's Koinly Capital Gains Report—and deterministically compares them. 

VaultBasis identifies agreements, mathematical differences, and unresolved facts. It produces a signed **Outcome Receipt** that proves exactly what the software concluded, preserving the provenance of both data sources.

## What VaultBasis Does NOT Do
VaultBasis is **not** a tax calculator. It does not determine taxpayer eligibility, provide tax advice, guarantee IRS audit protection, or calculate missing cost basis. It simply identifies discrepancies between two independent reports so you can reconcile them.

## 1. Installation
1. Extract the downloaded `VaultBasis_Edge.zip` to your machine.
2. Ensure you have Docker or Python 3.13 installed (depending on distribution).
3. Run `launch.sh` (Mac/Linux) or `launch.bat` (Windows) to start the local Edge server.
4. VaultBasis will start locally on `http://localhost:8000`.

*Note: VaultBasis is designed to run entirely offline to protect client privacy. No transaction data leaves your machine.*

## 2. Creating a Case
1. Open your browser and navigate to `http://localhost:8000`.
2. Click **New Case**.
3. Enter a local case identifier (e.g., `SMITH-2025-RECONCILIATION`) and the applicable tax year.

## 3. Importing Information
VaultBasis requires exactly two independent sources to perform a reconciliation.
1. Click **Import Broker Data** and upload the supported CSV (e.g., Coinbase Form 1099-DA export).
2. Click **Import Ledger Data** and upload the supported tax-ledger output (e.g., Koinly Capital Gains CSV).

## 4. Reviewing Findings
Once both sources are imported, click **Reconcile**.
VaultBasis will display a dashboard of results:
* **MATCHED**: The broker and the ledger agree.
* **BASIS_DIFFERENCE**: The cost basis reported by the ledger differs from the broker's 1099-DA.
* **PROCEEDS_DIFFERENCE**: The sales proceeds do not match.
* **UNRESOLVED_DATA**: Essential data (such as acquisition date) is missing or cannot be compared.

## 5. Generating and Locating the Receipt
1. Click **Generate Receipt**.
2. A ZIP evidence bundle will be downloaded to your local `Downloads` folder.
3. This ZIP contains the `receipt-v0.1.json`, your original CSV inputs, and the `independent_verifier.html` tool.
4. You may attach this ZIP bundle to your internal workpapers.

## Support & Privacy
* **Privacy Boundary**: VaultBasis has zero outbound telemetry for transaction data. Your case files never leave the Edge installation folder.
* **Common Errors**: If VaultBasis returns `UNSUPPORTED_SCHEMA`, ensure you are uploading the exact CSV format supported by the current preview (do not manually modify columns in Excel before uploading).
* **Contact**: For Design-Partner preview support, contact your VaultBasis engineering liaison.
