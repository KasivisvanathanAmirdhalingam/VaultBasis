#!/usr/bin/env python3
"""
VaultBasis — Release Content Gate (package-content lint + ZIP artifact inspection).
Fails the pipeline when practitioner-facing content carries superseded claims
(VB-RC2-UAT-002..005, VB-RC2-UAT-010) or developer shell instructions in the
primary Quick Start. Also inspects RC3 ZIP artifacts for prohibited content/files.
Contextual terms (localhost, ports) are reviewed by policy, not blindly banned.
Stdlib only. Exit 0 = PASS, 1 = FAIL.

Usage:
  python3 scripts/check_release_content.py            # source lint only
  python3 scripts/check_release_content.py <zip>      # source lint + ZIP inspection
"""
import io
import sys
import zipfile
from pathlib import Path

# Windows CI runners default to cp1252 stdout. Force UTF-8 so diagnostic
# messages with non-ASCII characters (arrows, bullets) don't crash the gate.
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

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
    "apps/web-dashboard/index.html",
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


# Strings that must never appear inside any RC3 ZIP artifact.
ZIP_BANNED_NAMES = [
    "VaultBasis-RC1",
    "preview-macOS",
    "VaultBasis_Quick_Start_Guide",  # obsolete dark guide — canonical is VaultBasis-Quick-Start.html
]
# Hard bans: must not appear in ANY text member of the ZIP
ZIP_HARD_BANNED_CONTENT = [
    "Release Candidate 1",
    "VaultBasis Inc.",
    "verify standard compliance",
    "Simulate Audits",
    "proves you ran",
]

# Shell/bypass bans: only applied to the canonical Quick Start member
ZIP_QUICKSTART_MEMBER = "VaultBasis-Quick-Start.html"
ZIP_QUICKSTART_BANNED_CONTENT = [
    "xattr",
    "chmod",
    "Open Anyway",
    "Run anyway",
]


def check_zip_relative_links(names: list, zf) -> list:
    """
    Verify that every relative href/src in HTML members resolves to another
    member in the same ZIP directory. External URLs (http/https/mailto/#)
    and absolute paths are skipped. A broken relative link is a packaging
    defect that causes silent failure for recipients (Defect B in RC3 smoke).
    """
    import re
    failures = []
    # Build a set of bare filenames present in the ZIP (flat — all members)
    zip_filenames = {Path(n).name for n in names if not n.endswith("/")}
    for name in names:
        if not name.endswith(".html"):
            continue
        try:
            text = zf.read(name).decode("utf-8", errors="replace")
        except Exception:
            continue
        member_name = Path(name).name
        # Extract all href and src attribute values
        for attr_val in re.findall(r'(?:href|src)=["\']([^"\']+)["\']', text):
            # Skip external URLs, anchors, mailto, and javascript: pseudo-URLs
            if attr_val.startswith(("http://", "https://", "mailto:", "#", "/", "javascript:")):
                continue
            # Strip query/fragment for file resolution
            target = attr_val.split("?")[0].split("#")[0]
            if not target:
                continue
            target_name = Path(target).name
            if target_name not in zip_filenames:
                failures.append(
                    f"ZIP-BROKEN-LINK in {member_name}: "
                    f"'{attr_val}' -> '{target_name}' not found in package"
                )
    return failures


def check_zip(zip_path: Path) -> list:
    """Inspect an RC3 candidate ZIP. Returns failure strings; empty = PASS."""
    failures = []
    if not zip_path.is_file():
        return [f"ZIP not found: {zip_path}"]
    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            # Banned filenames
            for name in names:
                for banned in ZIP_BANNED_NAMES:
                    if banned in name:
                        failures.append(f"ZIP-BANNED filename {banned!r} in {name}")
            # Inspect text members for hard-banned content
            for name in names:
                if not any(name.endswith(ext) for ext in (".html", ".txt", ".json", ".md")):
                    continue
                try:
                    text = zf.read(name).decode("utf-8", errors="replace")
                except Exception:
                    continue
                for banned in ZIP_HARD_BANNED_CONTENT:
                    if banned in text:
                        failures.append(f"ZIP-BANNED content {banned!r} in {name}")
                # Shell/bypass bans: Quick Start member only (same policy as source gate)
                if name.endswith(ZIP_QUICKSTART_MEMBER):
                    for banned in ZIP_QUICKSTART_BANNED_CONTENT:
                        if banned in text:
                            failures.append(
                                f"ZIP-SHELL-BANNED {banned!r} in Quick Start member {name}"
                            )
            # Relative link integrity: every local href/src must resolve within the ZIP
            failures.extend(check_zip_relative_links(names, zf))
    except zipfile.BadZipFile as e:
        failures.append(f"ZIP unreadable: {e}")
    return failures


def main() -> int:
    failures = run_checks(REPO)

    # Optional ZIP inspection when a path is passed as argv[1]
    if len(sys.argv) > 1:
        zip_path = Path(sys.argv[1])
        zip_failures = check_zip(zip_path)
        if zip_failures:
            print(f"ZIP-CONTENT-GATE: FAIL ({zip_path.name})")
            for f in zip_failures:
                print(f"  - {f}")
            failures.extend(zip_failures)
        else:
            print(f"ZIP-CONTENT-GATE: PASS ({zip_path.name})")

    if failures:
        print("RELEASE-CONTENT-GATE: FAIL")
        for f in failures:
            if not f.startswith("ZIP"):  # already printed above
                print(f"  - {f}")
        return 1
    print(f"RELEASE-CONTENT-GATE: PASS ({len(PRACTITIONER_FILES)} files, "
          f"{len(HARD_BANS)} claim bans, {len(QUICKSTART_BANS)} quickstart bans)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
