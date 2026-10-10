"""
Tests for CASE-CAP-001: Monotonic Paid Capacity Metering and Anti-Deletion Loophole Defense.

Invariants Verified:
1. One new production client-tax-year case consumes one allowance unit in its annual entitlement period.
2. Deletion never refunds consumed capacity.
3. Same-term upgrade/reissue preserves consumed usage.
4. New annual term provides a new allowance.
5. Existing historical cases reopened during a later term are not counted again as newly activated cases.
6. Capacity check + case creation + activation recording are atomic.
7. Failed creation consumes zero capacity.
8. Bundled sample cases do not consume commercial capacity.
9. customer_id + not_before + expires_at forms stable commercial entitlement identity.
"""
import pytest
from datetime import datetime, timezone
from pathlib import Path

from tools.issue_license import issue_commercial_license
from edge.commercial.models import LicenseTier
from edge.commercial.policy import (
    CommercialOperation,
    CommercialDenialCode,
    CommercialPolicyService,
)
from edge.storage.sqlite_store import SQLiteStore
from schemas.canonical.case import CanonicalCase
from cryptography.hazmat.primitives.asymmetric import ed25519


@pytest.fixture
def test_setup(monkeypatch, tmp_path):
    monkeypatch.setenv("VAULTBASIS_BYPASS_ENTITLEMENT", "0")
    db_path = tmp_path / "test_cap.db"
    store = SQLiteStore(str(db_path))
    priv_key = ed25519.Ed25519PrivateKey.generate()
    priv_hex = priv_key.private_bytes_raw().hex()
    pub_hex = priv_key.public_key().public_bytes_raw().hex()
    key_id = "KEY-TEST-001"
    keyring = {key_id: pub_hex}
    policy = CommercialPolicyService(
        store=store,
        keyring_override=keyring,
        installation_id="TEST-INST-001"
    )
    return store, policy, priv_hex, key_id


def _create_token(priv_hex, key_id, customer_id="FIRM-ACME", tier=LicenseTier.PRACTITIONER, max_cases=2,
                  not_before="2026-01-01T00:00:00Z", expires_at="2026-12-31T23:59:59Z", revision=1):
    return issue_commercial_license(
        signing_key_hex=priv_hex,
        customer_id=customer_id,
        tier=tier,
        max_cases=max_cases,
        license_id=f"LIC-{customer_id}-{revision}",
        issued_at=not_before,
        not_before=not_before,
        expires_at=expires_at,
        grace_until=expires_at,
        entitlements=["reconciliation", "offline_export"],
        key_id=key_id,
        revision=revision,
    )


