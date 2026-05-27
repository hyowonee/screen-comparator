# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['git_analyzer.py'],
    pathex=[],
    binaries=[],
    datas=[('config.json', '.')],
    hiddenimports=['git', 'git.cmd', 'git.config', 'git.remote', 'git.index', 'openpyxl'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='screen-comparator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
