'use strict';

/**
 * VaultBasis — Commercial Checkout Session API (MMP15-PROD-BILL-001)
 *
 * Initiates a self-serve checkout session for Solo ($499/yr) or Practice ($1,499/yr).
 * Rejects Enterprise requests (which must route to managed inquiry).
 * Derives price and terms authoritatively from server-side PLAN_CATALOG.
 */

const { createOrder, getPlanConfig } = require('./billing-store');

module.exports = async (req, res) => {
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
    const providerSessionId = `sess_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

    const order = await createOrder({
      providerSessionId,
      customerEmail: email,
      customerName: name,
      firmName: firm,
      planId: planConfig.planId,
    });

    const canonicalBase = process.env.PUBLIC_BASE_URL || 'http://localhost:3000';
    // When live Stripe integration is active, this returns Stripe Checkout URL;
    // in UAT / development mode, it returns the verified test checkout endpoint.
    const checkoutUrl = process.env.STRIPE_SECRET_KEY
      ? `${canonicalBase}/api/stripe-redirect?session_id=${providerSessionId}`
      : `${canonicalBase}/api/checkout-session?order_id=${order.orderId}&session_id=${providerSessionId}`;

    return res.status(200).json({
      status: 'success',
      orderId: order.orderId,
      providerSessionId,
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
    console.error('[checkout-api] Checkout initiation error:', error);
    return res.status(500).json({ error: 'Failed to initiate checkout session.' });
  }
};
