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
    WINDOWS_REQUIRED_MEMBERS,
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


def _build_mock_windows_zip(zip_path: Path, extra_members: dict = None, missing_required: list = None):
    import zipfile
    required = {
        "VaultBasis-RC3-Windows-x64/RELEASE.txt": b"RELEASE NOTES",
        "VaultBasis-RC3-Windows-x64/VaultBasis-Quick-Start.html": b"<html>Quick Start</html>",
        "VaultBasis-RC3-Windows-x64/VaultBasis-Troubleshooting.html": b"<html><a href=\"VaultBasis-Quick-Start.html\">link</a></html>",
        "VaultBasis-RC3-Windows-x64/VaultBasis/VaultBasis.exe": b"MZ\x90\x00\x03\x00\x00\x00",
        "VaultBasis-RC3-Windows-x64/VaultBasis/_internal/apps/web-dashboard/index.html": b"<html>Dashboard</html>",
        "VaultBasis-RC3-Windows-x64/VaultBasis/_internal/apps/edge-offline-verifier/index.html": b"<html>Verifier</html>",
        "VaultBasis-RC3-Windows-x64/VaultBasis/_internal/apps/verifier/verify_receipt.py": b"# verifier",
        "VaultBasis-RC3-Windows-x64/VaultBasis/_internal/schemas/receipt/receipt-v0.1.json": b"{}",
        "VaultBasis-RC3-Windows-x64/VaultBasis/_internal/docs/scope_and_limitations_v0.1.md": b"# Scope",
        "VaultBasis-RC3-Windows-x64/VaultBasis/_internal/sample/golden_receipt_valid.json": b"{}",
        "VaultBasis-RC3-Windows-x64/VaultBasis/_internal/sample/golden_receipt_tampered.json": b"{}",
    }
    if missing_required:
        for m in missing_required:
            required.pop(m, None)
    if extra_members:
        required.update(extra_members)

    with zipfile.ZipFile(zip_path, "w") as zf:
        for name, content in required.items():
            zf.writestr(name, content)


def test_check_zip_windows_package_hygiene_passes_clean_package(tmp_path):
    from check_release_content import check_zip
    zpath = tmp_path / "VaultBasis-RC3-Windows-x64.zip"
    _build_mock_windows_zip(zpath)
    failures = check_zip(zpath)
    assert failures == [], f"Expected clean pass, got: {failures}"


@pytest.mark.parametrize("forbidden", [
    "VaultBasis-RC3-Windows-x64/VaultBasis/_internal/docs/adr/ADR-001.md",
    "VaultBasis-RC3-Windows-x64/VaultBasis/_internal/docs/audit/status.md",
    "VaultBasis-RC3-Windows-x64/VaultBasis/_internal/docs/qualification/record.md",
    "VaultBasis-RC3-Windows-x64/VaultBasis/_internal/docs/commercial/pricing.md",
    "VaultBasis-RC3-Windows-x64/VaultBasis/_internal/docs/master_tasks_ledger.md",
    "VaultBasis-RC3-Windows-x64/VaultBasis/_internal/apps/web-marketing/api/download.js",
    "VaultBasis-RC3-Windows-x64/VaultBasis/_internal/apps/web-verifier/index.html",
    "VaultBasis-RC3-Windows-x64/VaultBasis/_internal/schemas/canonical/case.py",
    "VaultBasis-RC3-Windows-x64/VaultBasis/_internal/schemas/receipt/signing-v0.1.md",
    "VaultBasis-RC3-Windows-x64/VaultBasis/_internal/schemas/release/manifest-v0.1.json",
])
def test_check_zip_windows_package_hygiene_rejects_forbidden_categories(tmp_path, forbidden):
    from check_release_content import check_zip
    zpath = tmp_path / "VaultBasis-RC3-Windows-x64.zip"
    _build_mock_windows_zip(zpath, extra_members={forbidden: b"internal content"})
    failures = check_zip(zpath)
    assert any("ZIP-FORBIDDEN-CATEGORY" in f for f in failures), f"Failed to reject forbidden category: {forbidden}"


