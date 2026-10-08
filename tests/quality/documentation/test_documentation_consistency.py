"""
VaultBasis Quality Engineering — Automated Documentation Consistency & Governance Tests
Ensures zero documentation drift across normative specifications, indices, gate definitions,
traceability matrices, commercial policy configurations, and customer-facing trust claims.
"""

import json
import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class TestDocumentationConsistency:

    def test_documentation_index_links_exist(self):
        """All files referenced in docs/DOCUMENTATION_INDEX.md must exist on disk."""
        index_file = REPO_ROOT / "docs" / "DOCUMENTATION_INDEX.md"
        assert index_file.exists(), "docs/DOCUMENTATION_INDEX.md is missing"
        content = index_file.read_text(encoding="utf-8")

        # Extract markdown file links: [`path`](path)
        file_links = re.findall(r"\[`([^`]+)`\]\([^)]+\)", content)
        assert len(file_links) >= 10, "Documentation index should link to key documents"

        for link in file_links:
            target = REPO_ROOT / link
            assert target.exists(), f"Indexed document does not exist on disk: {link}"

    def test_canonical_prod_gates_definition_completeness(self):
        """canonical_prod_gates.md must define all 18 gates PROD-GATE-01 through PROD-GATE-18."""
        gates_file = REPO_ROOT / "docs" / "qualification" / "canonical_prod_gates.md"
        assert gates_file.exists(), "docs/qualification/canonical_prod_gates.md is missing"
        content = gates_file.read_text(encoding="utf-8")

        for i in range(1, 19):
            gate_id = f"PROD-GATE-{i:02d}"
            assert gate_id in content, f"Missing definition for canonical gate: {gate_id}"

    def test_traceability_matrix_and_test_suite_gate_alignment(self):
        """Traceability matrix and test suite must use identical canonical PROD-GATE names."""
        matrix_file = REPO_ROOT / "docs" / "qualification" / "mmp15_traceability_matrix.md"
        test_file = REPO_ROOT / "tests" / "security" / "test_artifact_qualification_suite.py"

        assert matrix_file.exists()
        assert test_file.exists()

        matrix_content = matrix_file.read_text(encoding="utf-8")
        test_content = test_file.read_text(encoding="utf-8")

        for i in range(1, 19):
            gate_id = f"PROD-GATE-{i:02d}"
            assert gate_id in matrix_content, f"Matrix missing gate: {gate_id}"
            assert gate_id in test_content, f"Test suite missing gate: {gate_id}"

    def test_pricing_parity_across_docs_and_commercial_policy(self):
        """Pricing tiers ($0, $499, $1,499) must match between docs and canonical catalog."""
        catalog_path = REPO_ROOT / "schemas" / "commercial" / "canonical_catalog.json"
        assert catalog_path.exists()
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

        pricing_doc = REPO_ROOT / "docs" / "commercial" / "pricing_and_capacity_v1.md"
        assert pricing_doc.exists()
        doc_text = pricing_doc.read_text(encoding="utf-8")

        # Verify key prices appear in pricing documentation
        assert "$499" in doc_text
        assert "$1,499" in doc_text or "$1499" in doc_text

        # Verify catalog definitions
        assert catalog["tiers"]["PRACTITIONER"]["priceAmountCents"] == 49900
        assert catalog["tiers"]["FIRM"]["priceAmountCents"] == 149900
        assert catalog["tiers"]["EVALUATION"]["caseCapacity"] == 3

    def test_current_candidate_sha_consistency(self):
        """Current candidate macOS SHA must be 1ce6fba1... and old hash marked SUPERSEDED."""
        matrix_file = REPO_ROOT / "docs" / "qualification" / "mmp15_traceability_matrix.md"
        content = matrix_file.read_text(encoding="utf-8")

        assert "1ce6fba1193ebbef60d0834b4dad1f83781129dfda2c91b6d7339138155b9204" in content
        assert "CURRENT_PRE_SIGN_CANDIDATE" in content
        assert "SUPERSEDED" in content

    def test_known_limitations_document_completeness(self):
        """docs/KNOWN_LIMITATIONS.md must define the canonical scope boundaries."""
        limits_file = REPO_ROOT / "docs" / "KNOWN_LIMITATIONS.md"
        assert limits_file.exists()
        content = limits_file.read_text(encoding="utf-8")

        # Must explicitly declare key limitations
        assert "Tax Year 2025" in content
        assert "Form 1099-DA" in content
        assert "Single-Seat Desktop" in content
        assert "Zero Network Egress" in content

    def test_prohibited_premature_public_claims_scanner(self):
        """Customer-facing documents must not make unhedged premature claims before signing closure."""
        customer_docs = [
            REPO_ROOT / "docs" / "Edge_Quick_Start.md",
            REPO_ROOT / "docs" / "Independent_Verifier_Guide.md",
            REPO_ROOT / "docs" / "RELEASE_NOTES_1.5.0.md"
        ]

        prohibited_unhedged_phrases = [
            "Apple approved",
            "Apple certified",
            "Microsoft certified",
            "100% secure",
            "IRS approved",
            "IRS certified",
            "audit-proof"
        ]

        for doc_path in customer_docs:
            if doc_path.exists():
                text = doc_path.read_text(encoding="utf-8").lower()
                for phrase in prohibited_unhedged_phrases:
                    assert phrase not in text, f"Prohibited premature claim '{phrase}' found in {doc_path}"
