# ADR-001: Evidence Contract v0.1 as First Normative Engineering Artifact

* **Status**: ACCEPTED / FROZEN  
* **Date**: 2026-09-23  
* **Deciders**: VaultBasis Architecture Group  
* **PRD Reference**: §0.2 (Binding Changes), §6.5 (Evidence Contract Dependency Order), §13.2 (Normative Artifact)  

---

## Context and Problem Statement

In distributed financial reconciliation, systems frequently design internal data models and application logic first, retrofitting output receipts or evidence exports as an afterthought. This invariably leads to schema drift, unversioned receipt structures, verifier breakage, and tight coupling between internal database representations and external verifiable proofs.

VaultBasis is positioned as an **independent outcome verification edge**. Downstream CPAs, taxpayers, enterprise clients, and independent machines must be able to verify VaultBasis Outcome Receipts without relying on internal VaultBasis database state or proprietary software.

## Decision Drivers

* Receipts must be portable, stable, and independently verifiable offline.
* The verifier and receipt signer must depend on a frozen normative contract, rather than defining it retroactively.
* Multiple engineering workstreams must be able to work concurrently without schema conflicts.

## Considered Options

1. **Build application and engine first, export receipt at the end** (Standard MVP approach).
2. **Freeze Evidence Contract v0.1 first as a normative schema**, then build verifier, signer, canonical models, and engine conforming strictly to the frozen contract.

## Decision Outcome

Chosen option: **Option 2 (Evidence Contract v0.1 First)**.

Per PRD §6.5, the implementation order is frozen and non-negotiable:
1. `Evidence Contract v0.1` (`schemas/receipt/receipt-v0.1.json`, `canonicalization-v0.1.md`, `signing-v0.1.md`, `verification-v0.1.md`)
2. `Independent Verifier`
3. `Receipt Signer`
4. `Canonical Case Model`
5. `Reconciliation Engine`
6. `Edge API`
7. `Three-Screen UI`

### Positive Consequences
* The receipt schema is immutable and version-pinned (`v0.1`).
* Independent verifiers can be written in any programming language against the frozen schema and canonicalization specification.
* Zero risk of application logic silently altering evidence properties or receipt semantics.

### Negative Consequences
* Requires upfront discipline before writing application features; modifications to receipt properties require formal version increments (`v0.2`).
