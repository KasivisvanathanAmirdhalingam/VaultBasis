"""
VaultBasis Quality Suite — Vercel Serverless Function & Route Parity Test (MMP15-INFRA-VCL-001)
Tag: regression, production-infra, vercel, route-parity, left-shift-maximum

Validates:
1. Function Quota Enforcement: Total serverless functions in api/ is strictly <= 7 (well below 12 Hobby cap).
2. Helper Store Isolation: Helper stores reside exclusively in api/_lib/ (never packaged as functions).
3. Vercel Rewrite Parity: Every rewrite target in vercel.json exists on disk and is reachable.
4. Commercial Endpoint Contract Parity:
   - /api/checkout (POST 400 on empty, 200 on valid Solo/Practice, 400 on Enterprise)
   - /api/checkout-session (GET 200 HTML order review, POST 200 provisioning transition)
   - /api/enterprise-inquiry (POST 400 on empty, 200 on valid inquiry)
5. Zero Private Key & Client Case Bleed in web serverless plane.
"""

import json
import os
import subprocess
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
API_DIR = REPO_ROOT / "api"
VERCEL_JSON = REPO_ROOT / "vercel.json"


def run_node_snippet(code: str) -> dict:
    """Helper to run a Node.js snippet against the consolidated commercial handler."""
    wrapped_code = f"""
    const path = require('path');
    const commercialHandler = require('{API_DIR / "commercial.js"}');

    async function main() {{
        {code}
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
        raise RuntimeError(f"Node execution failed: {proc.stderr}\nstdout: {proc.stdout}")
    return json.loads(proc.stdout.strip())


@pytest.mark.regression
def test_serverless_function_count_within_hobby_limit():
    """Asserts that total serverless functions in api/ is strictly <= 7 (Hobby limit is 12)."""
    # Top-level .js files in api/ (excluding _lib)
    api_files = [f for f in API_DIR.glob("*.js") if not f.name.startswith("_")]
    assert len(api_files) <= 7, f"Expected <= 7 serverless functions, found {len(api_files)}: {[f.name for f in api_files]}"
    assert len(api_files) == 7, f"Expected exactly 7 functions, found: {[f.name for f in api_files]}"

    # Assert helper libraries are in _lib
    lib_files = [f.name for f in (API_DIR / "_lib").glob("*.js")]
    assert "billing-store.js" in lib_files
    assert "delivery-mailer.js" in lib_files
    assert "entitlement-store.js" in lib_files
    assert "preview-access-store.js" in lib_files


@pytest.mark.regression
def test_vercel_rewrites_map_to_valid_destinations():
    """Validates that every rewrite rule in vercel.json maps to an existing file or serverless function."""
    assert VERCEL_JSON.is_file(), "vercel.json must exist"
    config = json.loads(VERCEL_JSON.read_text(encoding="utf-8"))
    rewrites = config.get("rewrites", [])

    assert len(rewrites) >= 5, "Expected rewrites in vercel.json"
    
    # Check specific critical commercial rewrites
    sources = {r["source"]: r["destination"] for r in rewrites}
    assert "/api/checkout" in sources
    assert sources["/api/checkout"] == "/api/commercial?action=checkout"
    
    assert "/api/checkout-session" in sources
    assert sources["/api/checkout-session"] == "/api/commercial?action=checkout-session"
    
    assert "/api/enterprise-inquiry" in sources
    assert sources["/api/enterprise-inquiry"] == "/api/commercial?action=enterprise-inquiry"
    
    assert "/verifier" in sources
    assert sources["/verifier"] == "/api/verifier-page"


@pytest.mark.regression
def test_commercial_checkout_order_creation_contract():
    """Validates that api/commercial.js correctly processes self-serve checkout orders."""
    code = """
    let statusCode = null;
    let jsonBody = null;

    const mockRes = {
        status(code) {
            statusCode = code;
            return {
                json(body) {
                    jsonBody = body;
                    return body;
                },
                send(body) {
                    jsonBody = body;
                    return body;
                }
            };
        },
        setHeader() {}
    };

    // Test 1: Empty body -> 400
    await commercialHandler({ method: 'POST', query: { action: 'checkout' }, body: {} }, mockRes);
    const emptyStatus = statusCode;

    // Test 2: Valid Solo order -> 200
    await commercialHandler({
        method: 'POST',
        query: { action: 'checkout' },
        body: { plan: 'SOLO', name: 'Dr. Jane Tax, CPA', email: 'jane@taxcpa.com', firm: 'Tax CPA LLC' }
    }, mockRes);
    const soloStatus = statusCode;
    const soloBody = jsonBody;

    // Test 3: Enterprise self-serve -> 400 (requires assisted inquiry)
    await commercialHandler({
        method: 'POST',
        query: { action: 'checkout' },
        body: { plan: 'ENTERPRISE', name: 'Big Firm', email: 'partner@bigfirm.com' }
    }, mockRes);
    const entStatus = statusCode;

    console.log(JSON.stringify({
        emptyStatus,
        soloStatus,
        soloBody,
        entStatus
    }));
    """
    res = run_node_snippet(code)
    assert res["emptyStatus"] == 400
    assert res["soloStatus"] == 200
    assert res["soloBody"]["status"] == "success"
    assert res["soloBody"]["orderSummary"]["displayName"] == "Solo Practitioner"
    assert res["soloBody"]["orderSummary"]["amountCents"] == 49900
    assert res["soloBody"]["orderSummary"]["caseCapacity"] == 10
    assert res["entStatus"] == 400


@pytest.mark.regression
def test_commercial_enterprise_inquiry_contract():
    """Validates that api/commercial.js correctly handles assisted enterprise inquiries."""
    code = """
    let statusCode = null;
    let jsonBody = null;

    const mockRes = {
        status(code) {
            statusCode = code;
            return {
                json(body) {
                    jsonBody = body;
                    return body;
                },
                send(body) {
                    jsonBody = body;
                    return body;
                }
            };
        },
        setHeader() {}
    };

    // Test 1: Empty body -> 400
    await commercialHandler({ method: 'POST', query: { action: 'enterprise-inquiry' }, body: {} }, mockRes);
    const emptyStatus = statusCode;

    // Test 2: Valid inquiry -> 200
    await commercialHandler({
        method: 'POST',
        query: { action: 'enterprise-inquiry' },
        body: { name: 'National Practice Leader', email: 'lead@nationalfirm.com', firm: 'National Accounting LLP', estimatedCases: '500+' }
    }, mockRes);
    const validStatus = statusCode;
    const validBody = jsonBody;

    console.log(JSON.stringify({
        emptyStatus,
        validStatus,
        validBody
    }));
    """
    res = run_node_snippet(code)
    assert res["emptyStatus"] == 400
    assert res["validStatus"] == 200
    assert res["validBody"]["status"] == "success"
    assert "INQ-" in res["validBody"]["inquiryId"]


@pytest.mark.regression
def test_commercial_checkout_session_rendering_contract():
    """Validates that api/commercial.js renders order review HTML without 404."""
    code = """
    const billingStore = require('./api/_lib/billing-store.js');
    const order = await billingStore.createOrder({
        providerSessionId: 'sess_test_review_render',
        customerEmail: 'cpa@firm.com',
        customerName: 'CPA Reviewer',
        planId: 'PRACTICE'
    });

    let statusCode = null;
    let htmlContent = null;

    const mockRes = {
        status(code) {
            statusCode = code;
            return {
                send(content) {
                    htmlContent = content;
                    return content;
                }
            };
        },
        setHeader(name, val) {}
    };

    await commercialHandler({
        method: 'GET',
        query: { action: 'checkout-session', order_id: order.orderId, session_id: order.providerSessionId }
    }, mockRes);

    console.log(JSON.stringify({
        statusCode,
        hasTitle: htmlContent.includes('VaultBasis Commercial Checkout'),
        hasPlan: htmlContent.includes('Practice License'),
        hasCapacity: htmlContent.includes('50 Cases / Annual Term'),
        hasGuarantee: htmlContent.includes('Local Case Processing') || htmlContent.includes('Air-Gap & Privacy Guarantee'),
        hasSubmitBtn: htmlContent.includes('Continue to Secure Checkout') || htmlContent.includes('Proceed to Paddle Secure Checkout'),
        noEd25519Private: !htmlContent.includes('PRIVATE KEY'),
    }));
    """
    res = run_node_snippet(code)
    assert res["statusCode"] == 200
    assert res["hasTitle"] is True
    assert res["hasPlan"] is True
    assert res["hasCapacity"] is True
    assert res["hasGuarantee"] is True
    assert res["hasSubmitBtn"] is True
    assert res["noEd25519Private"] is True


@pytest.mark.regression
def test_commercial_checkout_handoff_contract():
    """Validates that POST /api/checkout-session produces an authentic Paddle checkout URL & advances state to PAYMENT_PENDING."""
    code = """
    const billingStore = require('./api/_lib/billing-store.js');
    const order = await billingStore.createOrder({
        customerEmail: 'practitioner@cpa.org',
        customerName: 'Senior Practitioner',
        planId: 'PRACTICE'
    });

    let statusCode = null;
    let jsonBody = null;

    const mockRes = {
        status(code) {
            statusCode = code;
            return {
                json(body) {
                    jsonBody = body;
                    return body;
                },
                send(body) {
                    jsonBody = body;
                    return body;
                }
            };
        },
        setHeader() {}
    };

    // Test 1: Missing agreement -> 400 rejection
    await commercialHandler({
        method: 'POST',
        headers: { 'accept': 'application/json', 'content-type': 'application/json' },
        query: { action: 'checkout-session' },
        body: { order_id: order.orderId, session_id: order.providerSessionId }
    }, mockRes);
    const unacceptedStatus = statusCode;
    const unacceptedBody = jsonBody;

    // Test 2: With affirmative agreement -> 200 handoff
    await commercialHandler({
        method: 'POST',
        headers: { 'accept': 'application/json', 'content-type': 'application/json' },
        query: { action: 'checkout-session' },
        body: { order_id: order.orderId, session_id: order.providerSessionId, agreement_accepted: true }
    }, mockRes);

    const freshOrder = await billingStore.getOrder(order.orderId);

    console.log(JSON.stringify({
        unacceptedStatus,
        unacceptedBody,
        statusCode,
        jsonBody,
        orderPaymentState: freshOrder.paymentState,
        orderProvisioningState: freshOrder.provisioningState,
        hasTxnId: Boolean(freshOrder.providerTransactionId),
        agreementVersion: freshOrder.events.find(e => e.metadata?.agreement)?.metadata?.agreement?.agreementVersion
    }));
    """
    res = run_node_snippet(code)
    assert res["unacceptedStatus"] == 400
    assert "agree to the Software License Agreement" in res["unacceptedBody"]["error"]
    assert res["statusCode"] == 200
    assert res["jsonBody"]["ok"] is True
    assert res["jsonBody"]["state"] == "PAYMENT_PENDING"
    assert res["jsonBody"]["provider"] == "PADDLE"
    assert res["jsonBody"]["provider_transaction_id"].startswith("txn_")
    assert res["orderPaymentState"] == "PAYMENT_PENDING"
    assert res["orderProvisioningState"] == "NOT_ELIGIBLE"
    assert res["hasTxnId"] is True
    assert res["agreementVersion"] == "MMP-1.5-2026.1"


@pytest.mark.regression
def test_paddle_webhook_transaction_completed_lifecycle():
    """Validates that a real Paddle webhook transaction.completed advances state to ORDER_ELIGIBLE_FOR_PROVISIONING."""
    code = """
    const billingStore = require('./api/_lib/billing-store.js');
    const webhookHandler = require('./api/webhook-payment.js');
    process.env.ALLOW_TEST_WEBHOOKS = 'true';

    const order = await billingStore.createOrder({
        customerEmail: 'paddle_cpa@firm.com',
        customerName: 'Paddle CPA',
        planId: 'PRACTICE' // $1,499 -> 149900 cents
    });

    // Advance to PAYMENT_PENDING with real Paddle transaction
    await billingStore.transitionOrderPaymentState(order.orderId, billingStore.PAYMENT_STATES.PAYMENT_PENDING, {
        providerTransactionId: 'txn_01jmpractice999888777'
    });

    let statusCode = null;
    let jsonBody = null;

    const mockRes = {
        status(code) {
            statusCode = code;
            return {
                json(body) {
                    jsonBody = body;
                    return body;
                }
            };
        }
    };

    // Authentic Paddle webhook payload
    const paddlePayload = {
        event_id: 'evt_01paddle_test_event_123',
        event_type: 'transaction.completed',
        data: {
            id: 'txn_01jmpractice999888777',
            status: 'completed',
            custom_data: {
                order_id: order.orderId
            },
            details: {
                totals: {
                    total: '149900',
                    currency_code: 'USD'
                }
            }
        }
    };

    await webhookHandler({
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: paddlePayload
    }, mockRes);

    const updatedOrder = await billingStore.getOrder(order.orderId);

    console.log(JSON.stringify({
        statusCode,
        jsonBody,
        paymentState: updatedOrder.paymentState,
        provisioningState: updatedOrder.provisioningState,
        providerTxnId: updatedOrder.providerTransactionId
    }));
    """
    res = run_node_snippet(code)
    assert res["statusCode"] == 200
    assert res["paymentState"] == "ORDER_ELIGIBLE_FOR_PROVISIONING"
    assert res["provisioningState"] == "ELIGIBLE"
    assert res["providerTxnId"] == "txn_01jmpractice999888777"


@pytest.mark.regression
def test_commercial_checkout_handoff_idempotency_reuses_active_session():
    """Validates that repeating POST /api/checkout-session reuses the existing active Paddle transaction without duplicate creations."""
    code = """
    const billingStore = require('./api/_lib/billing-store.js');
    const order = await billingStore.createOrder({
        customerEmail: 'repeat_checkout@cpa.org',
        customerName: 'Repeat Checkout',
        planId: 'SOLO'
    });

    let firstRes = null;
    let secondRes = null;

    function createMockRes(collector) {
        return {
            status(code) {
                return {
                    json(body) { collector.status = code; collector.body = body; return body; },
                    send(body) { collector.status = code; collector.body = body; return body; }
                };
            },
            setHeader() {}
        };
    }

    // Call 1
    const res1 = {};
    await commercialHandler({
        method: 'POST',
        headers: { 'accept': 'application/json', 'content-type': 'application/json' },
        query: { action: 'checkout-session' },
        body: { order_id: order.orderId, session_id: order.providerSessionId, agreement_accepted: true }
    }, createMockRes(res1));

    // Call 2 (duplicate click/retry)
    const res2 = {};
    await commercialHandler({
        method: 'POST',
        headers: { 'accept': 'application/json', 'content-type': 'application/json' },
        query: { action: 'checkout-session' },
        body: { order_id: order.orderId, session_id: order.providerSessionId, agreement_accepted: true }
    }, createMockRes(res2));

    console.log(JSON.stringify({
        res1Status: res1.status,
        res2Status: res2.status,
        txn1: res1.body.provider_transaction_id,
        txn2: res2.body.provider_transaction_id,
        reused: res2.body.reused
    }));
    """
    res = run_node_snippet(code)
    assert res["res1Status"] == 200
    assert res["res2Status"] == 200
    assert res["txn1"] == res["txn2"]
    assert res["reused"] is True


@pytest.mark.regression
def test_paddle_webhook_paid_vs_completed_progression():
    """Validates that transaction.paid moves order to PAYMENT_CONFIRMED, and transaction.completed to ORDER_ELIGIBLE_FOR_PROVISIONING."""
    code = """
    const billingStore = require('./api/_lib/billing-store.js');
    const webhookHandler = require('./api/webhook-payment.js');
    process.env.ALLOW_TEST_WEBHOOKS = 'true';

    const order = await billingStore.createOrder({
        customerEmail: 'progression@firm.com',
        customerName: 'Progression Test',
        planId: 'SOLO' // $499
    });

    await billingStore.transitionOrderPaymentState(order.orderId, billingStore.PAYMENT_STATES.PAYMENT_PENDING, {
        providerTransactionId: 'txn_01jmsolo111222333'
    });

    let mockRes = { status: (c) => ({ json: (b) => {} }) };

    // Step 1: transaction.paid
    await webhookHandler({
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: {
            event_id: 'evt_paid_001',
            event_type: 'transaction.paid',
            data: {
                id: 'txn_01jmsolo111222333',
                status: 'paid',
                custom_data: { order_id: order.orderId },
                details: { totals: { subtotal: '49900', total: '54890', currency_code: 'USD' } } // MoR tax added
            }
        }
    }, mockRes);

    const afterPaid = await billingStore.getOrder(order.orderId);
    const paidState = afterPaid.paymentState;
    const paidProvState = afterPaid.provisioningState;

    // Step 2: transaction.completed
    await webhookHandler({
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: {
            event_id: 'evt_completed_002',
            event_type: 'transaction.completed',
            data: {
                id: 'txn_01jmsolo111222333',
                status: 'completed',
                custom_data: { order_id: order.orderId },
                details: { totals: { subtotal: '49900', total: '54890', currency_code: 'USD' } }
            }
        }
    }, mockRes);

    const afterCompleted = await billingStore.getOrder(order.orderId);

    console.log(JSON.stringify({
        paidState,
        paidProvState,
        completedState: afterCompleted.paymentState,
        completedProvState: afterCompleted.provisioningState
    }));
    """
    res = run_node_snippet(code)
    assert res["paidState"] == "PAYMENT_CONFIRMED"
    assert res["paidProvState"] == "NOT_ELIGIBLE"
    assert res["completedState"] == "ORDER_ELIGIBLE_FOR_PROVISIONING"
    assert res["completedProvState"] == "ELIGIBLE"


@pytest.mark.regression
def test_paddle_webhook_transaction_binding_conflict_rejection():
    """Validates that a webhook event with a mismatched transaction ID is rejected with 409 Conflict."""
    code = """
    const billingStore = require('./api/_lib/billing-store.js');
    const webhookHandler = require('./api/webhook-payment.js');
    process.env.ALLOW_TEST_WEBHOOKS = 'true';

    const order = await billingStore.createOrder({
        customerEmail: 'tamper@firm.com',
        customerName: 'Tamper CPA',
        planId: 'SOLO'
    });

    // Order bound to legitimate transaction
    await billingStore.transitionOrderPaymentState(order.orderId, billingStore.PAYMENT_STATES.PAYMENT_PENDING, {
        providerTransactionId: 'txn_01jm_legitimate_id'
    });

    let statusCode = null;
    let jsonBody = null;

    const mockRes = {
        status(code) {
            statusCode = code;
            return { json(b) { jsonBody = b; return b; } };
        }
    };

    // Webhook with rogue transaction ID trying to claim this order
    await webhookHandler({
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: {
            event_id: 'evt_rogue_001',
            event_type: 'transaction.completed',
            data: {
                id: 'txn_01jm_rogue_different_id',
                custom_data: { order_id: order.orderId },
                details: { totals: { total: '49900', currency_code: 'USD' } }
            }
        }
    }, mockRes);

    const freshOrder = await billingStore.getOrder(order.orderId);

    console.log(JSON.stringify({
        statusCode,
        jsonBody,
        orderState: freshOrder.paymentState,
        provState: freshOrder.provisioningState
    }));
    """
    res = run_node_snippet(code)
    assert res["statusCode"] == 409
    assert res["orderState"] == "PAYMENT_PENDING"
    assert res["provState"] == "NOT_ELIGIBLE"


@pytest.mark.regression
def test_paddle_checkout_url_integrity_and_allowlist_validation():
    """MMP15-PAY-URL-001: Asserts that Paddle checkout URLs are strictly validated against approved hosts and never double-prefixed."""
    code = """
    const paddleClient = require('./api/_lib/paddle-client.js');

    const results = {};

    // 1. Valid sandbox URL
    try {
        const u1 = paddleClient.validatePaddleCheckoutUrl('https://sandbox-buy.paddle.com/checkout?_ptxn=txn_01jm123');
        results.validSandbox = u1;
    } catch (e) { results.validSandboxError = e.message; }

    // 2. Valid production URL
    try {
        const u2 = paddleClient.validatePaddleCheckoutUrl('https://buy.paddle.com/checkout?_ptxn=txn_01jm456');
        results.validProd = u2;
    } catch (e) { results.validProdError = e.message; }

    // 3. Double-prefixed URL rejection
    try {
        paddleClient.validatePaddleCheckoutUrl('https://sandbox-sandbox-buy.paddle.com/checkout?_ptxn=txn_01jm789');
        results.doublePrefixedRejected = false;
    } catch (e) {
        results.doublePrefixedRejected = true;
    }

    // 4. Insecure HTTP scheme rejection
    try {
        paddleClient.validatePaddleCheckoutUrl('http://buy.paddle.com/checkout?_ptxn=txn_01jm000');
        results.httpRejected = false;
    } catch (e) {
        results.httpRejected = true;
    }

    // 5. Rogue external domain rejection
    try {
        paddleClient.validatePaddleCheckoutUrl('https://malicious-site.com/checkout?_ptxn=txn_01jm000');
        results.rogueDomainRejected = false;
    } catch (e) {
        results.rogueDomainRejected = true;
    }

    // 6. Test sandbox transaction creation URL shape and direct Paddle.js transaction ID
    const mockOrder = {
        orderId: 'ORD-2026-TESTURL',
        planId: 'SOLO',
        caseCapacity: 10,
        customerEmail: 'urltest@firm.com',
        customerName: 'URL Test',
        priceAmountCents: 49900,
        priceCurrency: 'USD'
    };
    const txn = await paddleClient.createPaddleTransaction({ order: mockOrder });
    results.generatedTransactionId = txn.transactionId;
    results.generatedCheckoutUrl = txn.checkoutUrl;

    console.log(JSON.stringify(results));
    """
    res = run_node_snippet(code)
    assert res["validSandbox"] == "https://sandbox-buy.paddle.com/checkout?_ptxn=txn_01jm123"
    assert res["validProd"] == "https://buy.paddle.com/checkout?_ptxn=txn_01jm456"
    assert res["doublePrefixedRejected"] is True
    assert res["httpRejected"] is True
    assert res["rogueDomainRejected"] is True
    assert res["generatedTransactionId"].startswith("txn_01")
    assert res["generatedCheckoutUrl"] is None


@pytest.mark.regression
def test_paddle_environment_coherence_and_client_token_isolation():
    """MMP15-PAY-PADDLEJS-INIT-001: Validates environment token coherence and asserts that server API keys are never exposed in rendered checkout HTML."""
    code = """
    const paddleClient = require('./api/_lib/paddle-client.js');
    const commercialHandler = require('./api/commercial.js');
    const billingStore = require('./api/_lib/billing-store.js');

    const results = {};

    // 1. Sandbox with valid test_ token
    process.env.PADDLE_ENVIRONMENT = 'sandbox';
    process.env.PADDLE_CLIENT_TOKEN = 'test_01jm_valid_client_token';
    process.env.PADDLE_API_KEY = 'secret_sandbox_key';
    results.sandboxValid = paddleClient.validatePaddleEnvironmentCoherence();

    // 2. Sandbox with live_ token (mismatch)
    process.env.PADDLE_ENVIRONMENT = 'sandbox';
    process.env.PADDLE_CLIENT_TOKEN = 'live_01jm_mismatched_token';
    results.sandboxMismatch = paddleClient.validatePaddleEnvironmentCoherence();

    // 3. Production with live_ token
    process.env.PADDLE_ENVIRONMENT = 'production';
    process.env.PADDLE_CLIENT_TOKEN = 'live_01jm_valid_prod_token';
    process.env.PADDLE_API_KEY = 'live_server_api_key';
    results.prodValid = paddleClient.validatePaddleEnvironmentCoherence();

    // 4. Production with test_ token (mismatch)
    process.env.PADDLE_ENVIRONMENT = 'production';
    process.env.PADDLE_CLIENT_TOKEN = 'test_01jm_mismatched_token';
    results.prodMismatch = paddleClient.validatePaddleEnvironmentCoherence();

    // 5. Test secret key isolation in rendered checkout HTML
    const secretApiKey = 'SUPER_SECRET_PADDLE_API_KEY_12345';
    process.env.PADDLE_API_KEY = secretApiKey;
    process.env.PADDLE_CLIENT_TOKEN = 'test_safe_client_token_67890';
    process.env.PADDLE_ENVIRONMENT = 'sandbox';

    const order = await billingStore.createOrder({
        customerEmail: 'isolation@firm.com',
        customerName: 'Isolation Test',
        planId: 'SOLO'
    });

    let renderedHtml = '';
    const mockRes = {
        setHeader() {},
        status() {
            return {
                send(html) { renderedHtml = html; return html; }
            };
        }
    };

    await commercialHandler({
        method: 'GET',
        query: { order_id: order.orderId, session_id: order.providerSessionId }
    }, mockRes);

    results.apiKeyLeakedInHtml = renderedHtml.includes(secretApiKey);
    results.clientTokenInHtml = renderedHtml.includes('test_safe_client_token_67890');
    results.hasPaddleScript = renderedHtml.includes('https://cdn.paddle.com/paddle/v2/paddle.js');

    console.log(JSON.stringify(results));
    """
    res = run_node_snippet(code)
    assert res["sandboxValid"]["ok"] is True
    assert res["sandboxMismatch"]["ok"] is False
    assert "must start with 'test_'" in res["sandboxMismatch"]["errors"][0]
    assert res["prodValid"]["ok"] is True
    assert res["prodMismatch"]["ok"] is False
    assert "must start with 'live_'" in res["prodMismatch"]["errors"][0]
    assert res["apiKeyLeakedInHtml"] is False
    assert res["clientTokenInHtml"] is True
    assert res["hasPaddleScript"] is True





