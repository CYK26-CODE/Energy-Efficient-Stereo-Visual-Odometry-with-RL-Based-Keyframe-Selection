# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for SLAM System
Creates standalone .exe with all dependencies
"""

block_cipher = None

# Collect all data files
datas = [
    ('app/runtime/*.py', 'app/runtime'),
    ('app/frontend/*.py', 'app/frontend'),
]

# Hidden imports (modules not auto-detected)
hiddenimports = [
    'cv2',
    'numpy',
    'matplotlib',
    'customtkinter',
    'tkinter',
    'PIL',
    'scipy',
    'sklearn',
    'json',
    'threading',
    'queue',
    'collections',
]

a = Analysis(
    ['tools/launch_slam.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='SLAM_System',
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
    icon=None  # Add icon='slam_icon.ico' if you have an icon file
)
