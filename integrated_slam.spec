# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['tools/launch_integrated_slam.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/runtime/*.py', 'app/runtime'),
        ('app/runtime/*.json', 'app/runtime'),
    ],
    hiddenimports=[
        'cv2',
        'numpy',
        'matplotlib',
        'scipy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'sklearn'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SLAM_Integrated',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
