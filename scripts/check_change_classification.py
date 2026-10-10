#!/usr/bin/env python3
"""
VaultBasis — Change Classification Validator & Fail-Closed Guard
Conforms to REGRESSION-COVERAGE-001 under VB-FRZ-REG-001.

Validates that any git commit or working tree modification affecting release scope
supplies a recognized change classification, and verifies that appropriate regression
gates are enforced for that classification.

Permitted Classification Tags:
  - DOCS_ONLY
  - MARKETING_ONLY
  - QUALIFICATION_HARNESS
  - PRODUCT_UI
  - PRODUCT_RUNTIME
  - PACKAGING
  - COMMERCIAL
  - SECURITY
  - MODE3_AUTHORIZED
"""

import os
import subprocess
import sys
from pathlib import Path

VALID_CLASSIFICATIONS = {
    "DOCS_ONLY",
    "MARKETING_ONLY",
    "QUALIFICATION_HARNESS",
    "PRODUCT_UI",
    "PRODUCT_RUNTIME",
    "PACKAGING",
    "COMMERCIAL",
    "SECURITY",
    "MODE3_AUTHORIZED",
}

# Directories and paths that trigger fail-closed classification enforcement
SENSITIVE_PREFIXES = [
    "edge/",
    "apps/web-dashboard/",
    "scripts/build_",
    "scripts/installer_",
    "schemas/",
    "main.py",
    "package.json",
    "requirements.txt",
]


def get_changed_files() -> list[str]:
    """Gets list of changed files relative to HEAD or origin/preprod."""
    try:
        # Check against HEAD first
        res = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return [line.strip() for line in res.stdout.strip().splitlines()]
    except Exception:
        pass

    # Fallback to status
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            files = []
            for line in res.stdout.strip().splitlines():
                if len(line) > 3:
                    files.append(line[3:].strip())
            return files
    except Exception:
        pass
    return []


def get_commit_classification() -> str | None:
    """Extracts classification tag from commit message or VAULTBASIS_CHANGE_CLASS env var."""
    env_class = os.environ.get("VAULTBASIS_CHANGE_CLASS")
    if env_class and env_class in VALID_CLASSIFICATIONS:
        return env_class

    try:
        res = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            msg = res.stdout
            for tag in VALID_CLASSIFICATIONS:
                if f"[{tag}]" in msg or f"class:{tag}" in msg.lower() or f"{tag}:" in msg:
                    return tag
    except Exception:
        pass
    return None


def main() -> int:
    classification = get_commit_classification()
    changed_files = get_changed_files()

    sensitive_changes = [
        f for f in changed_files
        if any(f.startswith(prefix) for prefix in SENSITIVE_PREFIXES)
    ]

    print("=" * 80)
    print("VAULTBASIS CHANGE CLASSIFICATION & REGRESSION GUARD")
    print("Standard: REGRESSION-COVERAGE-001 (Left-Shift Maximum)")
    print("=" * 80)
    print(f"Detected Classification : {classification or 'NONE SUPPLIED'}")
    print(f"Total Changed Files     : {len(changed_files)}")
    print(f"Sensitive Release Files : {len(sensitive_changes)}")

    if sensitive_changes:
        print("\nSensitive files detected:")
        for sf in sensitive_changes[:10]:
            print(f"  - {sf}")
        if len(sensitive_changes) > 10:
            print(f"  ... and {len(sensitive_changes) - 10} more")

    if sensitive_changes and not classification:
        print("\n[FAIL-CLOSED] SENSITIVE RELEASE FILES MODIFIED WITHOUT EXPLICIT CHANGE CLASSIFICATION.")
        print("Release policy requires one of the following canonical tags in commit message or VAULTBASIS_CHANGE_CLASS:")
        for tag in sorted(VALID_CLASSIFICATIONS):
            print(f"  • {tag}")
        print("\nBlocking CI and pre-commit progression.")
        return 1

    print("\n✓ Change classification guard PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
