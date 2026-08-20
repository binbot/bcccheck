# PyInstaller spec for bcccheck.
# Builds a single-file executable that bundles Python + the app + Textual +
# Playwright (the browser itself is NOT bundled; it is downloaded on first run
# by bcccheck.ensure_browser). Run with:
#   uv run --with pyinstaller pyinstaller bcccheck.spec
from PyInstaller.utils.hooks import collect_all

pw_datas, pw_binaries, pw_hiddenimports = collect_all("playwright")
tx_datas, tx_binaries, tx_hiddenimports = collect_all("textual")

block_cipher = None

a = Analysis(
    ["tui.py"],
    pathex=[],
    binaries=pw_binaries + tx_binaries,
    datas=[("styles.tcss", ".")] + pw_datas + tx_datas,
    hiddenimports=pw_hiddenimports + tx_hiddenimports + ["bcccheck"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="bcccheck",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
