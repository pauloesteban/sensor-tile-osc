# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['metabow_bridge.py'],
    pathex=[],
    binaries=[],
    datas=[('metabow.toml', '.')],
    hiddenimports=[],
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
    name='metabow_bridge',
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
)
app = BUNDLE(
    exe,
    name='metabow_bridge.app',
    icon=None,
    bundle_identifier=None,
    version='1.5.1',
    info_plist={
        'NSBluetoothAlwaysUsageDescription': 'This app uses Bluetooth.'
    }
)
