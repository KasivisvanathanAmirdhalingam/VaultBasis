"""
VaultBasis Pytest Configuration & Global Test Harness
Configures default test environment isolation.
"""

import os
import pytest


@pytest.fixture(autouse=True)
def default_test_commercial_mode(monkeypatch):
    """
    By default, sets dev bypass for pre-existing non-commercial unit tests (e.g. parser math, ATDD journeys)
    so that legacy tests not focused on commercial licensing don't fail due to missing license tokens.
    Commercial entitlement test suites explicitly monkeypatch VAULTBASIS_BYPASS_ENTITLEMENT to '0'.
    """
    if "VAULTBASIS_BYPASS_ENTITLEMENT" not in os.environ:
        monkeypatch.setenv("VAULTBASIS_BYPASS_ENTITLEMENT", "1")
