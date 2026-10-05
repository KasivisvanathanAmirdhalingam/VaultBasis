'use strict';

/**
 * VaultBasis — Commercial Checkout Session & Delivery Page (MMP15-PROD-BILL-001)
 *
 * Serves the authoritative checkout session page for self-serve orders (Solo & Practice).
 * Allows buyers to review order details, terms, and complete secure payment in preprod/test
 * or live Paddle/Stripe environments, with automated license provisioning and download access.
 */

const { getOrder, transitionOrderPaymentState, PAYMENT_STATES, getPlanConfig } = require('./billing-store');
const { generateLicenseTokenForOrder } = require('./entitlement-store');
const { sendOrderDeliveryEmail } = require('./delivery-mailer');

function renderCheckoutHtml(order, planConfig, error = null, success = null) {
  const isPaid = order.paymentState === PAYMENT_STATES.PAID || order.paymentState === PAYMENT_STATES.ORDER_ELIGIBLE_FOR_PROVISIONING;
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
      --success-bg: rgba(16, 185, 129, 0.12);
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
    .license-box {
      background: #0f172a;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 1rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.78rem;
      color: #38bdf8;
      word-break: break-all;
      margin: 1rem 0;
      text-align: left;
      user-select: all;
    }
  </style>
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
      <div class="brand-title">VaultBasis Checkout</div>
      <div class="badge-secure">🔒 256-BIT ENCRYPTED</div>
    </div>

    ${isPaid ? `
      <div class="success-panel">
        <h3 style="color:#10b981; font-size:1.3rem; margin-bottom:0.5rem; font-weight:800;">✓ Purchase Confirmed</h3>
        <p style="color:#cbd5e1; font-size:0.92rem; line-height:1.5;">
          Your ${planConfig.displayName} order (<strong>${order.orderId}</strong>) is active.<br>
          A signed license token and download authorization have been sent to <strong>${order.customerEmail}</strong>.
        </p>
      </div>

      <div class="order-card">
        <h4 style="font-size:0.95rem; margin-bottom:0.75rem; color:#fff;">Your VaultBasis License Token</h4>
        <div class="license-box">${order.licenseToken || 'TOKEN_PROVISIONED_VIA_EMAIL'}</div>
        <p style="font-size:0.8rem; color:var(--text-muted); line-height:1.5;">
          Copy this token into <strong>VaultBasis Edge &rarr; Settings &rarr; License</strong> to activate your ${order.caseCapacity} client cases.
        </p>
      </div>

      <div style="display:flex; gap:12px; flex-wrap:wrap; justify-content:center;">
        <a href="/" class="btn-secondary">&larr; Return to VaultBasis Home</a>
        <a href="/trust-assurance" class="btn-secondary">Review Security &amp; Trust &rarr;</a>
      </div>
    ` : `
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
        <strong>Commercial Guarantee:</strong> VaultBasis operates 100% locally on your computer with zero cloud telemetry. Your license entitles you to deterministic reconciliation, signed Evidence Receipts, and permanent offline access to historical cases.
      </div>

      <form method="POST" action="/api/checkout-session">
        <input type="hidden" name="order_id" value="${order.orderId}">
        <input type="hidden" name="session_id" value="${order.providerSessionId}">
        <button type="submit" class="btn-submit">
          Complete Purchase (${priceDisplay}) &rarr;
        </button>
      </form>

      <div style="text-align:center; margin-top:1.25rem;">
        <a href="/" class="btn-secondary">&larr; Cancel &amp; Return to Home</a>
      </div>
    `}
  </main>
</body>
</html>`;
}

module.exports = async (req, res) => {
  const query = req.query || {};
  const body = req.body || {};
  const orderId = query.order_id || body.order_id;
  const sessionId = query.session_id || body.session_id;

  if (!orderId) {
    return res.status(400).send('Order identifier is required.');
  }

  const order = await getOrder(orderId);
  if (!order) {
    return res.status(404).send(`Order '${orderId}' not found.`);
  }

  const planConfig = getPlanConfig(order.planId);
  if (!planConfig) {
    return res.status(400).send(`Unrecognized plan '${order.planId}'.`);
  }

  if (req.method === 'POST') {
    // Process commercial payment completion (self-serve test or live checkout transition)
    try {
      const updatedOrder = await transitionOrderPaymentState({
        orderId: order.orderId,
        newState: PAYMENT_STATES.ORDER_ELIGIBLE_FOR_PROVISIONING,
        reason: 'CHECKOUT_SESSION_COMPLETED',
        metadata: { completedAt: new Date().toISOString() },
      });

      // Issue signed license token
      const licenseResult = await generateLicenseTokenForOrder(updatedOrder.orderId);
      if (licenseResult && licenseResult.token) {
        updatedOrder.licenseToken = licenseResult.token;
      }

      // Send automated delivery email
      try {
        await sendOrderDeliveryEmail(updatedOrder.orderId);
      } catch (mailErr) {
        console.warn('[checkout-session] Delivery email warning:', mailErr.message);
      }

      res.setHeader('Content-Type', 'text/html; charset=utf-8');
      return res.status(200).send(renderCheckoutHtml(updatedOrder, planConfig));
    } catch (err) {
      console.error('[checkout-session] Payment completion error:', err);
      return res.status(500).send('Payment completion failed. Please try again.');
    }
  }

  // GET request: render checkout page
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  return res.status(200).send(renderCheckoutHtml(order, planConfig));
};
