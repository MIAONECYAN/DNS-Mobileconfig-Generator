# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    datas=[
        ('translations/en.qm', 'translations'),
        ('translations/ja.qm', 'translations'),
        ('translations/zh_TW.qm', 'translations'),
    ],
    scripts=['dns_config_generator.py'],
    pathex=[],
    binaries=[],
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
    name='dns_config_generator',
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
    name='dns_config_generator.app',
    icon=None,
    bundle_identifier=None,
)
