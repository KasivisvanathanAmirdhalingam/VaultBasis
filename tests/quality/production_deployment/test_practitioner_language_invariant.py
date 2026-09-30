"""
VaultBasis Quality Suite — Practitioner Language & Link Invariant
Tag: regression, release-invariant, practitioner-language

Release invariant: no practitioner-facing source artifact may contain
internal engineering vocabulary, developer artifacts, placeholder links,
raw Markdown syntax, or stale release references.

Scanned surfaces (source — always present, no prior build required):
  - apps/web-marketing/*.html
  - apps/web-verifier/index.html
  - apps/web-dashboard/index.html
  - docs/scope_and_limitations_v0.1.md (rendered into public web)

Fails CI on first violation. Must pass before any production deployment.
"""

import re
from pathlib import Path

import pytest

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Source surfaces scanned directly (no prior build step required)
SOURCE_SURFACES = [
    WORKSPACE_ROOT / "apps" / "web-marketing",
    WORKSPACE_ROOT / "apps" / "web-verifier",
    WORKSPACE_ROOT / "apps" / "web-dashboard",
]

SCOPE_DOC = WORKSPACE_ROOT / "docs" / "scope_and_limitations_v0.1.md"


def _collect_html_files(roots: list[Path]) -> list[Path]:
    files = []
    for root in roots:
        if root.is_file():
            files.append(root)
        elif root.is_dir():
            files.extend(sorted(root.rglob("*.html")))
    return files


# ---------------------------------------------------------------------------
# Forbidden patterns — internal engineering vocabulary
# ---------------------------------------------------------------------------

FORBIDDEN_VOCAB = [
    # Internal release labels
    r"\bMMP-1\b", r"\bMMP1\b", r"\bMMP-1\.1\b", r"\bMMP-1\.5\b", r"\bMMP-2\b",
    r"\bRC1\b", r"\bRC2\b", r"\bRC3\b",
    r"\bPRD\b",
    r"\bBUILD_VERIFIED\b",
    r"\bUAT\b",
    # Internal task-ID prefixes
    r"MMP11-[A-Z]",
    r"\bWEB-\d{3}\b",
    r"\bCONTENT-\d{3}\b",
    r"\bLANG-\d{3}\b",
    r"\bA11Y-\d{3}\b",
    r"\bGATE-\d{2}\b",
    r"\bSEC-\d{3}\b",
    # Internal severity labels used as task classifiers
    r"(?<![A-Za-z0-9])P0(?=[\s:,\.\-]|$)",
    r"(?<![A-Za-z0-9])P1(?=[\s:,\.\-]|$)",
    r"(?<![A-Za-z0-9])P2(?=[\s:,\.\-]|$)",
]

FORBIDDEN_DEVELOPER = [
    r"\blocalhost\b",
    r"ethereal\.email",
    r"\bEthereal\b",
]

FORBIDDEN_PLACEHOLDERS = [
    r'href="#"(?!\s*>)',
    r'href="TODO"',
    r'href=""',
    r'href="PLACEHOLDER"',
]


def _check_file(path: Path, patterns: list[str], label: str) -> list[str]:
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
def test_web_sources_no_internal_vocabulary():
    """Web source HTML must not contain internal release vocabulary."""
    files = _collect_html_files(SOURCE_SURFACES)
    assert files, f"No HTML source files found in {SOURCE_SURFACES}"
    violations = []
    for f in files:
        violations.extend(_check_file(f, FORBIDDEN_VOCAB, "VOCAB"))
    assert not violations, (
        f"{len(violations)} internal-vocabulary violation(s) in source HTML:\n"
        + "\n".join(violations)
    )


@pytest.mark.regression
def test_web_sources_no_developer_artifacts():
    """Web source HTML must not contain developer/tooling artifacts."""
    files = _collect_html_files(SOURCE_SURFACES)
    assert files, f"No HTML source files found in {SOURCE_SURFACES}"
    violations = []
    for f in files:
        violations.extend(_check_file(f, FORBIDDEN_DEVELOPER, "DEV"))
    assert not violations, (
        f"{len(violations)} developer-artifact violation(s) in source HTML:\n"
        + "\n".join(violations)
    )


@pytest.mark.regression
def test_web_sources_no_placeholder_links():
    """Web source HTML must not contain placeholder or empty links."""
    files = _collect_html_files(SOURCE_SURFACES)
    assert files, f"No HTML source files found in {SOURCE_SURFACES}"
    violations = []
    for f in files:
        violations.extend(_check_file(f, FORBIDDEN_PLACEHOLDERS, "LINK"))
    assert not violations, (
        f"{len(violations)} placeholder-link violation(s) in source HTML:\n"
        + "\n".join(violations)
    )


@pytest.mark.regression
def test_scope_doc_no_internal_vocabulary():
    """Scope & Limitations doc (rendered into public web) must not contain internal vocabulary."""
    assert SCOPE_DOC.is_file(), f"Scope doc not found: {SCOPE_DOC}"
    violations = _check_file(SCOPE_DOC, FORBIDDEN_VOCAB, "VOCAB")
    assert not violations, (
        f"{len(violations)} internal-vocabulary violation(s) in scope doc:\n"
        + "\n".join(violations)
    )
