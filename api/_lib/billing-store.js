'use strict';

/**
 * VaultBasis — Commercial Billing & Order Store (MMP15-PROD-BILL-001)
 *
 * Provides authoritative server-side plan catalogs, order state management,
 * and webhook idempotency tracking with dual-layer persistence (Blob storage
 * + HMAC-signed session resilience across cold-starts).
 *
 * Namespace: orders/ and webhook-events/
 *
 * Security & Integrity Invariants:
 * - Authoritative Server-Side Pricing: prices & capacities are derived strictly from PLAN_CATALOG.
 * - State Machine Discipline: Only verified payment webhooks transition to ORDER_ELIGIBLE_FOR_PROVISIONING.
 * - Zero Signing Key Bleed: This module stores commercial orders only; zero Ed25519 signing keys.
 * - Zero Client Evidence: Orders contain customer commercial identity only, never client ledger data.
 */

const crypto = require('crypto');
const { put, get } = require('@vercel/blob');

const BILLING_SCHEMA_VERSION = '1.0';
const SESSION_SECRET = process.env.SESSION_SECRET || 'vb_order_session_secret_granite_v1';

const PLAN_CATALOG = Object.freeze({
  SOLO: Object.freeze({
    planId: 'SOLO',
    displayName: 'Solo Practitioner',
    priceAmountCents: 49900,
    currency: 'USD',
    caseCapacity: 10,
    termDurationDays: 365,
    isSelfServe: true,
  }),
  PRACTICE: Object.freeze({
    planId: 'PRACTICE',
    displayName: 'Practice License',
    priceAmountCents: 149900,
    currency: 'USD',
    caseCapacity: 50,
    termDurationDays: 365,
    isSelfServe: true,
  }),
  ENTERPRISE: Object.freeze({
    planId: 'ENTERPRISE',
    displayName: 'Enterprise',
    isSelfServe: false,
  }),
});

const PAYMENT_STATES = Object.freeze({
  CHECKOUT_CREATED: 'CHECKOUT_CREATED',
  PAYMENT_PENDING: 'PAYMENT_PENDING',
  PAYMENT_CONFIRMED: 'PAYMENT_CONFIRMED',
  ORDER_ELIGIBLE_FOR_PROVISIONING: 'ORDER_ELIGIBLE_FOR_PROVISIONING',
  PAYMENT_FAILED: 'PAYMENT_FAILED',
  CHECKOUT_EXPIRED: 'CHECKOUT_EXPIRED',
  CANCELLED: 'CANCELLED',
  REFUNDED: 'REFUNDED',
  CHARGEBACK: 'CHARGEBACK',
});

const PROVISIONING_STATES = Object.freeze({
  NOT_ELIGIBLE: 'NOT_ELIGIBLE',
  ELIGIBLE: 'ELIGIBLE',
  IN_PROGRESS: 'IN_PROGRESS',
  PROVISIONED: 'PROVISIONED',
  FAILED: 'FAILED',
  CANCELLED: 'CANCELLED',
});

// In-memory fallback for local testing & preview environments
const _memoryOrders = new Map();
const _memoryEvents = new Map();

function _hasBlobStorage() {
  return Boolean(process.env.BLOB_READ_WRITE_TOKEN);
}

function generateOrderId() {
  const year = new Date().getUTCFullYear();
  const hex = crypto.randomBytes(4).toString('hex').toUpperCase();
  return `ORD-${year}-${hex}`;
}

function getPlanConfig(planId) {
  if (!planId || typeof planId !== 'string') return null;
  const upper = planId.trim().toUpperCase();
  return PLAN_CATALOG[upper] || null;
}

/**
 * Generates an HMAC-signed self-contained session token for cross-lambda resilience.
 */
function createSignedSessionToken(payload) {
  const dataStr = Buffer.from(JSON.stringify(payload), 'utf8').toString('base64url');
  const signature = crypto.createHmac('sha256', SESSION_SECRET).update(dataStr).digest('base64url');
  return `sess_${dataStr}_${signature}`;
}

/**
 * Validates and unpacks an HMAC-signed session token.
 */
function unpackSignedSessionToken(sessionId) {
  if (!sessionId || typeof sessionId !== 'string' || !sessionId.startsWith('sess_')) {
    return null;
  }
  const parts = sessionId.slice(5).split('_');
  if (parts.length !== 2) return null;

  const [dataStr, signature] = parts;
  const expectedSig = crypto.createHmac('sha256', SESSION_SECRET).update(dataStr).digest('base64url');

  if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expectedSig))) {
    return null;
  }

  try {
    const raw = Buffer.from(dataStr, 'base64url').toString('utf8');
    return JSON.parse(raw);
  } catch (_e) {
    return null;
  }
}

/**
 * Creates and records a new commercial order.
 */
