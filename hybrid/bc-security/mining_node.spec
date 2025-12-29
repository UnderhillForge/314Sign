# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['314st-mining-node.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include jaraco.text data files
        ('/usr/lib/python3/dist-packages/jaraco/text/', 'jaraco/text/'),
        # Include any other package data that might be needed
    ],
    hiddenimports=[
        'pygame',
        'cryptography',
        'cryptography.hazmat.backends',
        'cryptography.hazmat.primitives.asymmetric',
        'cryptography.hazmat.primitives.hashes',
        'cryptography.hazmat.primitives.padding',
        'cryptography.hazmat.primitives.serialization',
        'json',
        'time',
        'threading',
        'pathlib',
        'subprocess',
        'secrets',
        'hashlib',
        'socket',
        'logging',
        'argparse',
        'sys',
        'signal',
        'random'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='314st-mining-node',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulator=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
)