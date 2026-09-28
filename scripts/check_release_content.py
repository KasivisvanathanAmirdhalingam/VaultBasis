#!/usr/bin/env python3
"""
VaultBasis — Release Content Gate (package-content lint).
Fails the pipeline when practitioner-facing content carries superseded claims
(VB-RC2-UAT-002..005, VB-RC2-UAT-010) or developer shell instructions in the
primary Quick Start. Contextual terms (localhost, ports) are reviewed by policy,
not blindly banned: allowed in Troubleshooting/Technical, forbidden as Quick
Start instructions.
Stdlib only. Exit 0 = PASS, 1 = FAIL.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Hard bans: must not appear in ANY practitioner-facing file (RC3 frozen claims).
HARD_BANS = [
    "Release Candidate 1",
    "VaultBasis Inc.",
    "verify standard compliance",
    "Simulate Audits",
    "proves you ran",
]

PRACTITIONER_FILES = [
    "VaultBasis_Practitioner_Quick_Start.html",
    "VaultBasis_Troubleshooting.html",
    "VaultBasis_Quick_Start_Guide.html",
    "apps/web-marketing/index.html",
    "apps/web-verifier/index.html",
    "apps/web-dashboard/index.html",
]

# Shell/bypass instructions: forbidden in the PRIMARY Quick Start only.
# (They belong in Troubleshooting -> Advanced and the Technical Guide.)
QUICKSTART_FILE = "VaultBasis_Practitioner_Quick_Start.html"
QUICKSTART_BANS = [
    "xattr",
    "chmod",
    "PowerShell",
    "Open Anyway",
    "Run anyway",
]


# Design-token drift tripwire (apps/web-shared/design-tokens-v0.1.json is the
# versioned source of truth). Each practitioner surface must carry the primary
# color and body font; independent per-file edits fail loudly here.
TOKEN_SURFACES = [
    "VaultBasis_Practitioner_Quick_Start.html",
    "VaultBasis_Troubleshooting.html",
    "apps/web-marketing/index.html",
    "apps/web-verifier/index.html",
]


def run_checks(repo_root: Path) -> list:
    """Returns a list of failure strings; empty means PASS. Pure stdlib."""
    failures = []

    for rel in PRACTITIONER_FILES:
        p = repo_root / rel
        if not p.is_file():
            failures.append(f"MISSING practitioner file: {rel}")
            continue
        text = p.read_text(encoding="utf-8")
        for banned in HARD_BANS:
            if banned in text:
                failures.append(f"BANNED {banned!r} in {rel}")

    qs = repo_root / QUICKSTART_FILE
    if qs.is_file():
        text = qs.read_text(encoding="utf-8")
        for banned in QUICKSTART_BANS:
            if banned in text:
                failures.append(f"SHELL/BYPASS {banned!r} in primary Quick Start {QUICKSTART_FILE}")

    for rel in TOKEN_SURFACES:
        p = repo_root / rel
        if not p.is_file():
            continue  # missing files already reported above when applicable
        text = p.read_text(encoding="utf-8")
        if "#2563eb" not in text and "#2563EB" not in text:
            failures.append(f"TOKEN-DRIFT no primary color in {rel} (see design-tokens-v0.1.json)")
        if "Plus Jakarta Sans" not in text:
            failures.append(f"TOKEN-DRIFT no body font in {rel} (see design-tokens-v0.1.json)")

    return failures


def main() -> int:
    failures = run_checks(REPO)

    if failures:
        print("RELEASE-CONTENT-GATE: FAIL")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"RELEASE-CONTENT-GATE: PASS ({len(PRACTITIONER_FILES)} files, "
          f"{len(HARD_BANS)} claim bans, {len(QUICKSTART_BANS)} quickstart bans)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