async function createOrder({
  orderId = generateOrderId(),
  customerEmail,
  customerName,
  firmName = null,
  planId,
}) {
  const planConfig = getPlanConfig(planId);
  if (!planConfig) {
    throw new Error(`Invalid plan identifier: '${planId}'`);
  }
  if (!planConfig.isSelfServe) {
    throw new Error(`Plan '${planId}' requires assisted sales/invoice inquiry, not self-serve checkout.`);
  }
  if (!customerEmail || !customerName) {
    throw new Error('customerEmail and customerName are required to create an order.');
  }

  const now = new Date();
  const termStart = now.toISOString();
  const termEnd = new Date(now.getTime() + planConfig.termDurationDays * 24 * 60 * 60 * 1000).toISOString();

  // Create HMAC-signed session token containing immutable order parameters
  const providerSessionId = createSignedSessionToken({
    orderId,
    planId: planConfig.planId,
    customerEmail: customerEmail.trim().toLowerCase(),
    customerName: customerName.trim(),
    firmName: firmName ? firmName.trim() : null,
    priceAmountCents: planConfig.priceAmountCents,
    caseCapacity: planConfig.caseCapacity,
    createdAt: termStart,
  });

  const orderRecord = {
    schemaVersion: BILLING_SCHEMA_VERSION,
    orderId,
    providerSessionId,
    customerEmail: customerEmail.trim().toLowerCase(),
    customerName: customerName.trim(),
    firmName: firmName ? firmName.trim() : null,
    planId: planConfig.planId,
    priceAmountCents: planConfig.priceAmountCents,
    priceCurrency: planConfig.currency,
    caseCapacity: planConfig.caseCapacity,
    termStart,
    termEnd,
    paymentState: PAYMENT_STATES.CHECKOUT_CREATED,
    provisioningState: PROVISIONING_STATES.NOT_ELIGIBLE,
    createdAt: termStart,
    confirmedAt: null,
    events: [
      {
        state: PAYMENT_STATES.CHECKOUT_CREATED,
        timestamp: termStart,
        detail: 'Checkout session created',
      },
    ],
  };

  _memoryOrders.set(orderId, orderRecord);

  if (_hasBlobStorage()) {
    try {
      await put(`orders/${orderId}.json`, JSON.stringify(orderRecord), {
        access: 'private',
        contentType: 'application/json',
        addRandomSuffix: false,
        allowOverwrite: true,
      });
    } catch (err) {
      console.warn('[billing-store] Blob write warning:', err.message);
    }
  }

  return orderRecord;
}

/**
 * Retrieves an order by its orderId, with fallback to verified signed session token.
 */
async function getOrder(orderId, sessionId = null) {
  if (!orderId) return null;

  // 1. Check in-memory store
  if (_memoryOrders.has(orderId)) {
    return _memoryOrders.get(orderId);
  }

  // 2. Check Blob storage if configured
  if (_hasBlobStorage()) {
    try {
      const result = await get(`orders/${orderId}.json`, { access: 'private' });
      if (result) {
        const chunks = [];
        const reader = result.stream.getReader();
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          chunks.push(value);
        }
        const record = JSON.parse(Buffer.concat(chunks.map(c => Buffer.from(c))).toString('utf8'));
        _memoryOrders.set(orderId, record);
        return record;
      }
    } catch (e) {
      if (e && e.name !== 'BlobNotFoundError') {
        console.warn(`[billing-store] Blob read warning for ${orderId}:`, e.message);
      }
    }
  }

  // 3. Fallback to HMAC-signed session verification for stateless cold-start resilience
  if (sessionId) {
    const payload = unpackSignedSessionToken(sessionId);
    if (payload && payload.orderId === orderId) {
      const planConfig = getPlanConfig(payload.planId);
      if (planConfig) {
        const reconstructed = {
          schemaVersion: BILLING_SCHEMA_VERSION,
          orderId: payload.orderId,
          providerSessionId: sessionId,
          customerEmail: payload.customerEmail,
          customerName: payload.customerName,
          firmName: payload.firmName || null,
          planId: planConfig.planId,
          priceAmountCents: planConfig.priceAmountCents,
          priceCurrency: planConfig.currency,
          caseCapacity: planConfig.caseCapacity,
          termStart: payload.createdAt,
          termEnd: new Date(new Date(payload.createdAt).getTime() + planConfig.termDurationDays * 24 * 60 * 60 * 1000).toISOString(),
          paymentState: PAYMENT_STATES.CHECKOUT_CREATED,
          provisioningState: PROVISIONING_STATES.NOT_ELIGIBLE,
          createdAt: payload.createdAt,
          confirmedAt: null,
          events: [
            {
              state: PAYMENT_STATES.CHECKOUT_CREATED,
              timestamp: payload.createdAt,
              detail: 'Checkout session restored from signed session token',
            },
          ],
        };
        _memoryOrders.set(orderId, reconstructed);
        return reconstructed;
      }
    }
  }

  return null;
}