def test_check_zip_windows_package_hygiene_rejects_macos_bundle_path(tmp_path):
    """Negative Control A: .app structural path leakage is rejected regardless of file content."""
    from check_release_content import check_zip
    zpath = tmp_path / "VaultBasis-RC3-Windows-x64.zip"
    _build_mock_windows_zip(
        zpath,
        extra_members={"VaultBasis-RC3-Windows-x64/VaultBasis.app/Contents/MacOS/VaultBasis": b"arbitrary-payload"}
    )
    failures = check_zip(zpath)
    assert any("ZIP-CROSS-PLATFORM-LEAKAGE macOS .app bundle path" in f for f in failures)


@pytest.mark.parametrize("magic,desc", [
    (b"\xcf\xfa\xed\xfe\x07\x00\x00\x01", "Mach-O 64-bit LE"),
    (b"\xfe\xed\xfa\xcf\x01\x00\x00\x07", "Mach-O 64-bit BE"),
    (b"\xce\xfa\xed\xfe\x07\x00\x00\x00", "Mach-O 32-bit LE"),
    (b"\xfe\xed\xfa\xce\x00\x00\x00\x07", "Mach-O 32-bit BE"),
    (b"\xca\xfe\xba\xbe\x00\x00\x00\x02", "FAT universal binary BE"),
    (b"\xbe\xba\xfe\xca\x02\x00\x00\x00", "FAT universal binary LE"),
    (b"\xca\xfe\xba\xbf\x00\x00\x00\x02", "FAT 64-bit universal binary BE"),
    (b"\xbf\xba\xfe\xca\x02\x00\x00\x00", "FAT 64-bit universal binary LE"),
])
def test_check_zip_windows_package_hygiene_rejects_raw_macho_binary_without_extension(tmp_path, magic, desc):
    """Negative Control B: Mach-O binary without .app path or Windows extension is rejected."""
    from check_release_content import check_zip
    zpath = tmp_path / "VaultBasis-RC3-Windows-x64.zip"
    helper_path = "VaultBasis-RC3-Windows-x64/VaultBasis/_internal/native/helper"
    _build_mock_windows_zip(zpath, extra_members={helper_path: magic})
    failures = check_zip(zpath)
    assert any("ZIP-CROSS-PLATFORM-LEAKAGE Mach-O binary" in f for f in failures), (
        f"Gate failed to detect {desc} binary signature in extensionless member"
    )


def test_check_zip_windows_package_hygiene_accepts_pe_and_normal_runtime_members(tmp_path):
    """Control C: Normal Windows PE binaries and runtime data are not falsely classified as Mach-O."""
    from check_release_content import check_zip
    zpath = tmp_path / "VaultBasis-RC3-Windows-x64.zip"
    pe_dll = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
    normal_data = b"raw text or binary data not starting with macho magic"
    _build_mock_windows_zip(
        zpath,
        extra_members={
            "VaultBasis-RC3-Windows-x64/VaultBasis/_internal/native/win_helper.dll": pe_dll,
            "VaultBasis-RC3-Windows-x64/VaultBasis/_internal/data/blob.dat": normal_data,
        }
    )
    failures = check_zip(zpath)
    assert failures == [], f"Expected clean pass for PE and data members, got: {failures}"


@pytest.mark.parametrize("req", WINDOWS_REQUIRED_MEMBERS)
def test_check_zip_windows_package_hygiene_rejects_missing_required_member(tmp_path, req):
    """Negative Control: Omission of any required member at its exact path fails with ZIP-MISSING-REQUIRED."""
    from check_release_content import check_zip
    zpath = tmp_path / "VaultBasis-RC3-Windows-x64.zip"
    full_path = f"VaultBasis-RC3-Windows-x64/{req}"
    _build_mock_windows_zip(zpath, missing_required=[full_path])
    failures = check_zip(zpath)
    assert any("ZIP-MISSING-REQUIRED" in f and req in f for f in failures), (
        f"Gate failed to report missing required member: {req}"
    )



