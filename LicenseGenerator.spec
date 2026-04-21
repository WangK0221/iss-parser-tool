# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import os
import sys

from PyInstaller.utils.hooks import collect_system_data_files


PYTHON_BASE = Path(sys.base_prefix)
DLL_DIR = PYTHON_BASE / "DLLs"
TCL_DIR = PYTHON_BASE / "tcl"
SYSTEM32_DIR = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"


def _find_ucrt_redist_dir():
    candidates = [
        Path(r"C:\Program Files (x86)\Windows Kits\10\Redist\ucrt\DLLs\x64"),
        Path(r"C:\Program Files (x86)\Windows Kits\10\Redist\10.0.22621.0\ucrt\DLLs\x64"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _collect_runtime_binaries():
    runtime_binaries = []
    for candidate in [
        PYTHON_BASE / "vcruntime140.dll",
        PYTHON_BASE / "vcruntime140_1.dll",
        SYSTEM32_DIR / "msvcp140.dll",
        SYSTEM32_DIR / "concrt140.dll",
    ]:
        if candidate.exists():
            runtime_binaries.append((str(candidate), "."))

    ucrt_dir = _find_ucrt_redist_dir()
    if ucrt_dir is not None:
        for dll_file in sorted(ucrt_dir.glob("*.dll")):
            runtime_binaries.append((str(dll_file), "."))
    return runtime_binaries


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
binaries += _collect_runtime_binaries()

datas = []
datas += collect_system_data_files(str(TCL_DIR / "tcl8.6"), destdir="_tcl_data")
datas += collect_system_data_files(str(TCL_DIR / "tk8.6"), destdir="_tk_data")


a = Analysis(
    ["license_generator.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=["pyinstaller_hooks"],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="juki站位表生成工具-授权生成器",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
