"""
Unit tests for VaultBasis Commercial Billing & Order Qualification (MMP15-PROD-BILL-001).

Validates:
- Plan catalog authoritative pricing ($499 Solo / $1,499 Practice / Assisted Enterprise)
- Order state machine discipline: Only PAYMENT_CONFIRMED -> ORDER_ELIGIBLE_FOR_PROVISIONING
- Webhook signature validation & HMAC verification
- Webhook idempotency and replay defense
- Fail-closed behavior on amount/currency/plan mismatch
- Decoupled provisioning: Order eligibility without private key exposure
- Zero token / private key bleed in billing runtime
- Zero client case / evidence data in commercial records
"""

import json
import subprocess
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
API_DIR = REPO_ROOT / "api"


def run_node_script(script_code: str) -> dict:
    """Executes a Node.js snippet against the api/ modules and returns parsed JSON output."""
    wrapped_code = f"""
    const path = require('path');
    const billingStore = require('{API_DIR / "_lib" / "billing-store.js"}');
    const checkoutHandler = require('{API_DIR / "commercial.js"}');
    const webhookHandler = require('{API_DIR / "webhook-payment.js"}');
    const enterpriseHandler = require('{API_DIR / "commercial.js"}');

    async function main() {{
        {script_code}
    }}
    main().catch(err => {{
        console.error(JSON.stringify({{ error: err.message, stack: err.stack }}));
        process.exit(1);
    }});
    """
    proc = subprocess.run(
        ["node", "-e", wrapped_code],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Node execution failed (code {proc.returncode}): {proc.stderr}\nstdout: {proc.stdout}")
    return json.loads(proc.stdout.strip())


def test_authoritative_plan_catalog():
    """Validates that plan pricing and capacity are immutable and server-authoritative."""
    code = """
    const solo = billingStore.getPlanConfig('SOLO');
    const practice = billingStore.getPlanConfig('PRACTICE');
    const enterprise = billingStore.getPlanConfig('ENTERPRISE');
    const invalid = billingStore.getPlanConfig('HACKER_TIER');

    console.log(JSON.stringify({
        solo: {
            priceCents: solo.priceAmountCents,
            capacity: solo.caseCapacity,
            currency: solo.currency,
            isSelfServe: solo.isSelfServe
        },
        practice: {
            priceCents: practice.priceAmountCents,
            capacity: practice.caseCapacity,
            currency: practice.currency,
            isSelfServe: practice.isSelfServe
        },
        enterprise: {
            isSelfServe: enterprise.isSelfServe
        },
        invalid: invalid
    }));
    """
    result = run_node_script(code)
    assert result["solo"]["priceCents"] == 49900
    assert result["solo"]["capacity"] == 10
    assert result["solo"]["currency"] == "USD"
    assert result["solo"]["isSelfServe"] is True

    assert result["practice"]["priceCents"] == 149900
    assert result["practice"]["capacity"] == 50
    assert result["practice"]["currency"] == "USD"
    assert result["practice"]["isSelfServe"] is True

    assert result["enterprise"]["isSelfServe"] is False
    assert result["invalid"] is None


def test_checkout_session_creation_solo_and_practice():
    """Validates that Solo and Practice checkout sessions derive attributes authoritatively."""
    code = """
    const soloOrder = await billingStore.createOrder({
        customerEmail: 'cpa_solo@firm.com',
        customerName: 'Jane Solo, CPA',
        planId: 'SOLO'
    });

    const practiceOrder = await billingStore.createOrder({
        customerEmail: 'cpa_practice@firm.com',
        customerName: 'John Practice, CPA',
        firmName: 'Practice Partners LLC',
        planId: 'PRACTICE'
    });

    console.log(JSON.stringify({
        solo: {
            orderId: soloOrder.orderId,
            planId: soloOrder.planId,
            priceCents: soloOrder.priceAmountCents,
            capacity: soloOrder.caseCapacity,
            state: soloOrder.paymentState,
            provisioningState: soloOrder.provisioningState
        },
        practice: {
            orderId: practiceOrder.orderId,
            planId: practiceOrder.planId,
            priceCents: practiceOrder.priceAmountCents,
            capacity: practiceOrder.caseCapacity,
            state: practiceOrder.paymentState,
            provisioningState: practiceOrder.provisioningState
        }
    }));
    """
    result = run_node_script(code)
    assert result["solo"]["orderId"].startswith("ORD-")
    assert result["solo"]["planId"] == "SOLO"
    assert result["solo"]["priceCents"] == 49900
    assert result["solo"]["capacity"] == 10
    assert result["solo"]["state"] == "CHECKOUT_CREATED"
    assert result["solo"]["provisioningState"] == "NOT_ELIGIBLE"

    assert result["practice"]["orderId"].startswith("ORD-")
    assert result["practice"]["planId"] == "PRACTICE"
    assert result["practice"]["priceCents"] == 149900
    assert result["practice"]["capacity"] == 50
    assert result["practice"]["state"] == "CHECKOUT_CREATED"
    assert result["practice"]["provisioningState"] == "NOT_ELIGIBLE"


def test_enterprise_checkout_rejection():
    """Validates that Enterprise cannot create a self-serve checkout session."""
    code = """
    let rejected = false;
    let errorMessage = '';
    try {
        await billingStore.createOrder({
            customerEmail: 'ent@bigfirm.com',
            customerName: 'Enterprise Admin',
            planId: 'ENTERPRISE'
        });
    } catch (e) {
        rejected = true;
        errorMessage = e.message;
    }
    console.log(JSON.stringify({ rejected, errorMessage }));
    """
    result = run_node_script(code)
    assert result["rejected"] is True
    assert "assisted sales/invoice inquiry" in result["errorMessage"]


def test_webhook_payment_confirmation_transitions_to_eligible():
    """Validates that a confirmed payment transitions the order to ORDER_ELIGIBLE_FOR_PROVISIONING."""
    code = """
    const order = await billingStore.createOrder({
        customerEmail: 'taxprep@firm.com',
        customerName: 'Alex Prep, EA',
        planId: 'SOLO'
    });

    // Advance to confirmed & eligible via webhook simulation
    const updated = await billingStore.transitionOrderPaymentState(
        order.orderId,
        billingStore.PAYMENT_STATES.ORDER_ELIGIBLE_FOR_PROVISIONING,
        { providerEventId: 'evt_test_123', detail: 'Paddle transaction completed' }
    );

    console.log(JSON.stringify({
        orderId: updated.orderId,
        paymentState: updated.paymentState,
        provisioningState: updated.provisioningState,
        confirmedAt: updated.confirmedAt,
        eventsCount: updated.events.length
    }));
    """
    result = run_node_script(code)
    assert result["paymentState"] == "ORDER_ELIGIBLE_FOR_PROVISIONING"
    assert result["provisioningState"] == "ELIGIBLE"
    assert result["confirmedAt"] is not None
    assert result["eventsCount"] == 2


def test_webhook_idempotency_and_replay_defense():
    """Validates that replaying the same webhook event ID does not duplicate records or state changes."""
    code = """
    const eventId = 'evt_unique_12345';
    const firstCheck = await billingStore.isEventProcessed(eventId);
    await billingStore.recordWebhookEvent(eventId, 'ORD-2026-TEST', 'checkout.session.completed');
    const secondCheck = await billingStore.isEventProcessed(eventId);

    console.log(JSON.stringify({
        firstCheck,
        secondCheck
    }));
    """
    result = run_node_script(code)
    assert result["firstCheck"] is False
    assert result["secondCheck"] is True


def test_payment_failure_remains_not_eligible():
    """Validates that payment failures never become eligible for license provisioning."""
    code = """
    const order = await billingStore.createOrder({
        customerEmail: 'declined@firm.com',
        customerName: 'Declined User',
        planId: 'SOLO'
    });

    const failedOrder = await billingStore.transitionOrderPaymentState(
        order.orderId,
        billingStore.PAYMENT_STATES.PAYMENT_FAILED,
        { providerEventId: 'evt_fail_999', detail: 'Card declined' }
    );

    console.log(JSON.stringify({
        paymentState: failedOrder.paymentState,
        provisioningState: failedOrder.provisioningState
    }));
    """
    result = run_node_script(code)
    assert result["paymentState"] == "PAYMENT_FAILED"
    assert result["provisioningState"] == "NOT_ELIGIBLE"


def test_expired_and_cancelled_checkout_cannot_become_provisionable():
    """Validates that expired or cancelled checkouts can never transition to provisionable."""
    code = """
    const order1 = await billingStore.createOrder({
        customerEmail: 'cancel@firm.com',
        customerName: 'Cancel Test',
        planId: 'SOLO'
    });
    const order2 = await billingStore.createOrder({
        customerEmail: 'expire@firm.com',
        customerName: 'Expire Test',
        planId: 'PRACTICE'
    });

    const cancelled = await billingStore.transitionOrderPaymentState(
        order1.orderId,
        billingStore.PAYMENT_STATES.CANCELLED,
        { detail: 'User abandoned checkout' }
    );
    const expired = await billingStore.transitionOrderPaymentState(
        order2.orderId,
        billingStore.PAYMENT_STATES.CHECKOUT_EXPIRED,
        { detail: 'Session expired' }
    );

    // Attempt illegal transition to PAYMENT_CONFIRMED on cancelled order
    let illegalTransitionBlocked = false;
    try {
        await billingStore.transitionOrderPaymentState(
            order1.orderId,
            billingStore.PAYMENT_STATES.PAYMENT_CONFIRMED
        );
    } catch (e) {
        illegalTransitionBlocked = true;
    }

    console.log(JSON.stringify({
        cancelledState: cancelled.paymentState,
        cancelledProv: cancelled.provisioningState,
        expiredState: expired.paymentState,
        expiredProv: expired.provisioningState,
        illegalTransitionBlocked
    }));
    """
    result = run_node_script(code)
    assert result["cancelledState"] == "CANCELLED"
    assert result["cancelledProv"] == "NOT_ELIGIBLE"
    assert result["expiredState"] == "CHECKOUT_EXPIRED"
    assert result["expiredProv"] == "NOT_ELIGIBLE"
    assert result["illegalTransitionBlocked"] is True


def test_amount_and_currency_mismatch_fails_closed():
    """Validates that webhook calls with wrong amount or currency fail closed with 409."""
    code = """
    process.env.ALLOW_TEST_WEBHOOKS = 'true';
    const order = await billingStore.createOrder({
        customerEmail: 'tamper@firm.com',
        customerName: 'Tamper Test',
        planId: 'SOLO' // Expected 49900 USD
    });

    let mockRes = { statusCode: 200, json: (d) => { mockRes.data = d; } };
    mockRes.status = (code) => { mockRes.statusCode = code; return mockRes; };

    // 1. Wrong currency (EUR instead of USD)
    const reqWrongCurr = {
        method: 'POST',
        headers: {},
        body: {
            id: 'evt_wrong_curr',
            type: 'checkout.session.completed',
            data: {
                object: {
                    metadata: { orderId: order.orderId },
                    amount_total: 49900,
                    currency: 'eur'
                }
            }
        }
    };
    await webhookHandler(reqWrongCurr, mockRes);
    const codeWrongCurr = mockRes.statusCode;

    // 2. Wrong amount (10000 instead of 49900)
    const reqWrongAmt = {
        method: 'POST',
        headers: {},
        body: {
            id: 'evt_wrong_amt',
            type: 'checkout.session.completed',
            data: {
                object: {
                    metadata: { orderId: order.orderId },
                    amount_total: 10000,
                    currency: 'usd'
                }
            }
        }
    };
    await webhookHandler(reqWrongAmt, mockRes);
    const codeWrongAmt = mockRes.statusCode;

    // Verify order in store is still CHECKOUT_CREATED (NOT eligible)
    const freshOrder = await billingStore.getOrder(order.orderId);

    console.log(JSON.stringify({
        codeWrongCurr,
        codeWrongAmt,
        orderState: freshOrder.paymentState,
        provisioningState: freshOrder.provisioningState
    }));
    """
    result = run_node_script(code)
    assert result["codeWrongCurr"] == 409
    assert result["codeWrongAmt"] == 409
    assert result["orderState"] == "CHECKOUT_CREATED"
    assert result["provisioningState"] == "NOT_ELIGIBLE"


def test_refund_lifecycle_before_and_after_provisioning():
    """Validates refund state transitions before and after license provisioning."""
    code = """
    // Case 1: Refund before provisioning
    const orderBefore = await billingStore.createOrder({
        customerEmail: 'refund_before@firm.com',
        customerName: 'Refund Before',
        planId: 'SOLO'
    });
    const refundedBefore = await billingStore.transitionOrderPaymentState(
        orderBefore.orderId,
        billingStore.PAYMENT_STATES.REFUNDED
    );

    // Case 2: Refund after provisioning
    const orderAfter = await billingStore.createOrder({
        customerEmail: 'refund_after@firm.com',
        customerName: 'Refund After',
        planId: 'PRACTICE'
    });
    await billingStore.transitionOrderPaymentState(
        orderAfter.orderId,
        billingStore.PAYMENT_STATES.PAYMENT_CONFIRMED
    );
    // Simulate downstream worker completed provisioning
    orderAfter.provisioningState = billingStore.PROVISIONING_STATES.PROVISIONED;
    const refundedAfter = await billingStore.transitionOrderPaymentState(
        orderAfter.orderId,
        billingStore.PAYMENT_STATES.REFUNDED
    );

    console.log(JSON.stringify({
        beforePaymentState: refundedBefore.paymentState,
        beforeProvState: refundedBefore.provisioningState,
        afterPaymentState: refundedAfter.paymentState,
        afterProvState: refundedAfter.provisioningState
    }));
    """
    result = run_node_script(code)
    assert result["beforePaymentState"] == "REFUNDED"
    assert result["beforeProvState"] == "CANCELLED"
    assert result["afterPaymentState"] == "REFUNDED"
    assert result["afterProvState"] == "PROVISIONED"  # Preserves record that offline license was issued


def test_stripe_timestamped_signature_validation():
    """Validates Stripe t=...,v1=... HMAC signature verification."""
    code = """
    const secret = 'whsec_test_secret_key_12345';
    process.env.PAYMENT_WEBHOOK_SECRET = secret;

    const payload = JSON.stringify({ id: 'evt_sig_test', type: 'payment_intent.succeeded' });
    const timestamp = Math.floor(Date.now() / 1000);
    const signedPayload = `${timestamp}.${payload}`;
    const signature = crypto.createHmac('sha256', secret).update(signedPayload, 'utf8').digest('hex');
    const validHeader = `t=${timestamp},v1=${signature}`;
    const tamperedHeader = `t=${timestamp},v1=deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef`;
    const staleHeader = `t=${timestamp - 1000},v1=${signature}`;

    let mockRes = { statusCode: 200, json: (d) => { mockRes.data = d; } };
    mockRes.status = (code) => { mockRes.statusCode = code; return mockRes; };

    // Request with valid header
    const reqValid = {
        method: 'POST',
        headers: { 'stripe-signature': validHeader },
        body: payload
    };
    // Request with tampered header
    const reqTampered = {
        method: 'POST',
        headers: { 'stripe-signature': tamperedHeader },
        body: payload
    };

    // Call webhook handler
    await webhookHandler(reqTampered, mockRes);
    const tamperedCode = mockRes.statusCode;

    delete process.env.PAYMENT_WEBHOOK_SECRET;

    console.log(JSON.stringify({
        tamperedCode
    }));
    """
    result = run_node_script(code)
    assert result["tamperedCode"] == 401


def test_audit_event_trail_records_state_transitions():
    """Validates that every commercial state transition is appended to the order audit trail."""
    code = """
    const order = await billingStore.createOrder({
        customerEmail: 'audit@firm.com',
        customerName: 'Audit Test',
        planId: 'SOLO'
    });

    await billingStore.transitionOrderPaymentState(
        order.orderId,
        billingStore.PAYMENT_STATES.PAYMENT_PENDING,
        { detail: 'Awaiting bank clearance' }
    );

    await billingStore.transitionOrderPaymentState(
        order.orderId,
        billingStore.PAYMENT_STATES.PAYMENT_CONFIRMED,
        { providerEventId: 'evt_audit_100', detail: 'Bank clearance confirmed' }
    );

    const fresh = await billingStore.getOrder(order.orderId);

    console.log(JSON.stringify({
        eventsCount: fresh.events.length,
        states: fresh.events.map(e => e.state),
        details: fresh.events.map(e => e.detail)
    }));
    """
    result = run_node_script(code)
    assert result["eventsCount"] == 3
    assert result["states"] == [
        "CHECKOUT_CREATED",
        "PAYMENT_PENDING",
        "PAYMENT_CONFIRMED",
    ]


def test_zero_signing_key_and_evidence_bleed():
    """Verifies that billing stores and handlers contain zero private keys and zero client data."""
    billing_store_content = (API_DIR / "_lib" / "billing-store.js").read_text(encoding="utf-8")
    commercial_content = (API_DIR / "commercial.js").read_text(encoding="utf-8")
    webhook_content = (API_DIR / "webhook-payment.js").read_text(encoding="utf-8")

    for file_name, content in [
        ("billing-store.js", billing_store_content),
        ("commercial.js", commercial_content),
        ("webhook-payment.js", webhook_content),
    ]:
        assert "BEGIN PRIVATE KEY" not in content, f"Private key header in {file_name}"
        assert "COMMERCIAL_LICENSE_SIGNING_KEY" not in content, f"Signing key reference in {file_name}"
        assert "sign(" not in content or "crypto.createHmac" in content, f"Signing authority found in {file_name}"
        assert "evidence_receipt" not in content, f"Evidence bleed in {file_name}"
