# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_system_data_files


PYTHON_BASE = Path(sys.base_prefix)
DLL_DIR = PYTHON_BASE / "DLLs"
TCL_DIR = PYTHON_BASE / "tcl"


# Win7 包只应在 Python 3.8 x64 环境下构建，否则得到的 exe 仍然可能不兼容 Win7。
hiddenimports = [
    "tkinter",
    "tkinter.ttk",
    "tkinter.filedialog",
    "tkinter.messagebox",
    "tkinter.simpledialog",
    "tkinter.commondialog",
    "tkinter.dialog",
    "tkinter.constants",
]

binaries = [
    (str(DLL_DIR / "_tkinter.pyd"), "."),
    (str(DLL_DIR / "tcl86t.dll"), "."),
    (str(DLL_DIR / "tk86t.dll"), "."),
]

datas = []
for asset_file in Path("assets").glob("*"):
    if asset_file.is_file():
        datas.append((str(asset_file), "assets"))
datas += collect_system_data_files(str(TCL_DIR / "tcl8.6"), destdir="_tcl_data")
datas += collect_system_data_files(str(TCL_DIR / "tk8.6"), destdir="_tk_data")


a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=["pyinstaller_hooks"],
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
    name="ISSParserTool",
    icon=str(Path("assets") / "app.ico"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=["_tkinter.pyd", "tcl86t.dll", "tk86t.dll"],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
