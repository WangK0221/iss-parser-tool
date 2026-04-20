from __future__ import annotations

from pathlib import Path
import sys
from typing import Iterable

from config import SUPPORTED_EXTENSIONS


def normalize_path(path_text: str) -> Path:
    return Path(path_text).expanduser().resolve()


def is_iss_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS


def scan_iss_files(paths: Iterable[str], folder: str | None = None) -> list[Path]:
    """收集用户选择的文件与文件夹中的 .iss 文件。"""
    result: list[Path] = []
    seen: set[str] = set()

    for item in paths:
        if not item:
            continue
        path = normalize_path(item)
        if is_iss_file(path):
            key = str(path).lower()
            if key not in seen:
                seen.add(key)
                result.append(path)

    if folder:
        folder_path = normalize_path(folder)
        if folder_path.is_dir():
            for path in sorted(folder_path.rglob("*")):
                if is_iss_file(path):
                    key = str(path).lower()
                    if key not in seen:
                        seen.add(key)
                        result.append(path)

    return sorted(result)


def ensure_directory(path_text: str | Path) -> Path:
    path = Path(path_text).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_runtime_resource_path(relative_path: str | Path) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return (base_path / relative_path).resolve()