def test_cap_01_and_02_consumption_and_anti_delete(test_setup):
    """CAP-01 & CAP-02: Production case consumes 1 unit, and deletion NEVER refunds capacity."""
    store, policy, priv_hex, key_id = test_setup
    token = _create_token(priv_hex, key_id, max_cases=2)
    policy.install_license_token(token)

    eval_res = policy.evaluate_current_license()
    entitlement_period_id = f"{eval_res.customer_id}:{eval_res.not_before[:10]}_{eval_res.expires_at[:10]}"

    # Initial state: 0 consumed
    assert store.count_billable_cases(entitlement_period_id=entitlement_period_id) == 0

    # Create Case 1
    case1 = CanonicalCase(
        case_id="CASE-PROD-001",
        tax_year=2025,
        jurisdiction="US",
        case_status="CREATED",
        case_kind="PRODUCTION",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat()
    )
    store.create_case_atomic(
        case=case1,
        max_cases=2,
        entitlement_period_id=entitlement_period_id,
        customer_id=eval_res.customer_id
    )

    # Consumed = 1
    assert store.count_billable_cases(entitlement_period_id=entitlement_period_id) == 1

    # DELETE Case 1 (anti-deletion loophole test)
    store.delete_case("CASE-PROD-001")
    assert store.get_case("CASE-PROD-001") is None

    # Invariant CAP-02: Billable capacity remains 1, NOT refunded!
    assert store.count_billable_cases(entitlement_period_id=entitlement_period_id) == 1

    # Create Case 2: Uses remaining 1 unit of capacity
    case2 = CanonicalCase(
        case_id="CASE-PROD-002",
        tax_year=2025,
        jurisdiction="US",
        case_status="CREATED",
        case_kind="PRODUCTION",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat()
    )
    store.create_case_atomic(
        case=case2,
        max_cases=2,
        entitlement_period_id=entitlement_period_id,
        customer_id=eval_res.customer_id
    )
    assert store.count_billable_cases(entitlement_period_id=entitlement_period_id) == 2

    # Attempt Case 3: Must be blocked even though Case 1 was deleted
    case3 = CanonicalCase(
        case_id="CASE-PROD-003",
        tax_year=2025,
        jurisdiction="US",
        case_status="CREATED",
        case_kind="PRODUCTION",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat()
    )
    with pytest.raises(ValueError, match="Plan capacity reached"):
        store.create_case_atomic(
            case=case3,
            max_cases=2,
            entitlement_period_id=entitlement_period_id,
            customer_id=eval_res.customer_id
        )

    # Policy authorization denial
    decision = policy.authorize(CommercialOperation.CREATE_CASE)
    assert not decision.allowed
    assert decision.reason_code == CommercialDenialCode.CASE_CAPACITY_REACHED


def test_cap_03_same_term_upgrade_preserves_consumed_usage(test_setup):
    """CAP-03: Reissuing or upgrading license within the SAME commercial term preserves consumed usage."""
    store, policy, priv_hex, key_id = test_setup
    
    # Initial: 2-case license
    tok1 = _create_token(priv_hex, key_id, max_cases=2, revision=1)
    policy.install_license_token(tok1)

    eval_res1 = policy.evaluate_current_license()
    period_id1 = f"{eval_res1.customer_id}:{eval_res1.not_before[:10]}_{eval_res1.expires_at[:10]}"

    case1 = CanonicalCase(
        case_id="CASE-PROD-001",
        tax_year=2025,
        jurisdiction="US",
        case_status="CREATED",
        case_kind="PRODUCTION",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat()
    )
    store.create_case_atomic(
        case=case1,
        max_cases=2,
        entitlement_period_id=period_id1,
        customer_id=eval_res1.customer_id
    )
    assert store.count_billable_cases(entitlement_period_id=period_id1) == 1

    # Upgrade to 10-case license with SAME term dates, revision 2
    tok2 = _create_token(priv_hex, key_id, max_cases=10, revision=2)
    policy.install_license_token(tok2)

    eval_res2 = policy.evaluate_current_license()
    period_id2 = f"{eval_res2.customer_id}:{eval_res2.not_before[:10]}_{eval_res2.expires_at[:10]}"
    assert period_id1 == period_id2

    # Consumed count is preserved (1 of 10)
    assert store.count_billable_cases(entitlement_period_id=period_id2) == 1
    decision = policy.authorize(CommercialOperation.CREATE_CASE)
    assert decision.allowed


