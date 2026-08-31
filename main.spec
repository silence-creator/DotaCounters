# -*- mode: python ; coding: utf-8 -*-
import re

# Версия берётся из единственного места, где она объявлена, чтобы имя .exe
# не приходилось править отдельно при каждом релизе.
with open('dotacounters/version.py', encoding='utf-8') as _f:
    APP_VERSION = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', _f.read()).group(1)


a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
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
    name=f'DotaCounters{APP_VERSION}',
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
    icon=['icon.png'],
)
