"""
Normative Approved Rule Pack Registry for VaultBasis Edge.
Ensures deterministic, fail-closed regulatory routing.
"""
from typing import Dict, Tuple

# Formally approved rule packs for deterministic reconciliation.
# (jurisdiction, tax_year) -> approved canonical ruleset_id
SUPPORTED_RULESETS: Dict[Tuple[str, int], str] = {
    ("US", 2025): "VB_US_1099DA_2025_R1"
}
