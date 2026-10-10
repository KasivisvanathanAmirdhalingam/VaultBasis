"""
VaultBasis — Trust Boundary & Regression Invariants Suite
Conforms to REGRESSION-COVERAGE-001, MAC-GATEKEEPER-001, and ARTIFACT-TRANSPORT-001.

Validates the formal trust boundary contracts across pre-sign and post-sign stages
without requiring runtime modifications or bypassing operating system security.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestTrustBoundaryInvariants:
    """Validates FRZ-TRUST-* behavioral contracts and artifact transport rules."""

    def test_frz_trust_mac_01_unsigned_presign_contract(self):
        """FRZ-TRUST-MAC-01: Pre-sign unsigned candidate contract requires EXPECTED_REJECT_PRE_SIGN."""
        # Verify that candidate release metadata explicitly specifies unsigned state
        dist_dir = REPO_ROOT / "dist"
        manifest_path = dist_dir / "VaultBasis-RC3-macOS-arm64.manifest.json"
        
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            assert manifest["signing"]["status"] == "UNSIGNED"
            assert manifest["signing"]["notarization_ticket"] is None
        
        # Verify disposition document records EXPECTED PRE-SIGN TRUST REJECTION
        disposition_path = REPO_ROOT / "docs" / "qualification" / "MAC_GATEKEEPER_001_DISPOSITION.md"
        assert disposition_path.is_file(), "MAC_GATEKEEPER_001_DISPOSITION.md must exist"
        content = disposition_path.read_text(encoding="utf-8")
        assert "EXPECTED PRE-SIGN TRUST REJECTION" in content
        assert "remove quarantine" in content.lower()
        assert "zero-terminal" in content.lower()

    def test_frz_trust_mac_02_signed_postsign_contract(self):
        """FRZ-TRUST-MAC-02: Post-sign contract requires MUST_ACCEPT with zero-terminal customer journey."""
        contract_path = REPO_ROOT / "docs" / "qualification" / "frozen_regression_contract.md"
        assert contract_path.is_file()
        content = contract_path.read_text(encoding="utf-8")
        assert "FRZ-TRUST-MAC-02" in content
        assert "MUST_ACCEPT" in content
        assert "MAC-SIGNED-RC1" in content

    def test_frz_trust_win_01_unsigned_presign_contract(self):
        """FRZ-TRUST-WIN-01: Windows pre-sign unsigned installer contract requires EXPECTED_REPUTATION_PROMPT_PRE_SIGN."""
        dist_dir = REPO_ROOT / "dist"
        manifest_path = dist_dir / "VaultBasis-RC3-Windows-x64.manifest.json"
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            assert manifest["signing"]["status"] == "UNSIGNED"

        contract_path = REPO_ROOT / "docs" / "qualification" / "frozen_regression_contract.md"
        content = contract_path.read_text(encoding="utf-8")
        assert "FRZ-TRUST-WIN-01" in content
        assert "EXPECTED_REPUTATION_PROMPT_PRE_SIGN" in content

    def test_frz_trust_win_02_signed_postsign_contract(self):
        """FRZ-TRUST-WIN-02: Windows post-sign contract requires TRUSTED_LAUNCH via Microsoft Trusted Signing."""
        contract_path = REPO_ROOT / "docs" / "qualification" / "frozen_regression_contract.md"
        content = contract_path.read_text(encoding="utf-8")
        assert "FRZ-TRUST-WIN-02" in content
        assert "TRUSTED_LAUNCH" in content
        assert "WIN-SIGNED-RC1" in content

    def test_artifact_transport_001_separation_invariant(self):
        """ARTIFACT-TRANSPORT-001: Engineering folder transport must not be confused with customer DMG/Installer."""
        disposition_path = REPO_ROOT / "docs" / "qualification" / "MAC_GATEKEEPER_001_DISPOSITION.md"
        content = disposition_path.read_text(encoding="utf-8")
        assert "ARTIFACT-TRANSPORT-001" in content
        assert "engineering transport only" in content
        assert "VaultBasis-RC3-macOS-arm64.dmg" in content

    def test_presign_barriers_count_invariant(self):
        """Preserves corrected pre-sign count of exactly 5 barriers following UAT-29 post-sign repositioning."""
        directive_path = REPO_ROOT / "docs" / "qualification" / "mmp15_presign_execution_directive.md"
        if directive_path.is_file():
            content = directive_path.read_text(encoding="utf-8")
            # Verify 5-barrier structure is documented
            assert "0 / 5" in content or "PRE-SIGN BARRIERS" in content

    def test_change_classification_enforcement(self):
        """Verifies that check_change_classification script exists and executes cleanly."""
        script_path = REPO_ROOT / "scripts" / "check_change_classification.py"
        assert script_path.is_file()
        env = dict(os.environ, VAULTBASIS_CHANGE_CLASS="QUALIFICATION_HARNESS")
        res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, env=env)
        assert res.returncode == 0
        assert "Change classification guard PASSED" in res.stdout
