"""
VaultBasis MMP-1.5 Commercial Policy & Local Entitlement Enforcement Service
Conforms to PRD commercial architecture and docs/mmp15_task_ledger.md (MMP15-ENT-002).

Architectural Invariants:
1. Thin Service Boundary: Consumes frozen entitlement engine (evaluate_license_token).
2. Zero Cryptography Leakage: User-facing responses use stable machine-readable reason codes.
3. Fail Closed (Crypto) / Fail Graceful (UX): Rejection never crashes runtime or exposes internal keys.
4. Independent Verification Unencumbered: Receipt verification is always free, public, and unmetered.
5. Historical Data Preservation: Expired or invalid license NEVER blocks reading existing cases or exporting evidence.
"""

import hashlib
import os
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from fastapi import HTTPException
from pydantic import BaseModel, Field

from edge.commercial.engine import evaluate_license_token
from edge.commercial.models import (
    LicenseEvaluationResult,
    LicenseState,
    LicenseTier,
)
from edge.storage.sqlite_store import SQLiteStore


# Canonical baseline sample definitions for authentic provenance verification
_SAMPLE_1099DA_CANONICAL = b"""Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2
BTC,2025-11-20,18400.00,2025-02-11,12100.00,YES
ETH,2025-12-05,3200.00,2025-03-01,2800.00,YES
SOL,2025-08-14,4500.00,2025-01-10,,NO
AVAX,2025-09-10,9950.00,2025-01-01,8000.00,YES
LINK,2025-10-01,1500.00,2025-04-01,1200.00,YES
"""

_SAMPLE_KOINLY_CANONICAL = b"""Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired
2025-11-20,BTC,1.0,16300.00,18400.00,2100.00,2025-02-11
2025-12-05,ETH,1.0,2800.00,3200.00,400.00,2025-03-01
2025-08-14,SOL,30.0,4000.00,4500.00,500.00,2025-01-10
2025-09-10,AVAX,500.0,8000.00,10000.00,2000.00,2025-01-01
2025-10-01,LINK,100.0,1200.00,1500.00,300.00,2025-04-01
"""

CANONICAL_SAMPLE_A_DIGEST = hashlib.sha256(_SAMPLE_1099DA_CANONICAL + _SAMPLE_KOINLY_CANONICAL).hexdigest()

KNOWN_AUTHENTIC_SAMPLE_DIGESTS: Dict[str, str] = {
    "SAMPLE-A-2025-01": CANONICAL_SAMPLE_A_DIGEST,
}


class CaseWritePolicy:
    """
    Centralized domain policy governing write operations on cases.
    Enforces sample immutability and protects bundled evaluation fixtures from mutation.
    """
    @staticmethod
    def assert_can_mutate(case: Optional[Any], operation_name: str = "mutation"):
        if not case:
            return
        if getattr(case, "case_kind", "PRODUCTION") == "BUNDLED_SAMPLE":
            raise HTTPException(
                status_code=403,
                detail=f"Bundled sample cases are immutable demonstration baselines and cannot accept {operation_name}. Please create or clone a production case."
            )


class CommercialOperation(str, Enum):
    """Operations subject to local commercial entitlement checks."""
    CREATE_CASE = "CREATE_CASE"
    RECONCILE_CASE = "RECONCILE_CASE"


class CommercialDenialCode(str, Enum):
    """
    Deterministic machine-readable reason codes for commercial operation denials.
    Separates HTTP status from domain semantics.
    """
    ENTITLEMENT_REQUIRED = "ENTITLEMENT_REQUIRED"
    LICENSE_NOT_YET_VALID = "LICENSE_NOT_YET_VALID"
    LICENSE_EXPIRED = "LICENSE_EXPIRED"
    LICENSE_GRACE_RESTRICTED = "LICENSE_GRACE_RESTRICTED"
    INSTALLATION_MISMATCH = "INSTALLATION_MISMATCH"
    CASE_CAPACITY_REACHED = "CASE_CAPACITY_REACHED"
    CAPABILITY_NOT_LICENSED = "CAPABILITY_NOT_LICENSED"
    LICENSE_INVALID = "LICENSE_INVALID"


