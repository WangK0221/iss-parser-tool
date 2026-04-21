from __future__ import annotations

from copy import deepcopy
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from PIL import Image, ImageTk

from config import ABOUT_DIALOG_DEFAULTS, APP_NAME, BASE_DIR
from utils.file_utils import get_runtime_resource_path


class AboutDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.settings = deepcopy(ABOUT_DIALOG_DEFAULTS)
        self.image_ref: ImageTk.PhotoImage | None = None
        self._setup_window()
        self._build_ui()

    def _setup_window(self) -> None:
        width = int(self.settings.get("dialog_width", 760))
        height = int(self.settings.get("dialog_height", 430))
        self.title(str(self.settings.get("window_title", f"关于 {APP_NAME}")))
        self.geometry(f"{width}x{height}")
        self.minsize(620, 320)
        self.transient(self.master)
        self.grab_set()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def _build_ui(self) -> None:
        main = ttk.Frame(self, padding=18)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        image_frame = ttk.Frame(main)
        image_frame.grid(row=0, column=0, sticky="nsw", padx=(0, 18))
        self._build_qr_image(image_frame)

        info_frame = ttk.Frame(main)
        info_frame.grid(row=0, column=1, sticky="nsew")
        info_frame.columnconfigure(0, weight=1)

        title_value = self._info_value("产品名称") or APP_NAME
        version_value = self._info_value("版本")

        ttk.Label(
            info_frame,
            text=title_value,
            font=("Microsoft YaHei UI", 17, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        if version_value:
            ttk.Label(
                info_frame,
                text=version_value,
                font=("Microsoft YaHei UI", 10),
                foreground="#666666",
                anchor="w",
            ).grid(row=1, column=0, sticky="w", pady=(4, 14))

        detail_row = 2
        for item in self.settings.get("info_lines", []):
            label_text = str(item.get("label", "")).strip()
            value_text = str(item.get("value", "")).strip()
            if not value_text or label_text in {"产品名称", "版本"}:
                continue
            ttk.Label(
                info_frame,
                text=f"{label_text}：{value_text}",
                wraplength=330,
                justify="left",
                font=("Microsoft YaHei UI", 10),
                anchor="w",
            ).grid(row=detail_row, column=0, sticky="w", pady=(0, 8))
            detail_row += 1

        description_label = tk.Label(
            info_frame,
            text=str(self.settings.get("description", "")),
            wraplength=330,
            justify="left",
            anchor="nw",
            bg="#f6f7f9",
            fg="#4a4a4a",
            relief="solid",
            bd=1,
            padx=12,
            pady=10,
            font=("Microsoft YaHei UI", 10),
        )
        description_label.grid(row=detail_row, column=0, sticky="new", pady=(8, 0))

        ttk.Button(main, text="确定", command=self.destroy).grid(row=1, column=1, sticky="e", pady=(14, 0))

    def _build_qr_image(self, parent: ttk.Frame) -> None:
        path = self._resolve_qr_image_path(str(self.settings.get("qr_image_path", "")))
        if path is None:
            placeholder = ttk.Label(
                parent,
                text="未配置二维码图片",
                anchor="center",
                justify="center",
                relief="solid",
                width=22,
            )
            placeholder.grid(row=0, column=0, sticky="nsew")
            return

        image = Image.open(path)
        image.thumbnail((250, 250))
        self.image_ref = ImageTk.PhotoImage(image)
        label = ttk.Label(parent, image=self.image_ref, relief="solid")
        label.grid(row=0, column=0, sticky="nsew")

    def _info_value(self, label: str) -> str:
        for item in self.settings.get("info_lines", []):
            if str(item.get("label", "")).strip() == label:
                return str(item.get("value", "")).strip()
        return ""

    def _resolve_qr_image_path(self, path_text: str) -> Path | None:
        text = str(path_text or "").strip()
        if not text:
            return None

        candidate = Path(text).expanduser()
        if candidate.is_absolute():
            return candidate if candidate.exists() else None

        base_candidate = (BASE_DIR / candidate).resolve()
        if base_candidate.exists():
            return base_candidate

        runtime_candidate = get_runtime_resource_path(candidate)
        if runtime_candidate.exists():
            return runtime_candidate

        return None
