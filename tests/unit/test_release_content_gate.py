"""
Permanent negative control for the release content gate (VB-RC2-UAT-010).
A gate that has only ever passed is weaker evidence than one demonstrated to
reject a known-bad package: this suite proves run_checks() passes on the real
tree AND fails on every banned string via poisoned scratch copies.
"""
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from check_release_content import (
    HARD_BANS,
    PRACTITIONER_FILES,
    QUICKSTART_BANS,
    QUICKSTART_FILE,
    run_checks,
)


def test_release_content_gate_passes_on_clean_tree():
    assert run_checks(REPO) == []


def _scratch_tree(tmp_path: Path) -> Path:
    root = tmp_path / "pkg"
    for rel in PRACTITIONER_FILES:
        src = REPO / rel
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return root


@pytest.mark.parametrize("banned", HARD_BANS)
def test_release_content_gate_rejects_every_hard_ban(tmp_path, banned):
    root = _scratch_tree(tmp_path)
    target = root / PRACTITIONER_FILES[1]  # poison the Troubleshooting guide
    target.write_text(target.read_text(encoding="utf-8") + "\n" + banned, encoding="utf-8")
    failures = run_checks(root)
    assert any(banned in f for f in failures), f"gate missed hard ban {banned!r}"


@pytest.mark.parametrize("banned", QUICKSTART_BANS)
def test_release_content_gate_rejects_quickstart_shell_instructions(tmp_path, banned):
    root = _scratch_tree(tmp_path)
    target = root / QUICKSTART_FILE
    target.write_text(target.read_text(encoding="utf-8") + "\n" + banned, encoding="utf-8")
    failures = run_checks(root)
    assert any(banned in f for f in failures), f"gate missed quickstart ban {banned!r}"


def test_release_content_gate_rejects_missing_file(tmp_path):
    root = _scratch_tree(tmp_path)
    (root / PRACTITIONER_FILES[0]).unlink()
    failures = run_checks(root)
    assert any("MISSING" in f for f in failures)
