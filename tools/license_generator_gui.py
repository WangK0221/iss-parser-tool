from __future__ import annotations

import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from config import APP_NAME
from services.license_service import LicenseService


class LicenseGeneratorWindow(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master)
        self.master = master
        self.service = LicenseService()

        self.customer_var = tk.StringVar()
        self.machine_code_var = tk.StringVar()
        self.expire_at_var = tk.StringVar()
        self.output_path_var = tk.StringVar(value=str((Path.cwd() / "license.json").resolve()))

        self._setup_window()
        self._build_ui()

    def _setup_window(self) -> None:
        self.master.title(f"{APP_NAME}授权生成器")
        self.master.minsize(760, 260)
        self.pack(fill="both", expand=True, padx=12, pady=12)
        self.columnconfigure(1, weight=1)

    def _build_ui(self) -> None:
        ttk.Label(self, text="客户名称：").grid(row=0, column=0, padx=6, pady=8, sticky="e")
        ttk.Entry(self, textvariable=self.customer_var).grid(row=0, column=1, columnspan=2, padx=6, pady=8, sticky="ew")

        ttk.Label(self, text="机器码：").grid(row=1, column=0, padx=6, pady=8, sticky="e")
        ttk.Entry(self, textvariable=self.machine_code_var).grid(row=1, column=1, columnspan=2, padx=6, pady=8, sticky="ew")

        ttk.Label(self, text="到期日期：").grid(row=2, column=0, padx=6, pady=8, sticky="e")
        ttk.Entry(self, textvariable=self.expire_at_var).grid(row=2, column=1, padx=6, pady=8, sticky="ew")
        ttk.Label(self, text="格式 YYYY-MM-DD，留空表示长期").grid(row=2, column=2, padx=6, pady=8, sticky="w")

        ttk.Label(self, text="输出文件：").grid(row=3, column=0, padx=6, pady=8, sticky="e")
        ttk.Entry(self, textvariable=self.output_path_var).grid(row=3, column=1, padx=6, pady=8, sticky="ew")
        ttk.Button(self, text="选择路径", command=self.select_output_path).grid(row=3, column=2, padx=6, pady=8, sticky="w")

        button_frame = ttk.Frame(self)
        button_frame.grid(row=4, column=0, columnspan=3, sticky="w", pady=10)
        ttk.Button(button_frame, text="生成授权文件", command=self.generate_license).pack(side="left", padx=6)
        ttk.Button(button_frame, text="复制输出路径", command=self.copy_output_path).pack(side="left", padx=6)

        self.preview_text = tk.Text(self, wrap="word", height=8)
        self.preview_text.grid(row=5, column=0, columnspan=3, sticky="nsew", padx=6, pady=8)
        self.rowconfigure(5, weight=1)

    def select_output_path(self) -> None:
        path = filedialog.asksaveasfilename(
            title="保存授权文件",
            defaultextension=".json",
            initialfile="license.json",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
        )
        if path:
            self.output_path_var.set(path)

    def generate_license(self) -> None:
        customer = self.customer_var.get().strip()
        machine_code = self.machine_code_var.get().strip().upper()
        expire_at = self.expire_at_var.get().strip()
        output_path = Path(self.output_path_var.get().strip()).resolve()

        if not customer:
            messagebox.showwarning(f"{APP_NAME}授权生成器", "客户名称不能为空。")
            return
        if not machine_code:
            messagebox.showwarning(f"{APP_NAME}授权生成器", "机器码不能为空。")
            return

        data = self.service.generate_license_data(customer=customer, machine_code=machine_code, expire_at=expire_at)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert(tk.END, json.dumps(data, ensure_ascii=False, indent=2))
        messagebox.showinfo(f"{APP_NAME}授权生成器", f"授权文件已生成：\n{output_path}")

    def copy_output_path(self) -> None:
        path = self.output_path_var.get().strip()
        if not path:
            return
        self.master.clipboard_clear()
        self.master.clipboard_append(path)
