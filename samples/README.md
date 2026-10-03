# VaultBasis Edge — Test Data Samples for Reconciliation Engine

This directory contains three standard, practitioner-ready test sample pairs (`Source A` Form 1099-DA Broker Report and `Source B` Koinly Capital Gains Report) designed to test and validate all reconciliation variants, formulas, and outcome states in VaultBasis Edge.

---

## 📂 Sample Directory Overview

```
samples/
├── 01_clean_conformance_sample/
│   ├── Source_A_1099DA_Broker_Report.csv
│   └── Source_B_Koinly_Tax_Ledger.csv
├── 02_practitioner_variances_sample/
│   ├── Source_A_1099DA_Broker_Report.csv
│   └── Source_B_Koinly_Tax_Ledger.csv
├── 03_edge_cases_and_unresolved_sample/
│   ├── Source_A_1099DA_Broker_Report.csv
│   └── Source_B_Koinly_Tax_Ledger.csv
└── README.md
```

---

## 🧪 Sample 1: Clean Conformance (100% Green Match)
**Folder**: `samples/01_clean_conformance_sample/`  
**Expected Outcome State**: `MATCHED`  
**Expected Assurance Level**: `L2_EVIDENCE_RECONCILED`  
**Material Differences**: `0`  
**Unresolved Items**: `0`

### Test Rows:
| Row | Asset | Qty | Proceeds | Cost Basis | Date Sold | Date Acquired | Box 2 | Expected Match |
|---|---|---|---|---|---|---|---|---|
| 1 | BTC | 0.50000000 | $45,000.00 | $30,000.00 | 2025-04-15 | 2024-03-10 | YES | ✅ Exact Match |
| 2 | ETH | 4.25000000 | $12,750.00 | $8,500.00 | 2025-07-22 | 2024-09-05 | YES | ✅ Exact Match |
| 3 | SOL | 50.00000000 | $7,500.00 | $4,000.00 | 2025-10-18 | 2025-01-12 | YES | ✅ Exact Match |
| 4 | BTC | 0.12500000 | $11,250.00 | $7,500.00 | 2025-11-30 | 2024-11-15 | YES | ✅ Exact Match |

---

## 🔍 Sample 2: Practitioner Variances (Full Formula & Variant Coverage)
**Folder**: `samples/02_practitioner_variances_sample/`  
**Purpose**: Covers all primary variance formulas and difference states encountered during practitioner reconciliation.

### Test Rows & Expected Variance Behavior:
| Asset | Source A (1099-DA) | Source B (Koinly) | Difference State | Formula / Practitioner Root Cause |
|---|---|---|---|---|
| **BTC** | $22,500 proceeds / $15,000 basis (2025-03-10) | $22,500 proceeds / $15,000 basis (2025-03-10) | `MATCHED` | **Exact match control**: Verifies that matching rows alongside variances remain properly paired. |
| **ETH** | $10,000.00 proceeds | $9,975.00 proceeds | `PROCEEDS_DIFFERENCE` | **Gross vs Net Exchange Fees**: Broker reports gross proceeds ($10,000.00), tax software deducted $25 exchange trading fee. Variance = $25.00. |
| **SOL** | $3,200.00 basis | $4,100.00 basis | `BASIS_DIFFERENCE` | **FIFO vs HIFO / Spec ID**: Broker 1099-DA defaulted to FIFO basis, whereas tax ledger applied universal Spec ID/HIFO basis. Variance = $900.00. |
| **ADA** | Box 2 = `NO`, Basis = *(empty)* | $1,800.00 basis | `REPORTING_SCOPE_DIFFERENCE` | **IRS 2025 Non-Covered Scope**: Broker 1099-DA legally omits basis for pre-2025 acquired assets (Box 2 = NO), while tax ledger tracked $1,800 basis. |
| **DOT** | Acq Date = `2025-01-05` | Acq Date = `2023-11-20` | `ACQUISITION_DATE_DIFFERENCE` | **Transfer-in vs Acquisition**: Broker records on-chain deposit date, whereas tax ledger records original purchase date. |
| **AVAX** | $5,250 proceeds / 150 AVAX (2025-11-18) | *(Not in Koinly)* | `MISSING_FROM_LEDGER` | **Omitted Tax Ledger Import**: Trade executed on broker exchange was missing from Koinly tax ledger sync. |
| **LINK** | *(Not on 1099-DA)* | $4,200 proceeds / 300 LINK (2025-12-02) | `MISSING_FROM_1099DA` | **DEX / Non-Broker Trade**: Uniswap transaction present in client tax ledger but not subject to Broker 1099-DA reporting. |

---

## ⚠️ Sample 3: Edge Cases, High Precision & Unresolved Items
**Folder**: `samples/03_edge_cases_and_unresolved_sample/`  
**Purpose**: Tests high-precision crypto arithmetic, sub-cent rounding tolerance, and deterministic unresolved state detections.

### Test Rows & Expected Behavior:
| Asset | Condition | Source A (1099-DA) | Source B (Koinly) | Expected Behavior |
|---|---|---|---|---|
| **BTC** | 8-decimal micro-lot & sub-cent rounding | `0.00345678` BTC, $328.39 proceeds | `0.00345678` BTC, $328.39 proceeds | ✅ **MATCHED** (Sub-cent decimal arithmetic matches within $0.01 tolerance). |
| **ETH** | Missing acquisition date | Acq Date = *(empty)*, Box 2 = `YES` | Acq Date = `2024-05-01` | ⚠️ **UNRESOLVED_DATA** (`ACQUISITION_DATE_UNAVAILABLE`) |
| **SOL** | Missing cost basis on covered disposition | Basis = *(empty)*, Box 2 = `YES` | Basis = `$2,500.00` | ⚠️ **UNRESOLVED_DATA** (`BASIS_UNAVAILABLE` on covered lot) |
| **USDC** | ISO UTC with Z vs naive datetime | `2025-11-10T14:30:00Z` | `2025-11-10 14:30:00` | ⚠️ **UNRESOLVED_DATA** (`TIMEZONE_CONTEXT_MISSING`) |
| **DOGE** | Empty quantity field | Quantity = *(empty)* | Quantity = `10000.00000000` | ⚠️ **UNRESOLVED_DATA** (`QUANTITY_UNAVAILABLE`) |

---

## 🚀 How to Test in VaultBasis Edge

1. Launch VaultBasis Edge or open the local workspace at `http://127.0.0.1:8000`.
2. Click **New Reconciliation Case**.
3. Select **Source A · Broker Evidence (Form 1099-DA)** and upload `Source_A_1099DA_Broker_Report.csv` from any sample folder.
4. Select **Source B · Tax-Ledger Evidence (Koinly)** and upload `Source_B_Koinly_Tax_Ledger.csv` from the same sample folder.
5. Click **Reconcile Evidence** to inspect the deterministic outcome state, difference tables, and shallow provenance records.
