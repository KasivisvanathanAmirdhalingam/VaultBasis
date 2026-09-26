# ADR-005: Koinly Capital Gains CSV as Sole Named Tax Adapter for Preview

* **Status**: ACCEPTED / FROZEN  
* **Date**: 2026-09-23  
* **Deciders**: VaultBasis Architecture Group  
* **PRD Reference**: §0.2 (Binding Changes), §6.4(A) (Tax-System Export Decision)  

---

## Context and Problem Statement

To prove independent outcome verification between a broker's Form 1099-DA and tax software calculations, VaultBasis must ingest the tax software's gain/loss report. Attempting to build and maintain adapters for all cryptocurrency tax tools (CoinTracker, TaxBit, TokenTax, CryptoTaxCalculator, ZenLedger, Koinly) during MMP-1 would dilute focus and delay delivery.

## Decision Drivers

* Need a concrete, widely documented, itemized capital gains export format that includes asset, acquisition date, sale date, costs, proceeds, and gain/loss.
* Must avoid ambiguous multi-adapter maintenance during the preview.
* Design partners who use alternative systems need a bounded, documented fallback format.

## Decision Outcome

1. **Sole Named Tax Adapter**:
   - **Koinly Capital Gains Report CSV** is selected as the sole named tax-software adapter for MMP-1 preview.
   - Koinly's Capital Gains Report provides explicit itemized columns (`Date`, `Asset`, `Amount`, `Cost basis`, `Proceeds`, `Gain / loss`, `Date acquired`).
   - The parser enforces strict schema validation and fails closed on drifted headers.
2. **Documented Fallback Adapter**:
   - For design partners unable to supply Koinly CSVs, VaultBasis provides a frozen fallback format: **`VaultBasis Reconciliation CSV v0.1`** with canonical header: `date,asset,quantity,proceeds,cost_basis,date_acquired,source_ref`.
   - This fallback is a controlled test contract, not a promise of universal ingestion.

### Positive Consequences
* Narrow, well-defined integration scope for MMP-1.
* Clear testing boundaries with reproducible golden fixtures.

### Negative Consequences
* Users of other tax platforms (e.g. CoinTracker) must export to the generic VaultBasis CSV fallback during preview.
