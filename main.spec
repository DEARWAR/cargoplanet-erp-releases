# -*- mode: python ; coding: utf-8 -*-
# Folder build (not one-file): faster start-up and a proper installer.
import os
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('customtkinter') + collect_data_files('tkcalendar')
for f in ('company logo.jpeg', 'full_header.png', 'full laser.png', 'login_bg.jpg'):
    if os.path.exists(f):
        datas.append((f, '.'))
if os.path.isdir('backgrounds'):
    datas.append(('backgrounds', 'backgrounds'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['libsql', 'libsql_experimental', 'babel.numbers', 'updater', 'yard_ui'],
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
    [],
    exclude_binaries=True,
    name='CargoPlanetERP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX makes antivirus false-alarms more likely
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False, upx=False, name='CargoPlanetERP',
)
