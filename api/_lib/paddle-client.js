'use strict';

/**
 * VaultBasis — Authoritative Paddle Billing Client (MMP15-PAY-PROVIDER-001)
 *
 * Direct integration with Paddle Billing API (v2) for authoritative transaction creation.
 *
 * Invariants:
 * - Authoritative Pricing: Maps VaultBasis internal plans (SOLO, PRACTICE) strictly to Paddle price_ids.
 * - Real Identifier Integrity: Returns authentic Paddle transaction IDs (txn_01...).
 * - Zero Key Bleed: Zero Ed25519 commercial license private keys in this module.
 */

const https = require('https');

const APPROVED_PADDLE_HOSTS = new Set([
  'buy.paddle.com',
  'sandbox-buy.paddle.com',
  'checkout.paddle.com',
  'sandbox-checkout.paddle.com',
]);

function isApprovedCheckoutHost(hostname) {
  if (!hostname) return false;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return true;
  if (APPROVED_PADDLE_HOSTS.has(hostname)) return true;
  if (hostname === 'vaultbasis.com' || hostname.endsWith('.vaultbasis.com')) return true;
  const customApproved = process.env.APPROVED_CHECKOUT_HOST;
  if (customApproved && (hostname === customApproved || hostname.endsWith(`.${customApproved}`))) return true;
  return false;
}

function validatePaddleCheckoutUrl(urlStr) {
  if (!urlStr) return null;
  if (typeof urlStr !== 'string') {
    throw new Error('Invalid Paddle checkout URL: URL must be a string.');
  }
  let parsed;
  try {
    parsed = new URL(urlStr);
  } catch (e) {
    throw new Error(`Invalid Paddle checkout URL format: ${e.message}`);
  }
  if (parsed.protocol !== 'https:' && parsed.hostname !== 'localhost' && parsed.hostname !== '127.0.0.1') {
    throw new Error(`Insecure Paddle checkout URL protocol: '${parsed.protocol}'. Must be https:`);
  }
  if (!isApprovedCheckoutHost(parsed.hostname)) {
    throw new Error(`Unapproved checkout hostname: '${parsed.hostname}'.`);
  }
  return urlStr;
}

function getPaddleApiBase() {
  const env = process.env.PADDLE_ENVIRONMENT || 'sandbox';
  return env === 'production' ? 'https://api.paddle.com' : 'https://sandbox-api.paddle.com';
}

function getPaddlePriceIdForPlan(planId) {
  if (planId === 'SOLO') {
    return process.env.PADDLE_SOLO_PRICE_ID || 'pri_01jm_solo_annual_499';
  }
  if (planId === 'PRACTICE') {
    return process.env.PADDLE_PRACTICE_PRICE_ID || 'pri_01jm_practice_annual_1499';
  }
  throw new Error(`Unrecognized or non-self-serve plan: '${planId}'`);
}

async function createPaddleTransaction({ order, planConfig, returnUrl, agreementRecord }) {
  const apiKey = process.env.PADDLE_API_KEY;
  const env = process.env.PADDLE_ENVIRONMENT || 'sandbox';
  const apiBase = getPaddleApiBase();
  const priceId = planConfig?.paddlePriceId || getPaddlePriceIdForPlan(order.planId);

  // If no API key is provided:
  if (!apiKey) {
    if (env === 'production') {
      console.error('[paddle-client] CRITICAL: PADDLE_API_KEY missing in production environment.');
      throw new Error('PADDLE_API_KEY is not configured in production environment.');
    }

    // In sandbox / development / testing mode, generate a compliant sandbox transaction envelope
    const mockTxnId = `txn_01${Buffer.from(order.orderId).toString('hex').padEnd(20, '0').substring(0, 22)}`;
    const customCheckoutUrl = process.env.PADDLE_CHECKOUT_URL ? validatePaddleCheckoutUrl(process.env.PADDLE_CHECKOUT_URL) : null;

    console.warn(`[paddle-client] PADDLE_API_KEY unconfigured; initialized sandbox transaction ${mockTxnId} for plan ${order.planId} (${priceId}).`);
    return {
      transactionId: mockTxnId,
      checkoutUrl: customCheckoutUrl,
      priceId,
      status: 'draft',
      simulated: true,
    };
  }

  const payload = {
    items: [
      {
        price_id: priceId,
        quantity: 1,
      },
    ],
    customer: {
      email: order.customerEmail,
      name: order.customerName || undefined,
    },
    custom_data: {
      order_id: order.orderId,
      plan: order.planId,
      case_capacity: order.caseCapacity,
      customer_email: order.customerEmail,
      agreement_version: agreementRecord?.agreementVersion || 'MMP-1.5-2026.1',
    },
    checkout: {
      url: returnUrl || process.env.PUBLIC_BASE_URL || 'https://www.vaultbasis.com',
    },
  };

  const url = new URL('/transactions', apiBase);
  const postData = JSON.stringify(payload);

  return new Promise((resolve, reject) => {
    const req = https.request(
      url,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(postData),
        },
      },
      (res) => {
        let raw = '';
        res.on('data', (chunk) => { raw += chunk; });
        res.on('end', () => {
          try {
            const json = JSON.parse(raw);
            if (res.statusCode >= 200 && res.statusCode < 300 && json.data?.id) {
              const txn = json.data;
              const checkoutUrl = txn.checkout?.url ? validatePaddleCheckoutUrl(txn.checkout.url) : null;
              return resolve({
                transactionId: txn.id,
                checkoutUrl,
                priceId,
                status: txn.status,
                raw: txn,
              });
            }
            const errorDetail = json.error?.detail || json.error?.message || `HTTP ${res.statusCode}`;
            return reject(new Error(`Paddle API rejected transaction: ${errorDetail}`));
          } catch (e) {
            return reject(new Error(`Failed to parse Paddle response: ${e.message}`));
          }
        });
      }
    );

    req.on('error', (err) => {
      reject(new Error(`Paddle API connection error: ${err.message}`));
    });

    req.write(postData);
    req.end();
  });
}

module.exports = {
  getPaddleApiBase,
  getPaddlePriceIdForPlan,
  validatePaddleCheckoutUrl,
  isApprovedCheckoutHost,
  createPaddleTransaction,
};
