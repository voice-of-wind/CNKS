# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['recAndsend.py'],
    pathex=[],
    binaries=[],
    datas=[('send1.py', '.'), ('receive1.py', '.')],
    hiddenimports=['socket', 'os', 'tkinter.filedialog', 'tkinter.ttk', 'hashlib', 'time', 'threading', 'uuid', 'tkinter.messagebox', 'json'],
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
    name='recAndsend',
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