/**
 * Checks if a webhook event has already been processed (Idempotency).
 */
async function isEventProcessed(providerEventId) {
  if (!providerEventId) return false;
  if (!_hasBlobStorage()) {
    return _memoryEvents.has(providerEventId);
  }
  try {
    const result = await get(`webhook-events/${providerEventId}.json`, { access: 'private' });
    return Boolean(result);
  } catch (_e) {
    return false;
  }
}

/**
 * Records a processed webhook event.
 */
async function recordWebhookEvent(providerEventId, orderId, eventType) {
  const eventRecord = {
    providerEventId,
    orderId,
    eventType,
    processedAt: new Date().toISOString(),
  };

  _memoryEvents.set(providerEventId, eventRecord);

  if (_hasBlobStorage()) {
    try {
      await put(`webhook-events/${providerEventId}.json`, JSON.stringify(eventRecord), {
        access: 'private',
        contentType: 'application/json',
        addRandomSuffix: false,
        allowOverwrite: false,
      });
    } catch (err) {
      console.warn('[billing-store] Webhook event store warning:', err.message);
    }
  }
}

/**
 * Advances an order's payment state.
 * Supports both object signature and positional (orderId, targetState, opts) signature.
 */
async function transitionOrderPaymentState(arg1, arg2, arg3) {
  let orderId, targetState, detail, providerEventId, providerTransactionId, metadata;

  if (typeof arg1 === 'object' && arg1 !== null) {
    orderId = arg1.orderId;
    targetState = arg1.newState || arg1.targetState;
    detail = arg1.reason || arg1.detail;
    providerTransactionId = arg1.providerTransactionId || null;
    providerEventId = arg1.providerEventId || null;
    metadata = arg1.metadata || {};
  } else {
    orderId = arg1;
    targetState = arg2;
    const opts = arg3 || {};
    detail = opts.detail || opts.reason;
    providerEventId = opts.providerEventId || null;
    providerTransactionId = opts.providerTransactionId || null;
    metadata = opts.metadata || {};
  }

  const order = await getOrder(orderId);
  if (!order) {
    throw new Error(`Cannot transition state: Order '${orderId}' does not exist.`);
  }

  const currentState = order.paymentState;
  const now = new Date().toISOString();
  order.updatedAt = now;

  if (targetState === PAYMENT_STATES.PAYMENT_CONFIRMED || targetState === PAYMENT_STATES.ORDER_ELIGIBLE_FOR_PROVISIONING) {
    if (currentState !== PAYMENT_STATES.CHECKOUT_CREATED && currentState !== PAYMENT_STATES.PAYMENT_PENDING) {
      throw new Error(`Illegal state transition to PAYMENT_CONFIRMED from ${currentState}`);
    }
    order.paymentState = PAYMENT_STATES.ORDER_ELIGIBLE_FOR_PROVISIONING;
    order.provisioningState = PROVISIONING_STATES.ELIGIBLE;
    order.confirmedAt = now;
    if (providerTransactionId) {
      order.providerTransactionId = providerTransactionId;
    }
  } else if (targetState === PAYMENT_STATES.PAYMENT_FAILED) {
    order.paymentState = PAYMENT_STATES.PAYMENT_FAILED;
    order.provisioningState = PROVISIONING_STATES.NOT_ELIGIBLE;
  } else if (targetState === PAYMENT_STATES.REFUNDED) {
    order.paymentState = PAYMENT_STATES.REFUNDED;
    if (order.provisioningState !== PROVISIONING_STATES.PROVISIONED) {
      order.provisioningState = PROVISIONING_STATES.CANCELLED;
    }
  } else if (targetState === PAYMENT_STATES.CANCELLED) {
    order.paymentState = PAYMENT_STATES.CANCELLED;
    order.provisioningState = PROVISIONING_STATES.NOT_ELIGIBLE;
  } else {
    order.paymentState = targetState;
  }

  order.events.push({
    state: order.paymentState,
    timestamp: now,
    providerEventId,
    detail: detail || `Transitioned from ${currentState} to ${order.paymentState}`,
    metadata,
  });

  _memoryOrders.set(orderId, order);

  if (_hasBlobStorage()) {
    try {
      await put(`orders/${orderId}.json`, JSON.stringify(order), {
        access: 'private',
        contentType: 'application/json',
        addRandomSuffix: false,
        allowOverwrite: true,
      });
    } catch (err) {
      console.warn('[billing-store] Blob order update warning:', err.message);
    }
  }

  return order;
}

module.exports = {
  PLAN_CATALOG,
  PAYMENT_STATES,
  PROVISIONING_STATES,
  getPlanConfig,
  createOrder,
  getOrder,
  isEventProcessed,
  recordWebhookEvent,
  transitionOrderPaymentState,
};