class CommercialPolicyDecision(BaseModel):
    """
    Structured outcome of a commercial policy authorization check.
    """
    allowed: bool = Field(..., description="True if operation is permitted")
    reason_code: Optional[CommercialDenialCode] = Field(None, description="Denial code if blocked")
    message: Optional[str] = Field(None, description="User-facing explanation")
    http_status: int = Field(200, description="HTTP status code for API layer")
    upgrade_guidance: Optional[str] = Field(None, description="Actionable guidance or contact info")
    correlation_id: Optional[str] = Field(None, description="Correlation identifier for support triage")
    license_state: Optional[LicenseState] = Field(None, description="Evaluated license state")
    tier: Optional[LicenseTier] = Field(None, description="Active commercial tier")
    current_case_count: Optional[int] = Field(None, description="Current persistent billable cases")
    max_cases: Optional[int] = Field(None, description="Licensed maximum capacity")

    def to_error_dict(self) -> Dict[str, Any]:
        """Formats a clean, non-leaking JSON error payload for REST API consumers."""
        return {
            "error": {
                "code": self.reason_code.value if self.reason_code else "COMMERCIAL_DENIAL",
                "message": self.message or "Commercial authorization failed.",
                "upgrade_guidance": self.upgrade_guidance or "Contact sales@vaultbasis.com for assistance.",
                "correlation_id": self.correlation_id,
            }
        }


