# VaultBasis Edge Threat Model & Security Architecture
**Document ID:** VB-SEC-THREAT-001  
**Classification:** NORMATIVE  
**Authority:** Security Lead  
**Status:** ACTIVE  
**Applies To:** VaultBasis Edge v1.5.0  
**Last Reviewed:** 2026-10-08  

---

## 1. System Boundary & Trust Assumptions

```
┌───────────────────────────────────────────────────────────────────────────┐
│ Host Operating System (Windows 10/11 x64 / macOS Sonoma/Sequoia arm64)    │
│                                                                           │
│   ┌──────────────────────────┐             ┌──────────────────────────┐   │
│   │ Local Web Browser        │             │ VaultBasis Edge Backend  │   │
│   │ (Chromium / Safari /     │ HTTP/REST   │ (127.0.0.1:<port>)       │   │
│   │  Firefox / Edge)         ├────────────►│ Sockets strictly loopback│   │
│   │ Origin: loopback         │ Loopback    │ Zero external interface  │   │
│   └──────────────────────────┘             └────────────┬─────────────┘   │
│                                                         │                 │
│                                                         ▼                 │
│                                            ┌──────────────────────────┐   │
│                                            │ Local Encrypted Storage  │   │
│                                            │ SQLite (WAL mode, FULL)  │   │
│                                            │ Ed25519 Installation Key │   │
│                                            └──────────────────────────┘   │
│                                                                           │
│   [AIR-GAP BOUNDARY] Zero External Network Egress During Reconciliation   │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Threat Analysis & Defensive Controls

### 2.1 DNS Rebinding & External Host Header Attacks
* **Threat:** Malicious external website causes the victim's browser to resolve an external domain to `127.0.0.1`, sending requests to the local VaultBasis backend with a hostile `Host` header.
* **Control:** `security_and_host_validation_middleware` strictly validates the incoming `Host` header against `ALLOWED_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1", "[::1]", "testserver", "local"}`. Any request with an unlisted Host header is rejected immediately with `400 Bad Request`.

### 2.2 Cross-Origin Mutation & Malicious Downloaded HTML
* **Threat:** An attacker crafts a hostile local HTML file (`file://` or sandboxed iframe producing `Origin: null`) that attempts CSRF mutations against `POST /api/cases` or `POST /api/system/quit`.
* **Control:** All state-mutating HTTP methods (`POST`, `PUT`, `DELETE`, `PATCH`) enforce strict origin checks. Requests with `Origin: null` or untrusted cross-origins are rejected with `403 Forbidden` unless authorized via an instance-bound session capability token passed in `X-VaultBasis-Capability`.

### 2.3 Transient Capability Secret Containment
* **Threat:** Capability tokens leaked into logs, browser history, URLs, or exported receipts could allow attackers to forge authorized mutations.
* **Control:** `LOCAL_SESSION_CAPABILITY` is generated as an unguessable 128-bit random token in memory upon launch. It is never included in URL query parameters, serialized into SQLite, embedded in receipt exports, or exposed in diagnostic archives.

### 2.4 Directory Traversal & ZIP Slip
* **Threat:** Malicious uploaded ZIP archives or CSV file paths contain `../` directory traversal sequences aiming to overwrite sensitive host system files.
* **Control:** Strict path sanitization cleanses all upload paths and archive members, ensuring extractions are strictly confined within temporary workspace directories.

### 2.5 Data Loss on Crash & Power Outage
* **Threat:** Operating system crash or sudden termination during a large reconciliation leaves SQLite database corrupted.
* **Control:** SQLite engine enforces `PRAGMA journal_mode = WAL;` and `PRAGMA synchronous = FULL;` ensuring ACID durability and atomic transactions.

---

## 3. Residual Risk & Mitigation

| Residual Risk | Severity | Mitigation & Policy |
|---|---|---|
| Root/Admin Compromise of Host OS | HIGH | If the operating system itself is fully compromised, local memory and disk can be inspected. Mitigated by operating within isolated, secured endpoint workstations. |
| Physical Machine Theft | MEDIUM | Mitigated by recommending full-disk encryption (BitLocker / FileVault) for CPA workstations. |
