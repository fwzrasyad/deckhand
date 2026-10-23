# PyInstaller spec for the Deckhand daemon (SRD 13.2).
#
# Build with:  make package-daemon
# Output:      daemon/dist/deckhand/  (single-folder bundle, no console window on Windows)
#
# Run this from the daemon/ directory so the relative paths resolve.

from pathlib import Path

import sys

spec_dir = Path(SPECPATH)
src_dir = spec_dir / "src"

block_cipher = None

a = Analysis(
    [str(src_dir / "deckhand" / "__main__.py")],
    pathex=[str(src_dir)],
    binaries=[],
    datas=[
        (str(src_dir / "deckhand" / "tray" / "assets"), "deckhand/tray/assets"),
    ],
    hiddenimports=[
        "deckhand.cli.main",
        "deckhand.platform.windows",
        "deckhand.platform.linux",
        "deckhand.platform.macos",
        "deckhand.process.posix",
        "deckhand.process.windows",
        "deckhand.telemetry.providers.psutil_provider",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "pytest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="deckhand",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False if sys.platform == "win32" else True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="deckhand",
)