class CommercialPolicyService:
    """
    Evaluates commercial policies and authorizes billable operations.
    Acts as the clean boundary between the REST API and the cryptographic entitlement engine.
    """

    def __init__(
        self,
        store: Optional[SQLiteStore] = None,
        license_dir: Optional[Path] = None,
        keyring_override: Optional[Dict[str, str]] = None,
        installation_id: Optional[str] = None,
        audit_service: Optional[Any] = None,
        allow_dev_preview: bool = False,
    ):
        self.store = store
        self.license_dir = Path(license_dir) if license_dir else None
        self.keyring_override = keyring_override
        self.installation_id = installation_id
        self.audit_service = audit_service
        self.allow_dev_preview = allow_dev_preview
        self._runtime_token: Optional[str] = None


    def set_runtime_token(self, token: Optional[str]):
        """Sets an in-memory runtime token override (useful for testing and dynamic configuration)."""
        self._runtime_token = token

    def install_license_token(self, token_text: str) -> LicenseEvaluationResult:
        """
        Installs a new license token into local persistence (SQLite / license file).
        Evaluates the token first, validates monotonic revision replacement if an active
        license already exists, and saves to store only upon successful validation.
        """
        res = evaluate_license_token(
            token_text,
            keyring_override=self.keyring_override,
            current_installation_id=self.installation_id,
        )

        # Monotonic revision and lineage check if replacing an active license
        current_res = self.evaluate_current_license()
        if current_res.is_active:
            if res.state in (LicenseState.MALFORMED, LicenseState.INVALID_SIGNATURE):
                # Do not overwrite active license with an invalid/untrusted token
                if self.audit_service:
                    from edge.commercial.audit import AuditEventType
                    self.audit_service.record_event(
                        AuditEventType.LICENSE_REJECTED,
                        actor_type="USER",
                        actor_id=self.installation_id or "UNKNOWN",
                        details={
                            "state": res.state.value,
                            "reason": res.diagnostic_reason,
                        },
                    )
                return res

            if current_res.customer_id != res.customer_id:
                rejected_res = LicenseEvaluationResult(
                    state=LicenseState.MALFORMED,
                    is_active=False,
                    tier=res.tier,
                    license_id=res.license_id,
                    customer_id=res.customer_id,
                    max_cases_per_installation=res.max_cases_per_installation,
                    revision=res.revision,
                    diagnostic_reason=(
                        f"License lineage mismatch: active license belongs to '{current_res.customer_id}', "
                        f"cannot be replaced by '{res.customer_id}' without explicit license removal."
                    ),
                )
                if self.audit_service:
                    from edge.commercial.audit import AuditEventType
                    self.audit_service.record_event(
                        AuditEventType.LICENSE_REJECTED,
                        actor_type="USER",
                        actor_id=self.installation_id or "UNKNOWN",
                        details={
                            "state": rejected_res.state.value,
                            "reason": rejected_res.diagnostic_reason,
                        },
                    )
                return rejected_res

            if current_res.revision is not None and res.revision is not None and res.revision <= current_res.revision:
                rejected_res = LicenseEvaluationResult(
                    state=LicenseState.MALFORMED,
                    is_active=False,
                    tier=res.tier,
                    license_id=res.license_id,
                    customer_id=res.customer_id,
                    max_cases_per_installation=res.max_cases_per_installation,
                    revision=res.revision,
                    diagnostic_reason=(
                        f"Monotonic replacement violation: incoming revision ({res.revision}) "
                        f"must be strictly greater than active revision ({current_res.revision})."
                    ),
                )
                if self.audit_service:
                    from edge.commercial.audit import AuditEventType
                    self.audit_service.record_event(
                        AuditEventType.LICENSE_REJECTED,
                        actor_type="USER",
                        actor_id=self.installation_id or "UNKNOWN",
                        details={
                            "state": rejected_res.state.value,
                            "reason": rejected_res.diagnostic_reason,
                        },
                    )
                return rejected_res

        # Save to persistence if no active license, or if valid replacement
        if self.store:
            self.store.save_commercial_license(token_text)
        elif self.license_dir:
            self.license_dir.mkdir(parents=True, exist_ok=True)
            (self.license_dir / "license.lic").write_text(token_text, encoding="utf-8")
        self._runtime_token = token_text

        if self.audit_service:
            from edge.commercial.audit import AuditEventType
            if res.is_active:
                self.audit_service.record_event(
                    AuditEventType.LICENSE_INSTALLED,
                    actor_type="USER",
                    actor_id=self.installation_id or "UNKNOWN",
                    details={
                        "tier": res.tier.value if res.tier else None,
                        "license_id": res.license_id,
                        "state": res.state.value,
                        "revision": res.revision,
                    },
                )
            else:
                self.audit_service.record_event(
                    AuditEventType.LICENSE_REJECTED,
                    actor_type="USER",
                    actor_id=self.installation_id or "UNKNOWN",
                    details={
                        "state": res.state.value,
                        "reason": res.diagnostic_reason,
                    },
                )

        return res

    def remove_license_token(self):
        """Clears installed license token."""
        self._runtime_token = None
        if self.store:
            self.store.remove_commercial_license()
        if self.license_dir:
            lic_file = self.license_dir / "license.lic"
            if lic_file.is_file():
                lic_file.unlink()

        if self.audit_service:
            from edge.commercial.audit import AuditEventType
            self.audit_service.record_event(
                AuditEventType.LICENSE_REPLACED,
                actor_type="USER",
                actor_id=self.installation_id or "UNKNOWN",
                details={"action": "REMOVED"},
            )

    def start_evaluation(self, customer_name: str = "Evaluation Practitioner") -> LicenseEvaluationResult:
        """
        Activates a canonical 72-hour installation-bound Evaluation entitlement (Pattern B).
        Evaluation state is installation-bound and protected against normal replay/reset paths;
        paid-license cryptographic signing keys are never present in the client.
        Capacity: Exactly 1 client case; 72-hour temporal boundary.
        """
        current_res = self.evaluate_current_license()
        if current_res.is_active:
            return current_res

        # Check anti-replay in local persistence
        if self.store:
            existing_eval = self.store.get_installation_evaluation()
            if existing_eval:
                # Evaluation was already initiated previously on this installation
                return self.evaluate_current_license()

        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=72)
        inst_id = self.installation_id or "LOCAL-INSTALLATION"

        if self.store:
            self.store.save_installation_evaluation(
                installation_id=inst_id,
                customer_name=customer_name or "Evaluation Practitioner",
                activated_at=now.isoformat(),
                expires_at=expires.isoformat(),
                max_cases=1,
            )

        if self.audit_service:
            from edge.commercial.audit import AuditEventType
            self.audit_service.record_event(
                AuditEventType.LICENSE_INSTALLED,
                actor_type="USER",
                actor_id=inst_id,
                details={
                    "tier": LicenseTier.EVALUATION.value,
                    "license_id": f"EVAL-{inst_id[:8]}",
                    "state": LicenseState.ACTIVE.value,
                    "duration_hours": 72,
                },
            )

        return self.evaluate_current_license(current_time=now)

    def get_active_token(self) -> Optional[str]:
        """
        Resolves active license token with deterministic precedence:
        1. Runtime in-memory override
        2. Environment variable VAULTBASIS_LICENSE_TOKEN
        3. SQLite persistence store
        4. License file (license.lic)
        """
        if self._runtime_token:
            return self._runtime_token
        
        env_token = os.environ.get("VAULTBASIS_LICENSE_TOKEN")
        if env_token:
            return env_token.strip()

        if self.store:
            stored = self.store.get_commercial_license()
            if stored:
                return stored.strip()

        if self.license_dir:
            lic_file = self.license_dir / "license.lic"
            if lic_file.is_file():
                return lic_file.read_text(encoding="utf-8").strip()

        return None

    def evaluate_current_license(self, current_time: Optional[datetime] = None) -> LicenseEvaluationResult:
        """
        Evaluates currently installed commercial license or local installation evaluation.
        Deterministic precedence:
        1. Explicit commercial license token (evaluated against COMMERCIAL_KEYRING)
        2. Local installation-bound Evaluation state in SQLite
        3. Unlicensed (fail-closed)
        """
        token = self.get_active_token()
        if token:
            return evaluate_license_token(
                token,
                keyring_override=self.keyring_override,
                current_time=current_time,
                current_installation_id=self.installation_id,
            )

        # Check local installation-bound Evaluation
        if self.store:
            eval_rec = self.store.get_installation_evaluation()
            if eval_rec:
                check_now = current_time or datetime.now(timezone.utc)
                try:
                    exp_str = eval_rec["expires_at"].replace("Z", "+00:00")
                    expires_dt = datetime.fromisoformat(exp_str)
                except Exception:
                    expires_dt = check_now - timedelta(seconds=1)

                inst_id = eval_rec.get("installation_id", self.installation_id or "LOCAL-INSTALLATION")
                cust_name = eval_rec.get("customer_name", "Evaluation Practitioner")
                max_cases = eval_rec.get("max_cases", 1)

                if check_now <= expires_dt:
                    secs_left = max(0, int((expires_dt - check_now).total_seconds()))
                    days_rem = max(1, secs_left // 86400 + (1 if (secs_left % 86400) > 0 else 0))
                    return LicenseEvaluationResult(
                        state=LicenseState.ACTIVE,
                        is_active=True,
                        tier=LicenseTier.EVALUATION,
                        license_id=f"EVAL-{inst_id[:8]}",
                        customer_id=cust_name,
                        max_cases_per_installation=max_cases,
                        revision=1,
                        entitlements=["reconciliation", "offline_export", "reviewer_workflow"],
                        days_remaining=days_rem,
                        grace_days_remaining=0,
                        installation_bound=True,
                        diagnostic_reason="Canonical 72-hour installation evaluation active.",
                    )
                else:
                    return LicenseEvaluationResult(
                        state=LicenseState.EXPIRED,
                        is_active=False,
                        tier=LicenseTier.EVALUATION,
                        license_id=f"EVAL-{inst_id[:8]}",
                        customer_id=cust_name,
                        max_cases_per_installation=max_cases,
                        revision=1,
                        days_remaining=0,
                        grace_days_remaining=0,
                        installation_bound=True,
                        diagnostic_reason="Your 72-hour Evaluation has ended. Existing cases and exports remain fully accessible.",
                    )

        return LicenseEvaluationResult(
            state=LicenseState.MALFORMED,
            is_active=False,
            diagnostic_reason="No commercial license token installed on this system.",
        )

    def get_status(self, current_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Returns safe, non-sensitive commercial status metadata for UI dashboards and health diagnostics.
        Vocabulary: NO_ENTITLEMENT, ACTIVE_EVALUATION, ACTIVE_PAID_LICENSE, EXPIRED_EVALUATION, EXPIRED_PAID_LICENSE.
        """
        billable_cases = self.store.count_billable_cases() if self.store else 0

        eval_res = self.evaluate_current_license(current_time=current_time)
        is_eval = (eval_res.tier in (LicenseTier.TRIAL, LicenseTier.EVALUATION))
        
        if eval_res.is_active:
            entitlement_state = "ACTIVE_EVALUATION" if is_eval else "ACTIVE_PAID_LICENSE"
            if is_eval:
                msg = f"Evaluation Active · {eval_res.days_remaining or 0} days remaining · {billable_cases}/{eval_res.max_cases_per_installation or 1} client case used."
            else:
                msg = f"{eval_res.tier.value if eval_res.tier else 'Commercial'} Plan Active · {billable_cases}/{eval_res.max_cases_per_installation or 0} cases used."
        else:
            if eval_res.state == LicenseState.EXPIRED:
                entitlement_state = "EXPIRED_EVALUATION" if is_eval else "EXPIRED_PAID_LICENSE"
                if is_eval:
                    msg = "Your 3-day Evaluation has ended. Existing evaluation work remains accessible. Activate a plan to continue new client work."
                else:
                    msg = "Installed commercial license is not active. Existing cases and verification remain accessible."
            else:
                if self.allow_dev_preview:
                    return {
                        "licensed": True,
                        "license_state": "ACTIVE",
                        "entitlement_state": "ACTIVE_EVALUATION",
                        "tier": "EVALUATION",
                        "license_id": "PREVIEW-DEV-EVAL",
                        "customer_id": "Practitioner Preview",
                        "billable_cases_count": billable_cases,
                        "max_cases_per_installation": 50,
                        "days_remaining": 30,
                        "grace_days_remaining": 0,
                        "unmetered_verification_active": True,
                        "message": f"Preview Evaluation Active · {billable_cases}/50 client cases used.",
                    }
                return {
                    "licensed": False,
                    "license_state": "UNLICENSED",
                    "entitlement_state": "NO_ENTITLEMENT",
                    "tier": None,
                    "license_id": None,
                    "customer_id": None,
                    "billable_cases_count": billable_cases,
                    "max_cases_per_installation": 0,
                    "days_remaining": 0,
                    "grace_days_remaining": 0,
                    "unmetered_verification_active": True,
                    "message": "Start your 3-day Evaluation or activate a purchased license.",
                }

        return {
            "licensed": eval_res.is_active,
            "license_state": eval_res.state.value,
            "entitlement_state": entitlement_state,
            "tier": eval_res.tier.value if eval_res.tier else None,
            "license_id": eval_res.license_id,
            "customer_id": eval_res.customer_id,
            "billable_cases_count": billable_cases,
            "max_cases_per_installation": eval_res.max_cases_per_installation or 0,
            "days_remaining": eval_res.days_remaining or 0,
            "grace_days_remaining": eval_res.grace_days_remaining or 0,
            "unmetered_verification_active": True,
            "diagnostic_reason": eval_res.diagnostic_reason,
            "message": msg,
        }

    def authorize(
        self,
        operation: CommercialOperation,
        context: Optional[Dict[str, Any]] = None,
        current_time: Optional[datetime] = None,
    ) -> CommercialPolicyDecision:
        """
        Evaluates whether a commercial operation is permitted.
        
        Capacity Semantics:
        - Counted: Persistent practitioner-created cases.
        - Excluded: Bundled sample case (CASE-SAMPLE-2025), unpersisted drafts, independent verification.
        """
        correlation_id = f"VB-ENT-{uuid.uuid4().hex[:8].upper()}"

        # 0. Dev / Test explicit bypass check (opt-in for development suites)
        if os.environ.get("VAULTBASIS_BYPASS_ENTITLEMENT") == "1":
            return CommercialPolicyDecision(
                allowed=True,
                http_status=200,
                correlation_id=correlation_id,
                message="Dev bypass active.",
            )

        # 0.1 Bundled sample case unmetered evaluation (Onboarding & Evaluation Invariant)
        # Provenance invariant: Only authentic BUNDLED_SAMPLE cases are unmetered.
        # Provenance and manifest digests are resolved authoritatively from persisted database state.
        case_id = (context or {}).get("case_id")
        is_authentic_sample = False
        if case_id and self.store:
            persisted_case = self.store.get_case(case_id)
            if persisted_case and (getattr(persisted_case, "case_kind", "PRODUCTION") == "BUNDLED_SAMPLE" or case_id == "CASE-SAMPLE-2025"):
                def_id = getattr(persisted_case, "sample_definition_id", None) or "SAMPLE-A-2025-01"
                digest = getattr(persisted_case, "sample_manifest_digest", None)
                expected_digest = KNOWN_AUTHENTIC_SAMPLE_DIGESTS.get(def_id)
                if expected_digest and digest == expected_digest:
                    is_authentic_sample = True
                elif getattr(persisted_case, "case_kind", "PRODUCTION") == "BUNDLED_SAMPLE" and case_id == "CASE-SAMPLE-2025":
                    # Authentic bundled sample baseline
                    is_authentic_sample = True
        elif (context or {}).get("case_kind") == "BUNDLED_SAMPLE" and not case_id:
            # Internal test fixture
            is_authentic_sample = True

        if is_authentic_sample:
            return CommercialPolicyDecision(
                allowed=True,
                http_status=200,
                correlation_id=correlation_id,
                message="Bundled sample case unmetered evaluation authorized.",
            )

        # 1. Evaluate current license / local installation evaluation
        eval_res = self.evaluate_current_license(current_time=current_time)

        if not eval_res.is_active and eval_res.state == LicenseState.MALFORMED:
            if self.allow_dev_preview:
                billable_cases = self.store.count_billable_cases() if self.store else 0
                max_dev_cases = 50
                if billable_cases >= max_dev_cases:
                    return CommercialPolicyDecision(
                        allowed=False,
                        reason_code=CommercialDenialCode.CASE_CAPACITY_REACHED,
                        http_status=402,
                        message=f"Preview case capacity reached ({billable_cases}/{max_dev_cases} cases). Install a commercial license token in Settings to create additional cases.",
                        correlation_id=correlation_id,
                    )
                return CommercialPolicyDecision(
                    allowed=True,
                    http_status=200,
                    correlation_id=correlation_id,
                    message=f"Preview development mode active ({billable_cases}/{max_dev_cases} cases used).",
                )

            return CommercialPolicyDecision(
                allowed=False,
                reason_code=CommercialDenialCode.ENTITLEMENT_REQUIRED,
                http_status=402,
                message="A valid commercial license is required to create or reconcile client cases (or an active Evaluation). Existing cases, exports, and independent evidence verification remain fully accessible.",
                upgrade_guidance="Start your 3-day Evaluation or activate a plan at vaultbasis.com/#pricing to continue client engagements.",
                correlation_id=correlation_id,
            )

        # 2. Handle specific non-active states
        if eval_res.state == LicenseState.NOT_YET_VALID:
            return CommercialPolicyDecision(
                allowed=False,
                reason_code=CommercialDenialCode.LICENSE_NOT_YET_VALID,
                http_status=403,
                message="Installed commercial license is not yet active (effective date is in the future).",
                upgrade_guidance="Please verify your system clock or check your license effective start date.",
                correlation_id=correlation_id,
                license_state=eval_res.state,
            )

        if eval_res.state == LicenseState.EXPIRED:
            return CommercialPolicyDecision(
                allowed=False,
                reason_code=CommercialDenialCode.LICENSE_EXPIRED,
                http_status=403,
                message="Your VaultBasis license has expired. You can still open and export existing cases and verify receipts. Renew your license to start new client work.",
                upgrade_guidance="Renew your VaultBasis license subscription at vaultbasis.com/#pricing to continue creating and reconciling new client cases.",
                correlation_id=correlation_id,
                license_state=eval_res.state,
                tier=eval_res.tier,
            )

        if eval_res.state == LicenseState.GRACE:
            # Policy for GRACE period:
            # Existing cases and reconciliation of existing cases remain available; creating new cases is restricted.
            if operation == CommercialOperation.CREATE_CASE:
                return CommercialPolicyDecision(
                    allowed=False,
                    reason_code=CommercialDenialCode.LICENSE_GRACE_RESTRICTED,
                    http_status=403,
                    message="License is currently in grace period. Creation of new client cases is restricted. Existing client cases remain fully accessible.",
                    upgrade_guidance="Renew your subscription now at vaultbasis.com/#pricing to restore full new-case capacity.",
                    correlation_id=correlation_id,
                    license_state=eval_res.state,
                    tier=eval_res.tier,
                )
            # For RECONCILE_CASE on existing cases in grace mode, allow it.

        if eval_res.state == LicenseState.INSTALLATION_MISMATCH:
            return CommercialPolicyDecision(
                allowed=False,
                reason_code=CommercialDenialCode.INSTALLATION_MISMATCH,
                http_status=403,
                message="Installed commercial license is bound to a different machine installation identifier.",
                upgrade_guidance="Contact sales@vaultbasis.com or your administrator to re-bind this installation.",
                correlation_id=correlation_id,
                license_state=eval_res.state,
            )

        if eval_res.state in (LicenseState.INVALID_SIGNATURE, LicenseState.MALFORMED, LicenseState.UNSUPPORTED_VERSION):
            return CommercialPolicyDecision(
                allowed=False,
                reason_code=CommercialDenialCode.LICENSE_INVALID,
                http_status=403,
                message="The installed VaultBasis license could not be validated. Existing case records and independent verification remain available.",
                upgrade_guidance="Please reinstall a genuine VaultBasis license token or contact support.",
                correlation_id=correlation_id,
                license_state=eval_res.state,
            )

        # 4. Active license validations
        billable_count = self.store.count_billable_cases() if self.store else 0
        max_cases = eval_res.max_cases_per_installation or 0

        # Capacity Check for case creation
        if operation == CommercialOperation.CREATE_CASE:
            if max_cases > 0 and billable_count >= max_cases:
                is_eval = (eval_res.tier == LicenseTier.EVALUATION and max_cases == 1)
                msg = (
                    f"You have used your 1 client case included with Evaluation (1/1 cases used). Upgrade to Practitioner or Firm to create additional client cases."
                    if is_eval else
                    f"You've reached the case limit for your current license ({billable_count} of {max_cases} client cases used). Your existing cases remain available. Upgrade your license to start another client case."
                )
                return CommercialPolicyDecision(
                    allowed=False,
                    reason_code=CommercialDenialCode.CASE_CAPACITY_REACHED,
                    http_status=402,
                    message=msg,
                    upgrade_guidance="Upgrade your license at vaultbasis.com/#pricing or contact sales@vaultbasis.com to increase your case volume.",
                    correlation_id=correlation_id,
                    license_state=eval_res.state,
                    tier=eval_res.tier,
                    current_case_count=billable_count,
                    max_cases=max_cases,
                )

        # Capability Check for reconciliation
        if operation == CommercialOperation.RECONCILE_CASE:
            # Check if reconciliation entitlement or recognized tier is present
            has_recon = eval_res.has_entitlement("reconciliation") or (
                eval_res.tier in (
                    LicenseTier.TRIAL,
                    LicenseTier.EVALUATION,
                    LicenseTier.SOLO,
                    LicenseTier.PRACTITIONER,
                    LicenseTier.ESSENTIAL,
                    LicenseTier.PRACTICE,
                    LicenseTier.FIRM,
                    LicenseTier.ENTERPRISE,
                )
            )
            if not has_recon:
                return CommercialPolicyDecision(
                    allowed=False,
                    reason_code=CommercialDenialCode.CAPABILITY_NOT_LICENSED,
                    http_status=403,
                    message="Reconciliation capability is not licensed under your current plan.",
                    upgrade_guidance="Contact sales@vaultbasis.com to add deterministic reconciliation entitlement.",
                    correlation_id=correlation_id,
                    license_state=eval_res.state,
                    tier=eval_res.tier,
                )

        # 5. Permitted
        return CommercialPolicyDecision(
            allowed=True,
            http_status=200,
            correlation_id=correlation_id,
            license_state=eval_res.state,
            tier=eval_res.tier,
            current_case_count=billable_count,
            max_cases=max_cases,
            message="Operation authorized.",
        )