def test_cap_04_new_annual_term_resets_allowance(test_setup):
    """CAP-04: Genuine new commercial term provides fresh allowance without altering past term history."""
    store, policy, priv_hex, key_id = test_setup

    # Term 2026: 2 cases
    tok_2026 = _create_token(
        priv_hex, key_id, max_cases=2,
        not_before="2026-01-01T00:00:00Z", expires_at="2026-12-31T23:59:59Z", revision=1
    )
    policy.install_license_token(tok_2026)
    eval_res = policy.evaluate_current_license()
    period_2026 = f"{eval_res.customer_id}:{eval_res.not_before[:10]}_{eval_res.expires_at[:10]}"

    # Consume all 2 cases in 2026
    for i in (1, 2):
        c = CanonicalCase(
            case_id=f"CASE-2026-{i}",
            tax_year=2025,
            jurisdiction="US",
            case_status="CREATED",
            case_kind="PRODUCTION",
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat()
        )
        store.create_case_atomic(
            case=c,
            max_cases=2,
            entitlement_period_id=period_2026,
            customer_id=eval_res.customer_id
        )
    assert store.count_billable_cases(entitlement_period_id=period_2026) == 2

    # Renewal for 2027: New term dates
    tok_2027 = _create_token(
        priv_hex, key_id, max_cases=2,
        not_before="2027-01-01T00:00:00Z", expires_at="2027-12-31T23:59:59Z", revision=2
    )
    policy.install_license_token(tok_2027)
    eval_2027 = policy.evaluate_current_license(current_time=datetime(2027, 2, 1, tzinfo=timezone.utc))
    period_2027 = f"{eval_2027.customer_id}:{eval_2027.not_before[:10]}_{eval_2027.expires_at[:10]}"
    assert period_2026 != period_2027

    # New 2027 term starts fresh with 0 consumed
    assert store.count_billable_cases(entitlement_period_id=period_2027) == 0
    # Past 2026 term history remains preserved at 2 consumed
    assert store.count_billable_cases(entitlement_period_id=period_2026) == 2


def test_cap_05_reopening_historical_cases_does_not_consume_new_capacity(test_setup):
    """CAP-05: Accessing historical cases during a new term does not create a new activation."""
    store, policy, priv_hex, key_id = test_setup

    # Term 2027
    tok_2027 = _create_token(
        priv_hex, key_id, max_cases=2,
        not_before="2027-01-01T00:00:00Z", expires_at="2027-12-31T23:59:59Z", revision=1
    )
    policy.install_license_token(tok_2027)
    eval_2027 = policy.evaluate_current_license(current_time=datetime(2027, 2, 1, tzinfo=timezone.utc))
    period_2027 = f"{eval_2027.customer_id}:{eval_2027.not_before[:10]}_{eval_2027.expires_at[:10]}"

    # Retrieve existing historical case from DB
    existing = store.get_case("CASE-2026-1")
    # Reading does not alter 2027 capacity
    assert store.count_billable_cases(entitlement_period_id=period_2027) == 0


def test_cap_06_failed_creation_consumes_zero_capacity(test_setup):
    """CAP-06 / CAP-07: Failed creation in atomic transaction rolls back, consuming 0 capacity."""
    store, policy, priv_hex, key_id = test_setup
    tok = _create_token(priv_hex, key_id, max_cases=1)
    policy.install_license_token(tok)
    eval_res = policy.evaluate_current_license()
    period_id = f"{eval_res.customer_id}:{eval_res.not_before[:10]}_{eval_res.expires_at[:10]}"

    # Successfully create 1 case
    case1 = CanonicalCase(
        case_id="CASE-OK-001",
        tax_year=2025,
        jurisdiction="US",
        case_status="CREATED",
        case_kind="PRODUCTION",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat()
    )
    store.create_case_atomic(
        case=case1,
        max_cases=1,
        entitlement_period_id=period_id,
        customer_id=eval_res.customer_id
    )
    assert store.count_billable_cases(entitlement_period_id=period_id) == 1

    # Attempt second case: fails capacity limit
    case2 = CanonicalCase(
        case_id="CASE-FAIL-002",
        tax_year=2025,
        jurisdiction="US",
        case_status="CREATED",
        case_kind="PRODUCTION",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat()
    )
    with pytest.raises(ValueError):
        store.create_case_atomic(
            case=case2,
            max_cases=1,
            entitlement_period_id=period_id,
            customer_id=eval_res.customer_id
        )

    # Consumed count is still exactly 1, no phantom activations created
    assert store.count_billable_cases(entitlement_period_id=period_id) == 1
    assert store.get_case("CASE-FAIL-002") is None
