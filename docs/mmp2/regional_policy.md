# MMP-2 Regional & Organizational Policy Engine

> **Specification Ref:** `MMP2-POL-004`, `MMP2-POL-005`  
> **Core Concept:** Policy-Driven Compliance Rather Than Hard-Coded Geography

---

## 1. Compliance Architecture Overview

Professional CPA firms operate under strict jurisdictional regulations, federal contracts, and internal IT risk policies. For example, certain US accounting firms prohibit software utilizing models with specific corporate origins, or require strict EU GDPR localization.

VaultBasis implements a **Policy-Driven Engine** rather than hard-coding country assumptions.

---

## 2. Standard Policy Profiles

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ POLICY: US_FIRM_RESTRICTED (Default for US Accounting Practices)            │
│ • DENY: Models requiring external cloud endpoints                          │
│ • DENY: Models with restricted provenance / telemetric telemetry            │
│ • ALLOW: Local-only open-weight models (Apache-2.0 / MIT approved)          │
│ • REQUIRE: Strict zero-network egress validation                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ POLICY: EU_LOCAL_AI (GDPR / AI Act Compliance)                              │
│ • REQUIRE: Complete on-device execution (no cross-border data transfer)     │
│ • REQUIRE: Full practitioner auditability of context profiles               │
│ • REQUIRE: Local-only storage of vector embeddings and session caches       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ POLICY: ENTERPRISE_FED_AUDIT (Government / Bank Contract Compliance)        │
│ • REQUIRE: FIPS-compliant local cryptography for file stores                │
│ • REQUIRE: Zero AI automated changes to workpapers                          │
│ • REQUIRE: Cryptographic hash verification of all model binaries at startup │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ POLICY: AI_DISABLED (Strict Air-Gap Deterministic Only)                     │
│ • ACTION: Intelligence sidecar is completely unmounted                      │
│ • STATUS: 100% deterministic reconciliation active                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Evaluation Pipeline

Before any agent or model is executed:
1. The active `firm_identity` and `ContextProfile` are inspected.
2. The model's `ModelDescriptor` is cross-referenced against the active `PolicyProfile`.
3. If any policy violation occurs, the execution is blocked with machine-readable error code `POLICY_VIOLATION_BLOCKED` and logged in `commercial_audit_log`.
