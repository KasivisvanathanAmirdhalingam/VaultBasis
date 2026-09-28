#!/usr/bin/env python3
"""
VaultBasis RC3-MAC candidate builder (macOS arm64 only — fails fast elsewhere).
Deterministic assembly: frozen source -> .app bundle -> platform package with
current guides + release metadata -> hashes. Asserts the UAT-MAC-003 negative
vectors: Finder-recognizable application (no extensionless loose binary), no
stale RC1 content, correct-arch executable. Stdlib + PyInstaller + system tools.
 Signing/notarization: UNSIGNED here (no Developer ID); recorded honestly in
the candidate manifest. Exit non-zero on any assertion.
"""
import hashlib
import json
import os
import plistlib
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
APP_NAME = "VaultBasis.app"
PACKAGE_NAME = "VaultBasis-RC3-macOS-arm64"


def sh(*args):
    print("+", " ".join(args))
    subprocess.run(list(args), cwd=REPO, check=True)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if sys.platform != "darwin":
        print("RC3-MAC builder runs on macOS only.", file=sys.stderr)
        return 2
    if os.uname().machine != "arm64":
        print("RC3-MAC candidate requires Apple Silicon arm64.", file=sys.stderr)
        return 2

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                            capture_output=True, text=True, check=True).stdout.strip()

    # 1. Clean previous candidate outputs (never the sealed RC2 history).
    for p in [REPO / "build" / "VaultBasis", REPO / "dist" / APP_NAME,
              REPO / "dist" / PACKAGE_NAME, REPO / "dist" / f"{PACKAGE_NAME}.zip"]:
        if p.is_symlink() or p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)

    # 2. Build the .app bundle.
    sh(sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm",
       "VaultBasis-RC3-macOS.spec")

    app_dir = REPO / "dist" / APP_NAME
    exe = app_dir / "Contents" / "MacOS" / "VaultBasis"
    plist = app_dir / "Contents" / "Info.plist"

    # 3. Package assertions (UAT-MAC-003 negative vectors, automated).
    assert app_dir.is_dir(), "VaultBasis.app missing — Finder would have no application"
    assert exe.is_file(), "bundle executable missing"
    file_out = subprocess.run(["file", str(exe)], capture_output=True,
                              text=True, check=True).stdout
    assert "arm64" in file_out, f"wrong-arch executable: {file_out.strip()}"
    assert "x86_64" not in file_out, f"x86-only object leaked in: {file_out.strip()}"
    with open(plist, "rb") as f:
        info = plistlib.load(f)
    assert info.get("CFBundleIdentifier") == "com.vaultbasis.edge", info
    assert info.get("CFBundleName") == "VaultBasis", info
    assert os.access(exe, os.X_OK), "bundle executable not runnable"

    # 4. Assemble platform package from release source (never the stale ZIP).
    pkg = REPO / "dist" / PACKAGE_NAME
    pkg.mkdir(parents=True)
    shutil.copytree(app_dir, pkg / APP_NAME, symlinks=True)
    guides = {
        "VaultBasis_Practitioner_Quick_Start.html": "VaultBasis-Quick-Start.html",
        "VaultBasis_Troubleshooting.html": "VaultBasis-Troubleshooting.html",
    }
    doc_hashes = {}
    for src_name, dst_name in guides.items():
        src = REPO / src_name
        assert src.is_file(), f"missing release doc source: {src_name}"
        data = src.read_bytes()
        (pkg / dst_name).write_bytes(data)
        doc_hashes[dst_name] = hashlib.sha256(data).hexdigest()

    with open(REPO / "package.json") as f:
        version = json.load(f)["version"]
    release_txt = (
        f"VaultBasis Edge RC3-MAC candidate (NOT QUALIFIED — do not distribute)\n"
        f"Version: {version}\nRelease: RC3-MAC\nPlatform: macOS\nArchitecture: arm64\n"
        f"Source commit: {commit}\nBuilt: {datetime.now(timezone.utc).isoformat()}\n"
        f"Quick Start: VaultBasis-Quick-Start.html\n"
        f"Troubleshooting: VaultBasis-Troubleshooting.html\n"
        f"Evidence Contract: v0.1\nSigning: UNSIGNED (no Developer ID in build env)\n"
    )
    (pkg / "RELEASE.txt").write_text(release_txt)

    # 5. Forbidden-content sweep: artifact identity across the whole package,
    # plus claim-level sweep of the practitioner Quick Start + RELEASE.txt.
    # (Troubleshooting/Technical may reference historical RC2 filenames when
    # guiding support; the content gate already bans superseded claims there.)
    for f in pkg.rglob("*"):
        for b in ["preview-macOS", "RC1", "VaultBasis-RC1"]:
            assert b not in f.name, f"stale identity in package filename: {f.name}"
    for name in ["VaultBasis-Quick-Start.html", "RELEASE.txt"]:
        text = (pkg / name).read_text(encoding="utf-8", errors="replace")
        for b in ["Release Candidate 1", "VaultBasis Inc.", "verify standard compliance",
                  "Simulate Audits", "proves you ran", "preview-macOS"]:
            assert b not in text, f"BANNED {b!r} in package file {name}"

    # 6. Zip + hashes + candidate manifest (schema: schemas/release/manifest-v0.1.json).
    zip_path = REPO / "dist" / f"{PACKAGE_NAME}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(pkg.rglob("*")):
            if f.is_file():
                z.write(f, arcname=f"{PACKAGE_NAME}/{f.relative_to(pkg)}")
    artifact_sha = sha256_of(zip_path)

    # Candidate manifest: honest pre-qualification states. It MUST NOT validate
    # against schemas/release/manifest-v0.1.json yet (that schema's consts —
    # QUALIFIED / EQUIVALENT / PUBLICATION_VERIFIED — are earned only by the
    # frozen gates). Qualification overwrites these fields; never hand-edit.
    manifest = {
        "manifest_version": "v0.1",
        "release": {"tag": "RC3-candidate", "commit": commit, "candidate": "RC3-MAC"},
        "platform_artifact": {
            "os": "macos", "architecture": "arm64",
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
                {"control": "bundle-identity", "state": "IMPLEMENTED",
                 "evidence": "com.vaultbasis.edge in VaultBasis.app Info.plist"},
                {"control": "arch-purity-arm64", "state": "VERIFIED",
                 "evidence": f"file(1): {file_out.strip()}"},
                {"control": "developer-id-signing", "state": "PLANNED",
                 "evidence": "no Developer ID in build env"},
                {"control": "apple-notarization", "state": "PLANNED",
                 "evidence": "requires signing first"},
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
            "projection_digest_mac": "PENDING",
            "projection_digest_win": "PENDING-WIN-CANDIDATE",
            "result": "PENDING",
        },
        "qualification": {
            "distribution": "PENDING", "usability": "PENDING", "leakage_gate": "PASS",
            "result": "CANDIDATE-UNQUALIFIED",
        },
        "publication": {"endpoint": "NONE (do not distribute)", "published_artifact_sha256": artifact_sha},
        "post_publication": {"downloaded_sha256": "PENDING",
                             "matches_qualified": False,
                             "result": "NOT-VERIFIED"},
    }
    manifest_path = REPO / "dist" / f"{PACKAGE_NAME}.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"CANDIDATE: {zip_path.name}")
    print(f"SHA-256:  {artifact_sha}")
    print(f"SIZE:     {zip_path.stat().st_size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
