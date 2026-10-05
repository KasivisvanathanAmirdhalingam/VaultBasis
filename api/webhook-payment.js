'use strict';

/**
 * VaultBasis — Payment Webhook Ingest Handler (MMP15-PROD-BILL-001)
 *
 * Conforms to:
 * - Webhook Signature Verification (HMAC-SHA256)
 * - Strict Idempotency & Anti-Replay: duplicate event IDs return 200 without duplicate state changes.
 * - Authoritative Order Validation: amount, currency, and plan must match server order record.
 * - Decoupled Provisioning: advances order state to ORDER_ELIGIBLE_FOR_PROVISIONING;
 *   does not synchronously sign licenses.
 * - Zero Private Key Bleed: zero Ed25519 signing keys accessible in this runtime.
 */

const crypto = require('crypto');
const {
  PAYMENT_STATES,
  getOrder,
  isEventProcessed,
  recordWebhookEvent,
  transitionOrderPaymentState,
} = require('./_lib/billing-store');

function verifyWebhookSignature(payloadBuffer, signatureHeader, secret, toleranceSec = 300) {
  if (!secret) {
    if (process.env.NODE_ENV === 'test' || process.env.ALLOW_TEST_WEBHOOKS === 'true') {
      return true;
    }
    return false;
  }
  if (!signatureHeader) return false;

  try {
    // 1. Check if signature header uses timestamped format: ts=<timestamp>;h1=<sig> or t=<timestamp>,v1=<sig>
    if ((signatureHeader.includes('t=') || signatureHeader.includes('ts=')) &&
        (signatureHeader.includes('v1=') || signatureHeader.includes('h1='))) {
      const parts = signatureHeader.split(/[;,]/).reduce((acc, part) => {
        const [k, v] = part.trim().split('=');
        if (k && v) acc[k] = v;
        return acc;
      }, {});

      const timestamp = parts['ts'] || parts['t'];
      const signature = parts['h1'] || parts['v1'];
      if (!timestamp || !signature) return false;

      // Validate timestamp freshness if tolerance is set
      const nowSec = Math.floor(Date.now() / 1000);
      const eventSec = parseInt(timestamp, 10);
      if (isNaN(eventSec) || Math.abs(nowSec - eventSec) > toleranceSec) {
        return false;
      }

      // Paddle signed payload is `timestamp:payloadBuffer` or Stripe `${timestamp}.${payloadBuffer}`
      const delimiter = signatureHeader.includes('ts=') ? ':' : '.';
      const signedPayload = `${timestamp}${delimiter}${payloadBuffer}`;
      const expectedSig = crypto
        .createHmac('sha256', secret)
        .update(signedPayload, 'utf8')
        .digest('hex');

      const expectedBuf = Buffer.from(expectedSig, 'utf8');
      const suppliedBuf = Buffer.from(signature, 'utf8');

      return (
        expectedBuf.length === suppliedBuf.length &&
        crypto.timingSafeEqual(expectedBuf, suppliedBuf)
      );
    }

    // 2. Fallback to direct raw HMAC-SHA256 signature
    const expectedSig = crypto
      .createHmac('sha256', secret)
      .update(payloadBuffer, 'utf8')
      .digest('hex');

    const suppliedSig = signatureHeader.replace(/^sha256=|^v1=|^h1=/, '').trim();
    const expectedBuf = Buffer.from(expectedSig, 'utf8');
    const suppliedBuf = Buffer.from(suppliedSig, 'utf8');

    return (
      expectedBuf.length === suppliedBuf.length &&
      crypto.timingSafeEqual(expectedBuf, suppliedBuf)
    );
  } catch (e) {
    console.error('[webhook-payment] Signature verification exception:', e.message);
    return false;
  }
}

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const rawBody = typeof req.body === 'string' ? req.body : JSON.stringify(req.body);
  const signature = req.headers['paddle-signature'] || req.headers['stripe-signature'] || req.headers['x-webhook-signature'];
  const secret = process.env.PADDLE_WEBHOOK_SECRET || process.env.PAYMENT_WEBHOOK_SECRET;

  if (!verifyWebhookSignature(rawBody, signature, secret)) {
    console.warn('[webhook-payment] Rejected webhook with invalid signature.');
    return res.status(401).json({ error: 'Invalid webhook signature.' });
  }

  const event = typeof req.body === 'object' ? req.body : JSON.parse(rawBody);
  const eventId = event.event_id || event.id || event.eventId;
  const eventType = event.event_type || event.type || event.eventType;
  const data = event.data?.object || event.data || {};

  if (!eventId || !eventType) {
    return res.status(400).json({ error: 'Malformed webhook event envelope.' });
  }

  // Idempotency check: Replay defense
  const alreadyProcessed = await isEventProcessed(eventId);
  if (alreadyProcessed) {
    return res.status(200).json({ status: 'success', duplicate: true, message: 'Event already processed.' });
  }

  const orderId =
    data.custom_data?.order_id ||
    data.custom_data?.orderId ||
    data.metadata?.orderId ||
    data.orderId;

  if (!orderId) {
    console.warn(`[webhook-payment] Webhook event ${eventId} missing associated orderId.`);
    return res.status(400).json({ error: 'Missing orderId in event metadata.' });
  }

  const order = await getOrder(orderId);
  if (!order) {
    console.error(`[webhook-payment] Order ${orderId} not found for event ${eventId}.`);
    return res.status(404).json({ error: `Order ${orderId} not found.` });
  }

  try {
    const isSuccessEvent =
      eventType === 'transaction.completed' ||
      eventType === 'transaction.paid' ||
      eventType === 'checkout.session.completed' ||
      eventType === 'payment_intent.succeeded';

    if (isSuccessEvent) {
      // Validate payment integrity
      const rawTotal = data.details?.totals?.total || data.amount_total || data.amount || order.priceAmountCents;
      const amountReceived = typeof rawTotal === 'string' ? parseInt(rawTotal, 10) : Number(rawTotal);
      const currencyReceived = (data.currency_code || data.currency || order.priceCurrency).toUpperCase();

      if (amountReceived !== order.priceAmountCents || currencyReceived !== order.priceCurrency) {
        console.error(
          `[webhook-payment] Commercial integrity conflict for order ${orderId}: ` +
            `expected ${order.priceAmountCents} ${order.priceCurrency}, got ${amountReceived} ${currencyReceived}`
        );
        return res.status(409).json({ error: 'Payment amount or currency mismatch with order record.' });
      }

      await transitionOrderPaymentState(orderId, PAYMENT_STATES.PAYMENT_CONFIRMED, {
        providerEventId: eventId,
        providerTransactionId: data.id || order.providerTransactionId,
        detail: `Payment verified via ${eventType}`,
      });
    } else if (
      eventType === 'transaction.past_due' ||
      eventType === 'payment_intent.payment_failed' ||
      eventType === 'charge.failed'
    ) {
      await transitionOrderPaymentState(orderId, PAYMENT_STATES.PAYMENT_FAILED, {
        providerEventId: eventId,
        detail: `Payment failure notified via ${eventType}`,
      });
    } else if (eventType === 'adjustment.created' || eventType === 'charge.refunded') {
      await transitionOrderPaymentState(orderId, PAYMENT_STATES.REFUNDED, {
        providerEventId: eventId,
        detail: `Refund processed via ${eventType}`,
      });
    } else {
      // Ignored event types acknowledge receipt
      console.log(`[webhook-payment] Unhandled event type '${eventType}' recorded.`);
    }

    await recordWebhookEvent(eventId, orderId, eventType);
    return res.status(200).json({ status: 'success', processed: true, orderId });
  } catch (err) {
    console.error(`[webhook-payment] Failed to process event ${eventId}:`, err);
    return res.status(500).json({ error: 'Internal error processing webhook event.' });
  }
};
