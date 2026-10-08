#!/usr/bin/env python3
"""
VaultBasis Windows Setup Installer (VaultBasis-Setup.exe)
Single-file self-extracting installer for VaultBasis Edge on Windows.
Conforms to:
- MMP15-DIST-WIN-FIRST-RUN-001: Robust Windows installation & zero DLL crash
- MMP15-WIN-INSTALL-LICENSE-001: Professional Desktop/Start Menu shortcut & clean %LOCALAPPDATA% extraction
"""
import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

def create_shortcut(target_exe: str, shortcut_path: str, icon_path: str, description: str = "VaultBasis Edge"):
    """Creates a Windows .lnk shortcut via PowerShell COM interface without external python modules."""
    ps_cmd = f"""
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
    $Shortcut.TargetPath = '{target_exe}'
    $Shortcut.WorkingDirectory = '{os.path.dirname(target_exe)}'
    $Shortcut.Description = '{description}'
    $Shortcut.IconLocation = '{icon_path},0'
    $Shortcut.Save()
    """
    try:
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd], check=True, capture_output=True)
    except Exception as e:
        print(f"Warning: Failed to create shortcut at {shortcut_path}: {e}")

def main():
    # 1. Target directory: %LOCALAPPDATA%\\VaultBasis
    local_app_data = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~\\AppData\\Local")
    install_dir = Path(local_app_data) / "VaultBasis"
    install_dir.mkdir(parents=True, exist_ok=True)

    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    bundle_zip = base_dir / "vaultbasis_app.zip"
    
    if bundle_zip.is_file():
        with zipfile.ZipFile(bundle_zip, 'r') as zf:
            for member in zf.infolist():
                member_path = Path(os.path.normpath(os.path.join(install_dir, member.filename)))
                if not str(member_path).startswith(str(install_dir.resolve())):
                    raise ValueError(f"ZIP slip blocked: {member.filename!r} resolves outside install dir")
                zf.extract(member, install_dir)
    elif (base_dir / "VaultBasis").is_dir():
        shutil.copytree(base_dir / "VaultBasis", install_dir, dirs_exist_ok=True)
    
    exe_path = install_dir / "VaultBasis.exe"
    icon_path = str(exe_path)

    # 2. Desktop Shortcut
    user_profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    desktop_dir = Path(user_profile) / "Desktop"
    if desktop_dir.is_dir():
        desktop_shortcut = desktop_dir / "VaultBasis.lnk"
        create_shortcut(str(exe_path), str(desktop_shortcut), icon_path, "VaultBasis Edge — Tax Reconciliation")

    # 3. Start Menu Shortcut
    app_data = os.environ.get("APPDATA") or os.path.expanduser("~\\AppData\\Roaming")
    start_menu_dir = Path(app_data) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    start_menu_dir.mkdir(parents=True, exist_ok=True)
    start_menu_shortcut = start_menu_dir / "VaultBasis.lnk"
    create_shortcut(str(exe_path), str(start_menu_shortcut), icon_path, "VaultBasis Edge — Tax Reconciliation")

    # 4. Windows Settings -> Installed Apps Registry Entry (HKCU)
    reg_cmd = f"""
    $RegPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\VaultBasis"
    if (!(Test-Path $RegPath)) {{
        New-Item -Path $RegPath -Force | Out-Null
    }}
    Set-ItemProperty -Path $RegPath -Name "DisplayName" -Value "VaultBasis Edge"
    Set-ItemProperty -Path $RegPath -Name "DisplayVersion" -Value "1.5.0-rc3"
    Set-ItemProperty -Path $RegPath -Name "Publisher" -Value "VaultBasis"
    Set-ItemProperty -Path $RegPath -Name "DisplayIcon" -Value "{exe_path},0"
    Set-ItemProperty -Path $RegPath -Name "InstallLocation" -Value "{install_dir}"
    Set-ItemProperty -Path $RegPath -Name "UninstallString" -Value 'powershell -NoProfile -WindowStyle Hidden -Command "& {{ $d = \"{install_dir}\"; Remove-Item -Force \"$d\\VaultBasis.exe\" -ErrorAction SilentlyContinue; Remove-Item -Recurse -Force \"$d\\_internal\" -ErrorAction SilentlyContinue; Remove-Item -Force \"{desktop_shortcut}\" -ErrorAction SilentlyContinue; Remove-Item -Force \"{start_menu_shortcut}\" -ErrorAction SilentlyContinue; Remove-Item -Recurse -Force \"HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\VaultBasis\" -ErrorAction SilentlyContinue; Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show(\"VaultBasis has been uninstalled. Your evidence cases, receipts, and signing keys in $d have been preserved. You may delete this folder manually if you no longer need them.\", \"VaultBasis Uninstalled\") }}"'
    """
    try:
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", reg_cmd], check=False, capture_output=True)
    except Exception as e:
        print(f"Warning: Failed to write uninstall registry key: {e}")

    # 5. Launch VaultBasis Edge
    if exe_path.is_file():
        subprocess.Popen([str(exe_path)], cwd=str(install_dir))

if __name__ == "__main__":
    main()
