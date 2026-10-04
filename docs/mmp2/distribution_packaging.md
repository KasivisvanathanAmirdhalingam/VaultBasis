# MMP-2 Distribution & Packaging Strategy

> **Specification Ref:** `MMP2-DIST-001`, `MMP2-DIST-002`, `MMP2-DIST-003`, `MMP2-DIST-004`  
> **Core Concept:** Container-Compatible Architecture Without Docker-Dependent User Experience

---

## 1. The Packaging Problem: Why Docker Cannot Be Mandatory

While Docker simplifies multi-service deployment for engineers, forcing CPAs and accounting firms to install Docker Desktop, manage WSL2/virtualization, and configure container ports is a severe product adoption barrier.

VaultBasis resolves this by separating **packaging architecture** from **user installation UX**.

---

## 2. Dual-Track Distribution Model

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                   TRACK 1: NATIVE DESKTOP INSTALLER (DEFAULT UX)                 │
│                                                                                  │
│ • Windows (.exe / MSI) & macOS (.dmg / .app) single-click installers             │
│ • VaultBasis Desktop Launcher bundles and manages the sidecar automatically      │
│ • Zero container commands or virtualization setup required                       │
│ • Models downloaded / cached via built-in practitioner settings UI               │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                   TRACK 2: OCI / DOCKER IMAGES (ENTERPRISE IT OPTION)            │
│                                                                                  │
│ • Pre-built OCI container images (e.g., ghcr.io/vaultbasis/edge:2.0)             │
│ • Ready for Docker Compose, Kubernetes, or Podman deployments                    │
│ • Target audience: Firm IT departments running centralized local on-prem servers│
│ • Purely optional; never required for standalone practitioner use                │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Native Sidecar Process Lifecycle

In the native desktop packaging:
1. When VaultBasis launches, it spawns `vaultbasis-edge` (Core API).
2. If the practitioner enables Intelligence in Settings, the launcher spawns `vaultbasis-intelligence` (Sidecar).
3. Process health is monitored via heartbeat pings on `127.0.0.1:8100/health`.
4. Graceful shutdown terminates both processes cleanly on application exit.
