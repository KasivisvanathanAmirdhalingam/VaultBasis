# VaultBasis — Environment Architecture & Deployment Model (MMP-1.5)

## 1. Executive Summary & Zero-Cost Preprod Strategy

VaultBasis employs a strict three-tier environment separation. This allows continuous integration and end-to-end verification of commercial checkout, webhooks, and transactional delivery without exposing unreleased work to the public or incurring unnecessary SaaS subscription fees (e.g. €20/month password protection add-ons).

```
                      +---------------------------------------+
                      |             Git Repository            |
                      +---------------------------------------+
                                          |
             +----------------------------+----------------------------+
             |                                                         |
     [ feature/* ]                                             [ preprod ]
             |                                                         |
             v                                                         v
   Local Unit & Gate Suite                                Vercel Preview Deployment
   (100% Offline / Fast Tests)                            (Protected: Vercel Auth)
                                                                       |
                                                                       | Verified Release
                                                                       v
                                                               [ main Branch ]
                                                                       |
                                                                       v
                                                            Vercel Production Domain
                                                              (www.vaultbasis.com)
```

---

## 2. Environment Taxonomy

| Environment | Branch / Target | Access Control | Purpose | External Services / State |
|:---|:---|:---|:---|:---|
| **Local / CI** | Feature branches / PRs | Private workstation | Code execution, fast unit/integration suites, gate checks. | Local mock stores, zero egress, ephemeral SQLite. |
| **Preprod / Staging** | `preprod` branch | **Vercel Authentication** (Standard Protection — Free on Hobby) | End-to-end commercial validation, transactional mail tests, webhook simulations. | Stripe Test Mode, Ethereal/Sandbox SMTP, Staging Blob namespace. |
| **Production** | `main` branch (`www.vaultbasis.com`) | Publicly accessible | Qualified commercial release for practitioners and firms. | Live Stripe, Production SMTP, Production Release Manifest. |

> [!IMPORTANT]
> **Air-Gapped Private Key Boundary Invariant**:
> The Ed25519 Commercial License Signing Private Key **NEVER enters Vercel environment variables** in *any* environment (Local, Preprod, or Production). Commercial licenses are generated strictly during isolated offline ceremonies.

---

## 3. Zero-Cost Vercel Authentication Setup

To protect preview deployments without purchasing paid Password Protection add-ons:

1. In the Vercel Dashboard, navigate to:
   $$\text{Project} \longrightarrow \text{Settings} \longrightarrow \text{Deployment Protection}$$
2. Under **Vercel Authentication**, enable **Standard Protection**.
3. **Scope**:
   - `www.vaultbasis.com` (Production) $\longrightarrow$ **Public** (no login required).
   - `vaultbasis-git-preprod-*.vercel.app` (Preview) $\longrightarrow$ **Protected** (requires Vercel account sign-in).
4. **Verification**:
   - Open a private/incognito window to the preview URL: Vercel login is requested.
   - Open `www.vaultbasis.com`: Public marketing and trust portal loads immediately.

---

## 4. Environment Variable Scoping Matrix

| Variable | Local Dev / CI | Preprod (Preview Scope) | Production (Production Scope) |
|:---|:---|:---|:---|
| `PUBLIC_BASE_URL` | `http://localhost:3000` | `https://preprod.vaultbasis.com` (or preview URL) | `https://www.vaultbasis.com` |
| `BLOB_READ_WRITE_TOKEN` | *Unset (uses in-memory fallback)* | Vercel Blob Token (Staging store) | Vercel Blob Token (Production store) |
| `STRIPE_SECRET_KEY` | *Unset / mock* | `sk_test_...` (Stripe Test Mode) | `sk_live_...` (Live Stripe) |
| `STRIPE_WEBHOOK_SECRET` | `whsec_test_mock_123` | `whsec_test_...` (Stripe Test Webhook) | `whsec_live_...` (Live Stripe Webhook) |
| `SMTP_HOST` / `SMTP_USER` | *Unset (Ethereal test sink)* | Test SMTP Transport / Mailtrap | Production SMTP Provider (DKIM/SPF) |
| `COMMERCIAL_SIGNING_KEY` | **NEVER SET** | **NEVER SET** | **NEVER SET** |

---

## 5. Branching & Release Promotion Protocol

1. **Development & Bug Fixes**:
   - Work on `feature/*` or `fix/*` branches.
   - Validate locally: `./scripts/validate_before_commit.sh` (11/11 gates must PASS).
2. **Integration & Preprod Validation**:
   - Merge approved features into `preprod`:
     ```bash
     git checkout preprod
     git merge feature/my-feature
     git push origin preprod
     ```
   - Test full acquisition loop on the protected Vercel Preview URL.
3. **Formal Production Promotion**:
   - Only after all 18 canonical release gates are satisfied and UAT passes:
     ```bash
     git checkout main
     git merge preprod --ff-only
     git push origin main
     ```
