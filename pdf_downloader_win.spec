# -*- mode: python ; coding: utf-8 -*-
# Windows版本PyInstaller配置文件

import sys
from pathlib import Path

a = Analysis(
    ['pdf_downloader.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('test_urls.xlsx', '.'),
        ('urls.xlsx', '.'),
    ],
    hiddenimports=[
        'pandas',
        'openpyxl',
        'requests',
        'urllib3',
        'charset_normalizer',
        'certifi',
        'numpy',
        'pytz',
        'dateutil',
        'et_xmlfile',
    ],
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
    name='PDF下载器',
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
    icon=None,
    version_file=None,
) 