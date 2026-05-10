# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

qt_themes_datas = collect_data_files('qt_themes')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('classes', 'classes/'), ('utils', 'utils/'), ('assets', 'assets/')] + qt_themes_datas,
    hiddenimports=['qt_themes'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PipCamPortable',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\pipcam_icon.ico'],
)
