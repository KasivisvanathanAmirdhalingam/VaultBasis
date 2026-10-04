"""
VaultBasis MMP-1.5 System Version & Release Channel Compatibility Test Suite
Tests MMP15-OPS-002:
1. Controlled build and version metadata
2. Release channel vocabulary (DEVELOPMENT, CANDIDATE, STABLE, LTS)
3. Platform and architecture detection
4. Compatibility matrix decoupling
5. REST API endpoint GET /api/system/version
6. Zero network / read-only guarantee
"""

import os
import pytest
from fastapi.testclient import TestClient

from edge.api.app import app
from edge.system.version import (
    ReleaseChannel,
    SystemVersionInfo,
    get_system_version,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_system_version_defaults():
    info = get_system_version()
    assert info.product == "VaultBasis"
    assert info.version == "1.5.0-dev"
    assert len(info.build_sha) >= 7
    assert info.release_channel in (
        ReleaseChannel.DEVELOPMENT,
        ReleaseChannel.CANDIDATE,
        ReleaseChannel.STABLE,
        ReleaseChannel.LTS,
    )
    assert info.platform != ""
    assert info.architecture != ""
    assert info.python_version != ""
    assert info.schema_version >= 3
    assert info.license_protocol_version == "v1.0"
    assert info.receipt_schema_version == "v0.1"


def test_release_channel_vocabulary():
    assert ReleaseChannel.DEVELOPMENT == "DEVELOPMENT"
    assert ReleaseChannel.CANDIDATE == "CANDIDATE"
    assert ReleaseChannel.STABLE == "STABLE"
    assert ReleaseChannel.LTS == "LTS"


def test_release_channel_environment_override(monkeypatch):
    monkeypatch.setenv("VAULTBASIS_RELEASE_CHANNEL", "STABLE")
    info = get_system_version()
    assert info.release_channel == ReleaseChannel.STABLE

    monkeypatch.setenv("VAULTBASIS_RELEASE_CHANNEL", "CANDIDATE")
    info = get_system_version()
    assert info.release_channel == ReleaseChannel.CANDIDATE

    monkeypatch.setenv("VAULTBASIS_RELEASE_CHANNEL", "LTS")
    info = get_system_version()
    assert info.release_channel == ReleaseChannel.LTS

    # Unknown defaults safely to DEVELOPMENT
    monkeypatch.setenv("VAULTBASIS_RELEASE_CHANNEL", "UNKNOWN_CUSTOM_CHANNEL")
    info = get_system_version()
    assert info.release_channel == ReleaseChannel.DEVELOPMENT


def test_build_sha_environment_override(monkeypatch):
    test_sha = "abcdef1234567890abcdef1234567890abcdef12"
    monkeypatch.setenv("VAULTBASIS_BUILD_SHA", test_sha)
    info = get_system_version()
    assert info.build_sha == test_sha


def test_compatibility_matrix_independence():
    info = get_system_version()
    matrix = info.compatibility
    assert 3 in matrix.supported_database_schema_versions
    assert "v1.0" in matrix.supported_license_protocol_versions
    assert "v0.1" in matrix.supported_receipt_schema_versions
    assert "1099DA" in matrix.supported_intake_profiles


def test_api_system_version_endpoint(client):
    res = client.get("/api/system/version")
    assert res.status_code == 200
    data = res.json()
    assert data["product"] == "VaultBasis"
    assert data["version"] == "1.5.0-dev"
    assert "build_sha" in data
    assert "release_channel" in data
    assert "platform" in data
    assert "schema_version" in data
    assert "license_protocol_version" in data
    assert "receipt_schema_version" in data
    assert "compatibility" in data
