# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_system_data_files


PYTHON_BASE = Path(sys.base_prefix)
DLL_DIR = PYTHON_BASE / "DLLs"
TCL_DIR = PYTHON_BASE / "tcl"


# 显式收集 tkinter 及其运行时依赖，避免 PyInstaller 自动探测失效时漏包。
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
datas.append((str(Path("assets") / "app.ico"), "assets"))
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
    name="ISSParserTool_v5_win10_win11",
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
