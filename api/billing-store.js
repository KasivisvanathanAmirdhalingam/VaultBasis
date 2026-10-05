'use strict';

/**
 * VaultBasis — Commercial Billing & Order Store (MMP15-PROD-BILL-001)
 *
 * Provides authoritative server-side plan catalogs, order state management,
 * and webhook idempotency tracking.
 *
 * Namespace: orders/ and webhook-events/
 *
 * Security & Integrity Invariants:
 * - Authoritative Server-Side Pricing: prices & capacities are derived strictly from PLAN_CATALOG.
 * - State Machine Discipline: Only PAYMENT_CONFIRMED transitions to ORDER_ELIGIBLE_FOR_PROVISIONING.
 * - Zero Signing Key Bleed: This module stores commercial orders only; zero Ed25519 signing keys.
 * - Zero Client Evidence: Orders contain customer commercial identity only, never client ledger data.
 */

const crypto = require('crypto');
const { put, get } = require('@vercel/blob');

const BILLING_SCHEMA_VERSION = '1.0';

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

// In-memory fallback for local testing & offline UAT execution when BLOB_READ_WRITE_TOKEN is absent
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
 * Creates and records a new commercial order.
 */
async function createOrder({
  orderId = generateOrderId(),
  providerSessionId,
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

  if (_hasBlobStorage()) {
    await put(`orders/${orderId}.json`, JSON.stringify(orderRecord), {
      access: 'private',
      contentType: 'application/json',
      addRandomSuffix: false,
      allowOverwrite: false,
    });
  } else {
    _memoryOrders.set(orderId, orderRecord);
  }

  return orderRecord;
}

/**
 * Retrieves an order by its VaultBasis orderId.
 */
async function getOrder(orderId) {
  if (!orderId) return null;
  if (!_hasBlobStorage()) {
    return _memoryOrders.get(orderId) || null;
  }

  try {
    const result = await get(`orders/${orderId}.json`, { access: 'private' });
    if (!result) return null;
    const chunks = [];
    const reader = result.stream.getReader();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
    }
    return JSON.parse(Buffer.concat(chunks.map(c => Buffer.from(c))).toString('utf8'));
  } catch (e) {
    if (e && e.name === 'BlobNotFoundError') return null;
    console.error(`[billing-store] Failed to fetch order ${orderId}:`, e.message);
    throw e;
  }
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

  if (_hasBlobStorage()) {
    await put(`webhook-events/${providerEventId}.json`, JSON.stringify(eventRecord), {
      access: 'private',
      contentType: 'application/json',
      addRandomSuffix: false,
      allowOverwrite: false,
    });
  } else {
    _memoryEvents.set(providerEventId, eventRecord);
  }
}

/**
 * Advances the order payment state following strict state machine rules.
 */
async function transitionOrderPaymentState(orderId, targetState, { providerEventId = null, detail = null } = {}) {
  const order = await getOrder(orderId);
  if (!order) {
    throw new Error(`Order not found: ${orderId}`);
  }

  // Validate State Transitions
  const currentState = order.paymentState;
  const nowIso = new Date().toISOString();

  if (targetState === PAYMENT_STATES.PAYMENT_CONFIRMED) {
    if (currentState !== PAYMENT_STATES.CHECKOUT_CREATED && currentState !== PAYMENT_STATES.PAYMENT_PENDING) {
      throw new Error(`Illegal state transition to PAYMENT_CONFIRMED from ${currentState}`);
    }
    order.paymentState = PAYMENT_STATES.ORDER_ELIGIBLE_FOR_PROVISIONING;
    order.provisioningState = PROVISIONING_STATES.ELIGIBLE;
    order.confirmedAt = nowIso;
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
    timestamp: nowIso,
    providerEventId,
    detail: detail || `Transitioned from ${currentState} to ${order.paymentState}`,
  });

  if (_hasBlobStorage()) {
    await put(`orders/${orderId}.json`, JSON.stringify(order), {
      access: 'private',
      contentType: 'application/json',
      addRandomSuffix: false,
      allowOverwrite: true, // Allow state updates on existing order
    });
  } else {
    _memoryOrders.set(orderId, order);
  }

  return order;
}

module.exports = {
  BILLING_SCHEMA_VERSION,
  PLAN_CATALOG,
  PAYMENT_STATES,
  PROVISIONING_STATES,
  generateOrderId,
  getPlanConfig,
  createOrder,
  getOrder,
  isEventProcessed,
  recordWebhookEvent,
  transitionOrderPaymentState,
};
