"""
VaultBasis Quality Suite — Practitioner Language & Link Invariant
Tag: regression, release-invariant, practitioner-language

Release invariant: no practitioner-facing generated artifact may contain
internal engineering vocabulary, developer artifacts, placeholder links,
raw Markdown syntax, or stale release references.

Scanned surfaces:
  - dist/public-web/ (generated marketing/verifier/docs output)
  - apps/web-dashboard/index.html (Edge practitioner UI — not built, ships directly)

Fails CI on first violation. Must pass before any production deployment.
"""

import re
from pathlib import Path

import pytest

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Generated public-web output (built by scripts/build_public_web.js)
PUBLIC_WEB_DIST = WORKSPACE_ROOT / "dist" / "public-web"

# Edge dashboard ships directly (not through the build pipeline)
EDGE_DASHBOARD = WORKSPACE_ROOT / "apps" / "web-dashboard" / "index.html"


def _collect_html_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob("*.html"))


# ---------------------------------------------------------------------------
# Forbidden patterns — internal engineering vocabulary
# ---------------------------------------------------------------------------

# Whole-word matches for release-management terms that must never appear in
# practitioner-facing output. Checked as \bTERM\b to avoid false positives
# on partial matches (e.g. "promo" should not trigger "PRD" match).
FORBIDDEN_VOCAB = [
    # Internal release labels
    r"\bMMP-1\b", r"\bMMP1\b", r"\bMMP-1\.1\b", r"\bMMP-1\.5\b", r"\bMMP-2\b",
    r"\bRC1\b", r"\bRC2\b", r"\bRC3\b",
    r"\bPRD\b",
    r"\bBUILD_VERIFIED\b",
    r"\bUAT\b",
    # Internal task-ID prefixes (pattern: "MMP11-", "WEB-", "CONTENT-", etc.)
    r"MMP11-[A-Z]",
    r"\bWEB-\d{3}\b",
    r"\bCONTENT-\d{3}\b",
    r"\bLANG-\d{3}\b",
    r"\bA11Y-\d{3}\b",
    r"\bGATE-\d{2}\b",
    r"\bSEC-\d{3}\b",
    # Internal severity labels used as task classifiers (not prose words)
    # Match only when used as standalone classification labels, not in prose.
    # e.g. "P0 blocker" is forbidden; "P0.1" is not a concern here.
    # Use a conservative pattern: preceded by whitespace/start and followed by
    # punctuation or whitespace (avoids false positives on "P01234" etc.)
    r"(?<![A-Za-z0-9])P0(?=[\s:,\.\-]|$)",
    r"(?<![A-Za-z0-9])P1(?=[\s:,\.\-]|$)",
    r"(?<![A-Za-z0-9])P2(?=[\s:,\.\-]|$)",
]

# Developer/tooling artifacts
FORBIDDEN_DEVELOPER = [
    r"\blocalhost\b",
    r"ethereal\.email",
    r"\bEthereal\b",
]

# Raw Markdown visible in rendered HTML
FORBIDDEN_MARKDOWN = [
    r"^#{1,6} ",          # Markdown headings at line start
    r"\*\*[^\*]+\*\*",    # Bold **text** (should be <strong> in HTML)
]

# Placeholder links
FORBIDDEN_PLACEHOLDERS = [
    r'href="#"(?!\s*>)',   # bare anchor (allow href="#id" but not standalone)
    r'href="TODO"',
    r'href=""',
    r'href="PLACEHOLDER"',
]


def _check_file(path: Path, patterns: list[str], label: str) -> list[str]:
    """Return list of violation strings for a file."""
    violations = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for pattern in patterns:
        matches = list(re.finditer(pattern, text, re.MULTILINE))
        for m in matches:
            line_num = text[: m.start()].count("\n") + 1
            violations.append(
                f"{label} | {path.relative_to(WORKSPACE_ROOT)} "
                f"line {line_num}: matched /{pattern}/ → {m.group()!r}"
            )
    return violations


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.regression
def test_generated_public_web_no_internal_vocabulary():
    """Generated dist/public-web HTML must not contain internal release vocabulary."""
    files = _collect_html_files(PUBLIC_WEB_DIST)
    assert files, (
        f"No HTML files found in {PUBLIC_WEB_DIST}. "
        "Run 'node scripts/build_public_web.js' before this test."
    )
    violations = []
    for f in files:
        violations.extend(_check_file(f, FORBIDDEN_VOCAB, "VOCAB"))
    assert not violations, (
        f"{len(violations)} internal-vocabulary violation(s) in generated output:\n"
        + "\n".join(violations)
    )


@pytest.mark.regression
def test_generated_public_web_no_developer_artifacts():
    """Generated dist/public-web HTML must not contain developer/tooling artifacts."""
    files = _collect_html_files(PUBLIC_WEB_DIST)
    assert files, (
        f"No HTML files found in {PUBLIC_WEB_DIST}. "
        "Run 'node scripts/build_public_web.js' before this test."
    )
    violations = []
    for f in files:
        violations.extend(_check_file(f, FORBIDDEN_DEVELOPER, "DEV"))
    assert not violations, (
        f"{len(violations)} developer-artifact violation(s) in generated output:\n"
        + "\n".join(violations)
    )


@pytest.mark.regression
def test_generated_public_web_no_placeholder_links():
    """Generated dist/public-web HTML must not contain placeholder or empty links."""
    files = _collect_html_files(PUBLIC_WEB_DIST)
    assert files, (
        f"No HTML files found in {PUBLIC_WEB_DIST}. "
        "Run 'node scripts/build_public_web.js' before this test."
    )
    violations = []
    for f in files:
        violations.extend(_check_file(f, FORBIDDEN_PLACEHOLDERS, "LINK"))
    assert not violations, (
        f"{len(violations)} placeholder-link violation(s) in generated output:\n"
        + "\n".join(violations)
    )


@pytest.mark.regression
def test_edge_dashboard_no_internal_vocabulary():
    """Edge dashboard (apps/web-dashboard/index.html) must not contain internal vocabulary."""
    assert EDGE_DASHBOARD.is_file(), f"Edge dashboard not found: {EDGE_DASHBOARD}"
    violations = _check_file(EDGE_DASHBOARD, FORBIDDEN_VOCAB, "VOCAB")
    assert not violations, (
        f"{len(violations)} internal-vocabulary violation(s) in Edge dashboard:\n"
        + "\n".join(violations)
    )


@pytest.mark.regression
def test_edge_dashboard_no_developer_artifacts():
    """Edge dashboard must not contain developer/tooling artifacts."""
    assert EDGE_DASHBOARD.is_file(), f"Edge dashboard not found: {EDGE_DASHBOARD}"
    violations = _check_file(EDGE_DASHBOARD, FORBIDDEN_DEVELOPER, "DEV")
    assert not violations, (
        f"{len(violations)} developer-artifact violation(s) in Edge dashboard:\n"
        + "\n".join(violations)
    )


@pytest.mark.regression
def test_edge_dashboard_no_placeholder_links():
    """Edge dashboard must not contain placeholder or empty links."""
    assert EDGE_DASHBOARD.is_file(), f"Edge dashboard not found: {EDGE_DASHBOARD}"
    violations = _check_file(EDGE_DASHBOARD, FORBIDDEN_PLACEHOLDERS, "LINK")
    assert not violations, (
        f"{len(violations)} placeholder-link violation(s) in Edge dashboard:\n"
        + "\n".join(violations)
    )
