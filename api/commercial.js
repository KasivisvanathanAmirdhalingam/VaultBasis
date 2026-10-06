'use strict';

/**
 * VaultBasis — Commercial Bounded Services Handler (MMP15-INFRA-VCL-001)
 *
 * Consolidates commercial endpoints (checkout, checkout-session, enterprise-inquiry)
 * into a single bounded Serverless Function to stay strictly within Vercel platform limits.
 *
 * Security Invariants:
 * - ZERO Ed25519 commercial private keys accessible in this runtime.
 * - ZERO customer tax or reconciliation data processed or stored.
 * - Air-gapped license provisioning decoupled via ORDER_ELIGIBLE_FOR_PROVISIONING state.
 * - Client-side requests cannot assert payment completion.
 */

const crypto = require('crypto');
const { put } = require('@vercel/blob');
const { createOrder, getOrder, transitionOrderPaymentState, PAYMENT_STATES, getPlanConfig } = require('./_lib/billing-store');
const { createPaddleTransaction } = require('./_lib/paddle-client');

const _memoryInquiries = new Map();

function _hasBlobStorage() {
  return Boolean(process.env.BLOB_READ_WRITE_TOKEN);
}

function renderCheckoutHtml(order, planConfig) {
  const isPaidOrEligible =
    order.paymentState === PAYMENT_STATES.PAYMENT_CONFIRMED ||
    order.paymentState === PAYMENT_STATES.ORDER_ELIGIBLE_FOR_PROVISIONING;
  const priceDisplay = `$${(order.priceAmountCents / 100).toLocaleString('en-US', { minimumFractionDigits: 0 })}`;

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VaultBasis Secure Checkout — ${planConfig.displayName}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800&family=JetBrains+Mono:wght@400;500;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0f172a;
      --surface: #1e293b;
      --surface-elevated: #334155;
      --border: #334155;
      --border-accent: #475569;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --accent: #0284c7;
      --success: #10b981;
      --radius: 12px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2rem 1rem;
    }
    .checkout-container {
      width: 100%;
      max-width: 640px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 2.5rem;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.35);
    }
    .brand-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 2rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--border);
    }
    .brand-title {
      font-family: 'Outfit', sans-serif;
      font-size: 1.4rem;
      font-weight: 800;
      color: #fff;
    }
    .badge-secure {
      margin-left: auto;
      background: rgba(16, 185, 129, 0.15);
      color: var(--success);
      border: 1px solid rgba(16, 185, 129, 0.3);
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 0.76rem;
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
    }
    .order-card {
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.5rem;
      margin-bottom: 1.75rem;
    }
    .order-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.85rem;
      font-size: 0.92rem;
    }
    .order-row:last-child {
      margin-bottom: 0;
      padding-top: 0.85rem;
      border-top: 1px dashed var(--border);
    }
    .order-label { color: var(--text-muted); }
    .order-value { font-weight: 600; color: var(--text); }
    .order-price { font-family: 'Outfit', sans-serif; font-size: 1.5rem; font-weight: 800; color: #38bdf8; }
    
    .terms-box {
      background: rgba(51, 65, 85, 0.3);
      border-radius: 6px;
      padding: 1rem;
      font-size: 0.82rem;
      color: var(--text-muted);
      line-height: 1.5;
      margin-bottom: 1.75rem;
    }
    .btn-submit {
      width: 100%;
      background: var(--primary);
      color: #fff;
      border: none;
      border-radius: 8px;
      padding: 14px;
      font-size: 1.05rem;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      transition: background 0.2s;
      text-decoration: none;
    }
    .btn-submit:hover { background: var(--primary-hover); }
    .btn-secondary {
      display: inline-flex;
      background: transparent;
      color: var(--text-muted);
      border: 1px solid var(--border);
      padding: 10px 18px;
      border-radius: 8px;
      font-size: 0.88rem;
      text-decoration: none;
      margin-top: 1rem;
      transition: all 0.2s;
    }
    .btn-secondary:hover { color: #fff; border-color: var(--border-accent); }
    
    .success-panel {
      background: rgba(16, 185, 129, 0.1);
      border: 1px solid rgba(16, 185, 129, 0.3);
      border-radius: 8px;
      padding: 1.5rem;
      text-align: center;
      margin-bottom: 1.5rem;
    }
    .info-box {
      background: rgba(15, 23, 42, 0.7);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 1.25rem;
      margin: 1.25rem 0;
      text-align: left;
    }
    .step-item {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      margin-bottom: 0.75rem;
      font-size: 0.88rem;
      color: #cbd5e1;
    }
    .step-item:last-child { margin-bottom: 0; }
    .step-num {
      background: var(--primary);
      color: #fff;
      font-weight: 700;
      font-size: 0.75rem;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
  </style>
  <script src="https://cdn.paddle.com/paddle/v2/paddle.js"></script>
  <script>
    window.VAULTBASIS_PADDLE_CONFIG = {
      environment: "${process.env.PADDLE_ENVIRONMENT || 'sandbox'}",
      clientToken: "${process.env.PADDLE_CLIENT_TOKEN || ''}"
    };
  </script>
</head>
<body>
  <main class="checkout-container">
    <div class="brand-header">
      <svg width="32" height="32" viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="38" height="38" rx="9" fill="url(#vb-checkout-grad)"/>
        <defs>
          <linearGradient id="vb-checkout-grad" x1="0" y1="0" x2="38" y2="38" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="#2563eb"/>
            <stop offset="100%" stop-color="#0284c7"/>
          </linearGradient>
        </defs>
        <path d="M10 10 L19 26" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
        <path d="M28 10 L19 26" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
        <line x1="19" y1="26" x2="19" y2="30" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
      </svg>
      <div class="brand-title">VaultBasis Commercial Checkout</div>
      <div id="badge-secure-status" class="badge-secure" style="background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3);">⏳ CHECKOUT INITIALIZING…</div>
    </div>

    ${isPaidOrEligible ? `
      <div class="success-panel">
        <h3 style="color:#10b981; font-size:1.3rem; margin-bottom:0.5rem; font-weight:800;">✓ Payment Confirmed</h3>
        <p style="color:#cbd5e1; font-size:0.92rem; line-height:1.5;">
          Order <strong>${order.orderId}</strong> for <strong>${planConfig.displayName}</strong> is confirmed and eligible for provisioning.
        </p>
      </div>

      <div class="info-box">
        <h4 style="font-size:0.95rem; margin-bottom:0.75rem; color:#fff;">License Delivery &amp; Installation Steps</h4>
        <div class="step-item">
          <span class="step-num">1</span>
          <span>Your signed <code>VaultBasis_License_${order.orderId}.license</code> package is being generated by our isolated signing authority.</span>
        </div>
        <div class="step-item">
          <span class="step-num">2</span>
          <span>Delivery email with your license file and download access link is dispatched to <strong>${order.customerEmail}</strong>.</span>
        </div>
        <div class="step-item">
          <span class="step-num">3</span>
          <span>In <strong>VaultBasis Edge</strong>, navigate to <strong>Settings &rarr; License</strong> and import your <code>.license</code> file to activate your ${order.caseCapacity} client cases.</span>
        </div>
      </div>

      <div style="display:flex; gap:12px; flex-wrap:wrap; justify-content:center;">
        <a href="/" class="btn-secondary">&larr; Return to VaultBasis Home</a>
        <a href="/trust-assurance" class="btn-secondary">Review Security &amp; Trust &rarr;</a>
      </div>
    ` : `
      <div id="checkout-error-banner" style="display:none; background:rgba(239,68,68,0.15); border:1px solid rgba(239,68,68,0.4); border-radius:8px; padding:1rem; margin-bottom:1.25rem;">
        <p id="checkout-error-msg" style="color:#fca5a5; font-size:0.9rem; font-weight:600; margin:0 0 4px 0;"></p>
        <p id="checkout-error-ref" style="color:#94a3b8; font-size:0.78rem; font-family:'JetBrains Mono',monospace; margin:0;"></p>
      </div>

      <div class="order-card">
        <div class="order-row">
          <span class="order-label">Selected Plan</span>
          <span class="order-value">${planConfig.displayName}</span>
        </div>
        <div class="order-row">
          <span class="order-label">Client Case Capacity</span>
          <span class="order-value">${order.caseCapacity} Cases / Annual Term</span>
        </div>
        <div class="order-row">
          <span class="order-label">Customer / Entity</span>
          <span class="order-value">${order.customerName || 'Practitioner'}</span>
        </div>
        <div class="order-row">
          <span class="order-label">Delivery Work Email</span>
          <span class="order-value">${order.customerEmail}</span>
        </div>
        <div class="order-row">
          <span class="order-label">Total Amount Due</span>
          <span class="order-price">${priceDisplay}</span>
        </div>
      </div>

      <div class="terms-box">
        <strong>Local Case Processing &amp; Data Protection:</strong> VaultBasis Edge processes all client reconciliation, tax-basis calculations, and Evidence Receipts locally on your computer. Client tax records and ledger data are not uploaded to VaultBasis cloud services for normal Edge case processing.
      </div>

      <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid var(--border-accent); border-radius: 8px; padding: 1.25rem; margin-bottom: 1.5rem; text-align: left;">
        <label style="display: flex; align-items: flex-start; gap: 12px; cursor: pointer; font-size: 0.88rem; line-height: 1.5; color: #cbd5e1;">
          <input type="checkbox" id="agreement-checkbox" name="agreement_accepted" value="true" style="margin-top: 3px; width: 18px; height: 18px; accent-color: var(--primary); cursor: pointer;">
          <span>
            <strong>I agree to the <a href="/terms-of-service" target="_blank" rel="noopener" style="color: #38bdf8; text-decoration: underline;">Software License Agreement</a> and <a href="/terms-of-service" target="_blank" rel="noopener" style="color: #38bdf8; text-decoration: underline;">Terms of Service</a>.</strong>
            <br>
            <span style="font-size: 0.82rem; color: #94a3b8; display: block; margin-top: 4px;">
              I acknowledge the <a href="/privacy-policy" target="_blank" rel="noopener" style="color: #94a3b8; text-decoration: underline;">Privacy Policy</a>, <a href="/trust-assurance" target="_blank" rel="noopener" style="color: #94a3b8; text-decoration: underline;">Security &amp; Trust Model</a>, and <a href="/docs/scope_and_limitations_v0.1" target="_blank" rel="noopener" style="color: #94a3b8; text-decoration: underline;">Scope &amp; Limitations</a> describing local Edge processing and practitioner responsibilities.
            </span>
          </span>
        </label>
      </div>

      <form id="checkout-handoff-form" method="POST" action="/api/checkout-session">
        <input type="hidden" name="order_id" value="${order.orderId}">
        <input type="hidden" name="session_id" value="${order.providerSessionId}">
        <button type="submit" id="btn-checkout-submit" class="btn-submit" disabled style="opacity: 0.5; cursor: not-allowed;">
          Continue to Secure Checkout — ${priceDisplay} &rarr;
        </button>
      </form>

      <div style="text-align:center; margin-top:1.25rem;">
        <a href="/" class="btn-secondary">&larr; Cancel &amp; Return to Home</a>
      </div>

      <script>
        (function() {
          const form = document.getElementById('checkout-handoff-form');
          const btn = document.getElementById('btn-checkout-submit');
          const chk = document.getElementById('agreement-checkbox');
          const errBanner = document.getElementById('checkout-error-banner');
          const errMsg = document.getElementById('checkout-error-msg');
          const errRef = document.getElementById('checkout-error-ref');

          let paddleInitialized = false;

          function initPaddleInstance(overrideToken, overrideEnv) {
            if (paddleInitialized) return true;
            if (!window.Paddle) return false;

            const cfg = window.VAULTBASIS_PADDLE_CONFIG || {};
            const env = overrideEnv || cfg.environment || 'sandbox';
            const token = overrideToken || cfg.clientToken || '';

            if (!token) {
              console.warn('[paddle-init] No client-side token provided; Paddle.Initialize postponed.');
              const secureBadge = document.getElementById('badge-secure-status');
              if (secureBadge && !paddleInitialized) {
                secureBadge.textContent = '📋 PURCHASING OPENS AT LAUNCH';
                secureBadge.style.background = 'rgba(59, 130, 246, 0.15)';
                secureBadge.style.color = '#60a5fa';
                secureBadge.style.border = '1px solid rgba(59, 130, 246, 0.3)';
              }
              return false;
            }


            try {
              if (env === 'sandbox' && typeof Paddle.Environment !== 'undefined') {
                Paddle.Environment.set('sandbox');
              }
              if (typeof Paddle.Initialize !== 'undefined') {
                Paddle.Initialize({ token: token });
                paddleInitialized = true;
                const secureBadge = document.getElementById('badge-secure-status');
                if (secureBadge) {
                  secureBadge.textContent = '🔒 SECURE CHECKOUT READY';
                  secureBadge.style.background = 'rgba(16, 185, 129, 0.15)';
                  secureBadge.style.color = '#34d399';
                  secureBadge.style.border = '1px solid rgba(16, 185, 129, 0.3)';
                }
                return true;
              }
            } catch (initErr) {
              console.warn('[paddle-init] Initialization error:', initErr);
            }
            return false;
          }

          // Initialize on page load if Paddle script is already ready
          if (window.Paddle) {
            initPaddleInstance();
          } else {
            window.addEventListener('load', function() {
              initPaddleInstance();
            });
          }

          if (chk && btn) {
            chk.addEventListener('change', function() {
              if (chk.checked) {
                btn.disabled = false;
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
              } else {
                btn.disabled = true;
                btn.style.opacity = '0.5';
                btn.style.cursor = 'not-allowed';
              }
            });
          }

          if (form && btn) {
            form.addEventListener('submit', async function(e) {
              e.preventDefault();
              if (chk && !chk.checked) {
                if (errBanner && errMsg && errRef) {
                  errMsg.textContent = 'Please agree to the Software License Agreement and acknowledge the local processing terms before proceeding.';
                  errRef.textContent = 'Requirement: Agreement Acceptance';
                  errBanner.style.display = 'block';
                }
                return;
              }

              btn.disabled = true;
              btn.style.opacity = '0.75';
              btn.style.cursor = 'wait';
              btn.textContent = 'Starting secure checkout…';
              if (errBanner) errBanner.style.display = 'none';

              try {
                const orderId = form.querySelector('input[name="order_id"]').value;
                const sessionId = form.querySelector('input[name="session_id"]').value;

                const res = await fetch('/api/checkout-session', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                  },
                  body: JSON.stringify({
                    order_id: orderId,
                    session_id: sessionId,
                    agreement_accepted: true
                  })
                });

                const data = await res.json();
                if (!res.ok || !data.ok) {
                  throw new Error(data.error || "We couldn't start secure checkout. No payment was taken. Please try again.");
                }

                // Ensure Paddle.Initialize is invoked with client token
                const isReady = initPaddleInstance(data.paddle_client_token, data.paddle_environment);

                // 1. Direct Paddle.js modal overlay (strictly requiring successful initialization)
                if (isReady && window.Paddle && data.provider_transaction_id) {
                  try {
                    Paddle.Checkout.open({
                      transactionId: data.provider_transaction_id,
                      settings: {
                        successUrl: window.location.href
                      }
                    });
                    btn.disabled = false;
                    btn.style.opacity = '1';
                    btn.style.cursor = 'pointer';
                    btn.innerHTML = 'Continue to Secure Checkout — ${priceDisplay} &rarr;';
                    return;
                  } catch (paddleErr) {
                    console.warn('[checkout-handoff] Paddle.Checkout.open failed, falling back to URL redirect:', paddleErr);
                  }
                }

                // 2. Direct URL redirect if Paddle returned an approved checkout.url
                if (data.checkout_url) {
                  window.location.href = data.checkout_url;
                  return;
                }

                // 3. Fallback message if client token unconfigured and no direct URL
                if (!isReady) {
                  throw new Error("Secure checkout is temporarily unavailable. Client token is being configured. No payment was taken.");
                }

                throw new Error("Checkout initialized. Please complete payment through the secure Paddle dialog.");
              } catch (err) {
                console.error('[checkout-handoff]', err);
                btn.disabled = false;
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
                btn.innerHTML = 'Continue to Secure Checkout — ${priceDisplay} &rarr;';

                if (errBanner && errMsg && errRef) {
                  errMsg.textContent = err.message || "We couldn't start secure checkout. No payment was taken. Please try again.";
                  errRef.textContent = 'Error reference: VB-PAY-' + Math.random().toString(36).substring(2, 9).toUpperCase();
                  errBanner.style.display = 'block';
                } else {
                  alert("We couldn't start secure checkout. No payment was taken. Please try again.");
                }
              }
            });
          }
        })();
      </script>
    `}
  </main>
</body>
</html>`;
}

// Sub-handler: Checkout Order Creation
async function handleCheckout(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { plan, name, email, firm } = req.body || {};

  if (!plan || !name || !email) {
    return res.status(400).json({ error: 'Plan, name, and email are required.' });
  }

  const planConfig = getPlanConfig(plan);
  if (!planConfig) {
    return res.status(400).json({ error: `Unrecognized plan: '${plan}'.` });
  }

  if (!planConfig.isSelfServe) {
    return res.status(400).json({
      error: `Plan '${planConfig.displayName}' requires assisted commercial inquiry. Please contact sales.`,
      redirectRoute: '/contact',
    });
  }

  try {
    const order = await createOrder({
      customerEmail: email,
      customerName: name,
      firmName: firm,
      planId: planConfig.planId,
    });

    const canonicalBase = process.env.PUBLIC_BASE_URL || 'http://localhost:3000';
    const checkoutUrl = `${canonicalBase}/api/checkout-session?order_id=${order.orderId}&session_id=${encodeURIComponent(order.providerSessionId)}`;

    return res.status(200).json({
      status: 'success',
      orderId: order.orderId,
      providerSessionId: order.providerSessionId,
      checkoutUrl,
      orderSummary: {
        plan: order.planId,
        displayName: planConfig.displayName,
        amountCents: order.priceAmountCents,
        currency: order.priceCurrency,
        caseCapacity: order.caseCapacity,
        termDays: planConfig.termDurationDays,
      },
    });
  } catch (error) {
    console.error('[commercial] Checkout initiation error:', error);
    return res.status(500).json({ error: 'Failed to initiate checkout session.' });
  }
}

// Sub-handler: Checkout Session Review & Payment Handoff
async function handleCheckoutSession(req, res) {
  const query = req.query || {};
  const body = req.body || {};
  const orderId = query.order_id || body.order_id;
  const sessionId = query.session_id || body.session_id;

  if (!orderId) {
    return res.status(400).send('Order identifier is required.');
  }

  const order = await getOrder(orderId, sessionId);
  if (!order) {
    return res.status(404).send(`Order '${orderId}' not found.`);
  }

  const planConfig = getPlanConfig(order.planId);
  if (!planConfig) {
    return res.status(400).send(`Unrecognized plan '${order.planId}'.`);
  }

  if (req.method === 'POST') {
    const isJsonRequest =
      req.headers['accept']?.includes('application/json') ||
      req.headers['content-type']?.includes('application/json');

    // Mandatory Agreement Gate validation
    const agreementAccepted = body.agreement_accepted === true || body.agreement_accepted === 'true' || query.agreement_accepted === 'true';
    if (!agreementAccepted) {
      const errMsg = 'You must agree to the Software License Agreement and acknowledge the local processing terms to continue.';
      if (isJsonRequest) {
        return res.status(400).json({ ok: false, error: errMsg });
      }
      return res.status(400).send(errMsg);
    }

    try {
      const agreementRecord = {
        acceptedAt: new Date().toISOString(),
        agreementVersion: 'MMP-1.5-2026.1',
        termsVersion: 'v1.0',
        privacyPolicyVersion: 'v1.0',
        securityTrustVersion: 'v1.0',
        scopeLimitationsVersion: 'v0.1',
        acceptanceMethod: 'CLICKWRAP',
      };

      // Idempotency: If order already has an active Paddle transaction in PAYMENT_PENDING, reuse it
      if (
        order.paymentState === PAYMENT_STATES.PAYMENT_PENDING &&
        order.providerTransactionId &&
        order.events?.length > 0
      ) {
        const lastHandoff = order.events.slice().reverse().find(e => e.state === PAYMENT_STATES.PAYMENT_PENDING);
        const paddleEnv = process.env.PADDLE_ENVIRONMENT || 'sandbox';
        const paddleClientToken = process.env.PADDLE_CLIENT_TOKEN || '';
        const existingCheckoutUrl = lastHandoff?.metadata?.checkoutUrl || null;

        if (isJsonRequest) {
          return res.status(200).json({
            ok: true,
            order_id: order.orderId,
            state: PAYMENT_STATES.PAYMENT_PENDING,
            checkout_url: existingCheckoutUrl,
            provider: 'PADDLE',
            provider_transaction_id: order.providerTransactionId,
            paddle_environment: paddleEnv,
            paddle_client_token: paddleClientToken,
            reused: true,
          });
        }
        if (existingCheckoutUrl) {
          return res.redirect(303, existingCheckoutUrl);
        }
      }

      const canonicalBase = process.env.PUBLIC_BASE_URL || 'http://localhost:3000';
      const returnUrl = `${canonicalBase}/api/checkout-session?order_id=${order.orderId}&session_id=${encodeURIComponent(order.providerSessionId)}`;

      const paddleResult = await createPaddleTransaction({
        order,
        planConfig,
        returnUrl,
        agreementRecord,
      });

      const providerTxnId = paddleResult.transactionId;
      const checkoutUrl = paddleResult.checkoutUrl || null;
      const paddleEnv = process.env.PADDLE_ENVIRONMENT || 'sandbox';
      const paddleClientToken = process.env.PADDLE_CLIENT_TOKEN || '';

      const updatedOrder = await transitionOrderPaymentState({
        orderId: order.orderId,
        newState: PAYMENT_STATES.PAYMENT_PENDING,
        reason: 'CHECKOUT_PADDLE_HANDOFF',
        providerTransactionId: providerTxnId,
        metadata: {
          handoffAt: new Date().toISOString(),
          paymentProvider: 'paddle',
          priceId: paddleResult.priceId,
          checkoutUrl,
          agreement: agreementRecord,
        },
      });

      if (isJsonRequest) {
        return res.status(200).json({
          ok: true,
          order_id: updatedOrder.orderId,
          state: PAYMENT_STATES.PAYMENT_PENDING,
          checkout_url: checkoutUrl,
          provider: 'PADDLE',
          provider_transaction_id: providerTxnId,
          paddle_environment: paddleEnv,
          paddle_client_token: paddleClientToken,
        });
      }

      if (checkoutUrl) {
        return res.redirect(303, checkoutUrl);
      }

      return res.redirect(303, `/api/checkout-session?order_id=${order.orderId}&session_id=${encodeURIComponent(order.providerSessionId)}`);
    } catch (err) {
      console.error('[commercial] Paddle transaction creation error:', err.message);
      const errRef = `VB-PAY-${Date.now().toString(36).toUpperCase()}`;
      if (isJsonRequest) {
        return res.status(500).json({
          ok: false,
          error: "We couldn't start secure checkout. No payment was taken. Please try again.",
          error_reference: errRef,
        });
      }
      return res.status(500).send(`Checkout processing failed (${errRef}). Please try again.`);
    }
  }

  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  return res.status(200).send(renderCheckoutHtml(order, planConfig));
}

// Sub-handler: Enterprise Inquiry
async function handleEnterpriseInquiry(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { name, email, firm, estimatedCases, notes } = req.body || {};

  if (!name || !email) {
    return res.status(400).json({ error: 'Name and work email are required.' });
  }

  const inquiryId = `INQ-${new Date().getUTCFullYear()}-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;
  const now = new Date().toISOString();

  const inquiryRecord = {
    inquiryId,
    customerName: name.trim(),
    customerEmail: email.trim().toLowerCase(),
    firmName: firm ? firm.trim() : null,
    estimatedCases: estimatedCases || '250+',
    notes: notes ? notes.trim() : null,
    status: 'RECEIVED',
    createdAt: now,
  };

  try {
    if (_hasBlobStorage()) {
      await put(`inquiries/${inquiryId}.json`, JSON.stringify(inquiryRecord), {
        access: 'private',
        contentType: 'application/json',
        addRandomSuffix: false,
        allowOverwrite: false,
      });
    } else {
      _memoryInquiries.set(inquiryId, inquiryRecord);
    }

    return res.status(200).json({
      status: 'success',
      inquiryId,
      message: 'Enterprise inquiry received. Our commercial team will provide an IT security pack and custom quote.',
    });
  } catch (error) {
    console.error('[commercial] Error recording inquiry:', error);
    return res.status(500).json({ error: 'Failed to record enterprise inquiry.' });
  }
}

// Central Dispatcher
module.exports = async (req, res) => {
  const query = req.query || {};
  const action = query.action;
  const url = req.url || '';

  if (action === 'checkout-session' || url.includes('/checkout-session')) {
    return handleCheckoutSession(req, res);
  }
  if (action === 'enterprise-inquiry' || url.includes('/enterprise-inquiry')) {
    return handleEnterpriseInquiry(req, res);
  }
  if (action === 'checkout' || url.includes('/checkout')) {
    return handleCheckout(req, res);
  }

  // Default fallback routing
  if (req.body && req.body.plan) {
    return handleCheckout(req, res);
  }
  if (query.order_id || (req.body && req.body.order_id)) {
    return handleCheckoutSession(req, res);
  }

  return res.status(400).json({ error: 'Unrecognized commercial operation.' });
};
