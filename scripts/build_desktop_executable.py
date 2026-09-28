#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import sys

def build():
    # 1. Parse strict versioning
    with open("package.json", "r") as f:
        version = json.load(f)["version"]

    system = "macOS" if sys.platform == "darwin" else ("Windows" if sys.platform == "win32" else "Linux")
    binary_name = f"VaultBasis-Edge-v{version}-{system}"

    print(f"==> Initiating VaultBasis Desktop Build for {system}")
    print(f"==> Target Binary: {binary_name}")

    # 3. PyInstaller onefile bundle (console kept for preview diagnostics;
    # signing/notarization/hardening tracked in RC3 scope, not claimed here)
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", binary_name,
        "--onefile",
        "--clean",
        "--noconfirm",
        "--exclude-module", "matplotlib",
        "--exclude-module", "IPython",
        "--exclude-module", "tkinter",
        "--exclude-module", "sphinx",
        "--exclude-module", "numpy",
        "--exclude-module", "pandas",
        "--exclude-module", "scipy",
        "--exclude-module", "docutils",
        "--add-data", f"apps{os.pathsep}apps",
        "--add-data", f"schemas{os.pathsep}schemas",
        "main.py"
    ]
    
    subprocess.run(cmd, check=True)

    # 4. Create Final Deployable Zip
    dist_dir = "dist"
    binary_path = os.path.join(dist_dir, binary_name)
    if sys.platform == "win32":
        binary_path += ".exe"

    zip_filename = f"{binary_name}-Release.zip"
    zip_path = os.path.join(dist_dir, zip_filename)

    # Zip the binary for release distribution
    import zipfile
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        info = zipfile.ZipInfo(os.path.basename(binary_path))
        
        # Read original file permissions (e.g. 0o755) and embed them in the ZIP
        st = os.stat(binary_path)
        info.external_attr = (st.st_mode & 0xFFFF) << 16
        
        with open(binary_path, 'rb') as f:
            zipf.writestr(info, f.read())
            
        # Include the Quick Start Guide HTML
        guide_path = "VaultBasis_Quick_Start_Guide.html"
        if os.path.exists(guide_path):
            zipf.write(guide_path, arcname=guide_path)

        # Include the macOS one-click launcher script (must preserve execute bit)
        launcher_path = "launch_vaultbasis.command"
        if os.path.exists(launcher_path):
            launcher_info = zipfile.ZipInfo(launcher_path)
            lst = os.stat(launcher_path)
            launcher_info.external_attr = (lst.st_mode & 0xFFFF) << 16
            with open(launcher_path, 'rb') as lf:
                zipf.writestr(launcher_info, lf.read())

    print(f"==> SUCCESS: Created deployable artifact -> {zip_path}")

if __name__ == "__main__":
    build()
