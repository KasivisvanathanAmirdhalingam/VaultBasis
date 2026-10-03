#!/usr/bin/env python3
"""
VaultBasis RC3-WIN candidate builder (Windows x64 only — fails fast elsewhere).
Mirrors build_rc3_macos.py: deterministic assembly from release source with
current guides + metadata, platform assertions, hashes, honest candidate
manifest. No installer toolchain on stock runners: ships the signed-ready
application layout; a real installer (Inno/MSI) + code signing are tracked
as PLANNED in the manifest and required before qualification. Stdlib +
PyInstaller only. Exit non-zero on any assertion.

Launch gate: BUILD_VERIFIED requires the packaged executable to boot
successfully on the native CI runner, both pre-ZIP and post-ZIP-extraction,
under both piped stdio and disconnected windowed (DEVNULL) modes.
"""
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PACKAGE_NAME = "VaultBasis-RC3-Windows-x64"

HEALTH_URL = "http://127.0.0.1:8000/api/health"
LAUNCH_TIMEOUT_S = 30
POLL_INTERVAL_S = 1


def launch_gate(exe_path: Path, label: str, disconnected_stdio: bool = False) -> None:
    """
    Launch VaultBasis.exe, wait for the health endpoint, then terminate cleanly.
    Tests standard launch and explorer-equivalent (disconnected stdio) launch.
    Raises SystemExit(1) on any failure.
    """
    mode_str = "DISCONNECTED_STDIO (Explorer GUI mode)" if disconnected_stdio else "PIPED_STDIO"
    print(f"\n[LAUNCH-GATE] {label} [{mode_str}]")
    print(f"  exe: {exe_path}")

    popen_kwargs = {
        "cwd": str(exe_path.parent),
    }
    if disconnected_stdio:
        popen_kwargs["stdin"] = subprocess.DEVNULL
        popen_kwargs["stdout"] = subprocess.DEVNULL
        popen_kwargs["stderr"] = subprocess.DEVNULL
    else:
        popen_kwargs["stdout"] = subprocess.PIPE
        popen_kwargs["stderr"] = subprocess.STDOUT

    proc = subprocess.Popen([str(exe_path)], **popen_kwargs)

    deadline = time.monotonic() + LAUNCH_TIMEOUT_S
    healthy = False
    last_err = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=2) as resp:
                if resp.status == 200:
                    healthy = True
                    break
        except Exception as e:
            last_err = e
        time.sleep(POLL_INTERVAL_S)

    proc.terminate()
    stdout_bytes = b""
    if not disconnected_stdio:
        try:
            stdout_bytes, _ = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                stdout_bytes, _ = proc.communicate(timeout=15)
            except subprocess.TimeoutExpired:
                stdout_bytes = b"[process did not terminate after kill - Defender/AV hold suspected]"

        output = stdout_bytes.decode("utf-8", errors="replace").strip()
        if output:
            print(f"  [app output]\n{output}\n  [/app output]")
    else:
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

    if not healthy:
        print(f"  FAIL: health endpoint did not respond within {LAUNCH_TIMEOUT_S}s")
        print(f"  Last error: {last_err}")
        sys.exit(1)

    print(f"  PASS: health endpoint responded within deadline")
    print(f"  Process exit code: {proc.returncode}")


def sh(*args):
    print("+", " ".join(args))
    subprocess.run(list(args), cwd=REPO, check=True)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pe_machine(exe: Path) -> str:
    with open(exe, "rb") as f:
        f.seek(0x3C)
        e_lfanew = struct.unpack("<I", f.read(4))[0]
        f.seek(e_lfanew + 4)
        machine = struct.unpack("<H", f.read(2))[0]
    return {0x8664: "x64", 0xAA64: "ARM64", 0x14C: "x86"}.get(machine, f"UNKNOWN-{machine:#x}")


