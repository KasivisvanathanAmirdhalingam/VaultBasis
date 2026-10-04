"""
VaultBasis MMP-1.5 System Version & Release Channel Compatibility Service
Conforms to docs/mmp15_task_ledger.md (MMP15-OPS-002) and PRD §64.1.

Architectural Invariants:
1. Controlled Runtime Metadata: Centralized, immutable build and version identifiers.
2. Frozen Channel Semantics: DEVELOPMENT, CANDIDATE, STABLE, LTS.
3. Decoupled Compatibility: Schema/protocol support matrix distinct from release channels.
4. Zero Network / No Telemetry: Strictly local, read-only endpoint with no auto-updater or network calls.
"""

import os
import platform
import subprocess
import sys
from enum import Enum
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from edge.storage.sqlite_store import SQLiteStore


class ReleaseChannel(str, Enum):
    """
    Controlled distribution release channel vocabulary.
    """
    DEVELOPMENT = "DEVELOPMENT"
    CANDIDATE = "CANDIDATE"
    STABLE = "STABLE"
    LTS = "LTS"


def _resolve_build_sha() -> str:
    """
    Resolves active build SHA from environment, embedded build metadata, or local git tree.
    """
    env_sha = os.environ.get("VAULTBASIS_BUILD_SHA")
    if env_sha:
        return env_sha.strip()

    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=1.0,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass

    return "3152df830089f2d1e2b4676573c387b99adfe092"


def _resolve_release_channel() -> ReleaseChannel:
    """Resolves release channel from environment or defaults to DEVELOPMENT."""
    env_chan = os.environ.get("VAULTBASIS_RELEASE_CHANNEL", "DEVELOPMENT").upper().strip()
    try:
        return ReleaseChannel(env_chan)
    except ValueError:
        return ReleaseChannel.DEVELOPMENT


def _resolve_platform_identifier() -> str:
    """Returns normalized OS and architecture platform string (e.g. darwin-arm64, windows-x64, linux-x64)."""
    os_name = platform.system().lower()
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        norm_arch = "x64"
    elif machine in ("arm64", "aarch64"):
        norm_arch = "arm64"
    else:
        norm_arch = machine

    return f"{os_name}-{norm_arch}"


class CompatibilityMatrix(BaseModel):
    """
    Declares the schema and protocol formats supported by this runtime.
    """
    supported_database_schema_versions: List[int] = Field(
        default_factory=lambda: [1, 2, 3, 4]
    )
    supported_license_protocol_versions: List[str] = Field(
        default_factory=lambda: ["v1.0"]
    )
    supported_receipt_schema_versions: List[str] = Field(
        default_factory=lambda: ["v0.1"]
    )
    supported_intake_profiles: List[str] = Field(
        default_factory=lambda: ["1099DA", "COINBASE_CSV", "KRAKEN_LEDGER", "GENERIC_TAX_LOTS"]
    )


def _resolve_os_name() -> str:
    return platform.system()


def _resolve_architecture() -> str:
    return platform.machine()


class SystemVersionInfo(BaseModel):
    """
    Complete immutable system, build, channel, and compatibility metadata.
    """
    product: str = "VaultBasis"
    version: str = "1.5.0-dev"
    build_sha: str = Field(default_factory=_resolve_build_sha)
    release_channel: ReleaseChannel = Field(default_factory=_resolve_release_channel)
    platform: str = Field(default_factory=_resolve_platform_identifier)
    os_name: str = Field(default_factory=_resolve_os_name)
    architecture: str = Field(default_factory=_resolve_architecture)
    python_version: str = Field(default_factory=lambda: sys.version.split()[0])
    schema_version: int = Field(default=SQLiteStore.CURRENT_SCHEMA_VERSION)
    license_protocol_version: str = "v1.0"
    receipt_schema_version: str = "v0.1"
    compatibility: CompatibilityMatrix = Field(default_factory=CompatibilityMatrix)


def get_system_version() -> SystemVersionInfo:
    """Returns current system version and runtime metadata."""
    return SystemVersionInfo()
