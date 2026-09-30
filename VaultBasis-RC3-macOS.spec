# -*- mode: python ; coding: utf-8 -*-
# VaultBasis Edge RC3 macOS candidate: proper .app bundle named "VaultBasis".
# Unsigned preview build (no Developer ID in this environment) — Gatekeeper
# will still challenge first launch; the .app form fixes Finder document
# association (UAT-MAC-003) and carries bundle identity for future signing.

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('apps', 'apps'), ('apps/edge-offline-verifier', 'apps/edge-offline-verifier'), ('schemas', 'schemas'),
           ('docs/scope_and_limitations_v0.1.md', 'docs'),
           ('tests/fixtures/golden_receipt_valid.json', 'sample'),
           ('tests/fixtures/golden_receipt_tampered.json', 'sample')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # GUI / notebook / dev-toolchain leakage: the Edge server (FastAPI +
        # uvicorn + cryptography + jsonschema + pydantic) never imports these.
        # Verified by launch test after every exclude change.
        'matplotlib', 'IPython', 'tkinter', 'sphinx', 'numpy', 'pandas',
        'scipy', 'docutils',
        'Cython', 'cython', 'mypy',
        'lxml', 'bs4',
        'jupyter', 'jupyter_client', 'jupyter_core', 'ipykernel', 'ipywidgets',
        'nbformat', 'traitlets', 'tornado', 'zmq',
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'PIL',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VaultBasis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
    codesign_identity=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='VaultBasis',
)

app = BUNDLE(
    coll,
    name='VaultBasis.app',
    icon=None,
    bundle_identifier='com.vaultbasis.edge',
    version='0.1.0',
    info_plist={
        'CFBundleName': 'VaultBasis',
        'CFBundleDisplayName': 'VaultBasis',
        'CFBundleShortVersionString': '0.1.0',
        'LSMinimumSystemVersion': '14.0',
        'NSHighResolutionCapable': True,
        'NSPrincipalClass': 'NSApplication',
    },
)