def main() -> int:
    if sys.platform != "win32":
        print("RC3-WIN builder runs on Windows only.", file=sys.stderr)
        return 2

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                            capture_output=True, text=True, check=True).stdout.strip()

    for p in [REPO / "dist" / PACKAGE_NAME, REPO / "dist" / f"{PACKAGE_NAME}.zip",
              REPO / "dist" / "VaultBasis.exe", REPO / "build" / "VaultBasis"]:
        if p.is_symlink() or p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)

    cmd = [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm",
           "--name", "VaultBasis", "--onedir", "--windowed",
           "--exclude-module", "matplotlib", "--exclude-module", "IPython",
           "--exclude-module", "tkinter", "--exclude-module", "sphinx",
           "--exclude-module", "numpy", "--exclude-module", "pandas",
           "--exclude-module", "scipy", "--exclude-module", "docutils",
           "--hidden-import", "uvicorn.logging",
           "--hidden-import", "uvicorn.loops",
           "--hidden-import", "uvicorn.loops.auto",
           "--hidden-import", "uvicorn.protocols",
           "--hidden-import", "uvicorn.protocols.http",
           "--hidden-import", "uvicorn.protocols.http.auto",
           "--hidden-import", "uvicorn.lifespans",
           "--hidden-import", "uvicorn.lifespans.auto",
           "--add-data", f"apps{os.pathsep}apps",
           "--add-data", f"schemas{os.pathsep}schemas",
           "--add-data", f"docs{os.pathsep}docs",
           "--add-data", f"tests/fixtures/golden_receipt_valid.json{os.pathsep}sample",
           "--add-data", f"tests/fixtures/golden_receipt_tampered.json{os.pathsep}sample",
           "main.py"]
    sh(*cmd)

    # --onedir output: dist/VaultBasis/VaultBasis.exe
    exe = REPO / "dist" / "VaultBasis" / "VaultBasis.exe"
    assert exe.is_file(), "VaultBasis.exe missing in onedir output"
    arch = pe_machine(exe)
    assert arch == "x64", f"wrong-arch Windows binary: {arch} (need x64)"

    pkg = REPO / "dist" / PACKAGE_NAME
    pkg.mkdir(parents=True)
    # Copy entire onedir bundle (exe + _internal/) into package
    shutil.copytree(exe.parent, pkg / "VaultBasis", dirs_exist_ok=True)
    guides = {
        "VaultBasis_Practitioner_Quick_Start.html": "VaultBasis-Quick-Start.html",
        "VaultBasis_Troubleshooting.html": "VaultBasis-Troubleshooting.html",
    }
    with open(REPO / "package.json") as f:
        version = json.load(f)["version"]
    doc_hashes = {}
    for src_name, dst_name in guides.items():
        src = REPO / src_name
        assert src.is_file(), f"missing release doc source: {src_name}"
        data = src.read_bytes()
        (pkg / dst_name).write_bytes(data)
        doc_hashes[dst_name] = hashlib.sha256(data).hexdigest()

    (pkg / "RELEASE.txt").write_text(
        f"VaultBasis Edge RC3-WIN candidate (NOT QUALIFIED — do not distribute)\n"
        f"Version: {version}\nRelease: RC3-WIN\nPlatform: Windows\nArchitecture: x64\n"
        f"Source commit: {commit}\nBuilt: {datetime.now(timezone.utc).isoformat()}\n"
        f"Quick Start: VaultBasis-Quick-Start.html\n"
        f"Troubleshooting: VaultBasis-Troubleshooting.html\n"
        f"Evidence Contract: v0.1\nSigning: UNSIGNED (no certificate in build env)\n"
        f"Installer: PENDING (real installer required before qualification)\n"
    )

    bad_name_tokens = ["macos", "preview-macos", "rc1", "vaultbasis-rc1", ".app", "info.plist"]
    forbidden_names = [p for p in pkg.rglob("*")
                       if any(t in p.name.lower() for t in bad_name_tokens)]
    assert not forbidden_names, f"macOS artifact leaked into Windows package: {forbidden_names}"
    for name in ["VaultBasis-Quick-Start.html", "RELEASE.txt"]:
        text = (pkg / name).read_text(encoding="utf-8", errors="replace")
        for b in ["Release Candidate 1", "VaultBasis Inc.", "verify standard compliance",
                  "Simulate Audits", "proves you ran", "preview-macOS"]:
            assert b not in text, f"BANNED {b!r} in package file {name}"

    # Launch gate — pre-ZIP: launch the built exe from its onedir location.
    launch_gate(exe, "PRE-ZIP: built VaultBasis.exe in dist/VaultBasis/")
    launch_gate(exe, "PRE-ZIP (GUI Mode): built VaultBasis.exe in dist/VaultBasis/", disconnected_stdio=True)

    zip_path = REPO / "dist" / f"{PACKAGE_NAME}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(pkg.rglob("*")):
            if f.is_file():
                z.write(f, arcname=f"{PACKAGE_NAME}/{f.relative_to(pkg)}")
    artifact_sha = sha256_of(zip_path)

    # Launch gate — post-ZIP: extract to fresh temp dir and launch from there.
    with tempfile.TemporaryDirectory(prefix="vb_rc3_extract_") as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(tmp_path)
        # onedir layout: PACKAGE_NAME/VaultBasis/VaultBasis.exe
        extracted_exe = tmp_path / PACKAGE_NAME / "VaultBasis" / "VaultBasis.exe"
        assert extracted_exe.is_file(), f"extracted exe missing at {extracted_exe}"
        launch_gate(extracted_exe, "POST-ZIP: extracted VaultBasis.exe from candidate ZIP")
        launch_gate(extracted_exe, "POST-ZIP (GUI Mode): extracted VaultBasis.exe from candidate ZIP", disconnected_stdio=True)

    manifest = {
        "manifest_version": "v0.1",
        "release": {"tag": "RC3-candidate", "commit": commit, "candidate": "RC3-WIN"},
        "platform_artifact": {
            "os": "windows", "architecture": "x64",
            "artifact_filename": f"{PACKAGE_NAME}.zip", "sha256": artifact_sha,
        },
        "source_identity": {
            "frozen_commit": commit,
            "equivalence_projection": "schemas/receipt/equivalence-projection-v0.1.json",
            "evidence_contract": "v0.1",
        },
        "signing": {
            "status": "UNSIGNED", "notarization_ticket": None,
            "controls": [
                {"control": "pe-arch-x64", "state": "VERIFIED",
                 "evidence": f"PE machine: {arch}"},
                {"control": "no-macos-content", "state": "VERIFIED",
                 "evidence": "package name/content sweep clean"},
                {"control": "trusted-code-signing", "state": "PLANNED",
                 "evidence": "no certificate in build env"},
                {"control": "real-installer", "state": "PLANNED",
                 "evidence": "loose exe layout only; installer required"},
            ],
        },
        "documentation": {
            "quickstart_revision": commit[:8],
            "quickstart_sha256": doc_hashes["VaultBasis-Quick-Start.html"],
            "troubleshooting_revision": commit[:8],
            "troubleshooting_sha256": doc_hashes["VaultBasis-Troubleshooting.html"],
            "content_gate": "PASS",
        },
        "equivalence": {
            "projection_version": "v0.1",
            "projection_digest_mac": "PENDING-MAC-CANDIDATE",
            "projection_digest_win": "PENDING",
            "result": "PENDING",
        },
        "qualification": {
            "distribution": "PENDING", "usability": "PENDING", "leakage_gate": "PASS",
            "launch_gate_pre_zip": "PASS",
            "launch_gate_post_zip": "PASS",
            "result": "CANDIDATE-UNQUALIFIED",
        },
        "publication": {"endpoint": "NONE (do not distribute)", "published_artifact_sha256": artifact_sha},
        "post_publication": {"downloaded_sha256": "PENDING",
                             "matches_qualified": False,
                             "result": "NOT-VERIFIED"},
    }
    (REPO / "dist" / f"{PACKAGE_NAME}.manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n")

    print(f"CANDIDATE: {zip_path.name}")
    print(f"SHA-256:  {artifact_sha}")
    print(f"SIZE:     {zip_path.stat().st_size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
