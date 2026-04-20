from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from config import CUSTOMER_EXPORT_FIELD_LABELS
from utils.export_settings import (
    default_customer_export_settings,
    load_customer_export_settings,
    save_customer_export_settings,
)


class ExportSettingsDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, on_saved: Callable[[], None] | None = None) -> None:
        super().__init__(master)
        self.on_saved = on_saved
        self.items: list[dict[str, str]] = []
        self.layout_vars: dict[str, tk.Variable] = {}
        self.station_number_mapping_items: list[str] = []
        self.station_number_mapping_var = tk.StringVar()
        self.station_number_mapping_listbox: tk.Listbox | None = None
        self.rows_frame: ttk.Frame | None = None
        self._load_settings()
        self._setup_window()
        self._build_ui()
        self._render_rows()

    def _setup_window(self) -> None:
        self.title("表头设置")
        self.minsize(720, 380)
        self.transient(self.master)
        self.grab_set()

    def _build_ui(self) -> None:
        main = ttk.Frame(self, padding=12)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(3, weight=1)

        ttk.Label(
            main,
            text="可修改表头名称、列顺序，以及线体/机台显示与分组分割方式。线体值留空时自动识别。",
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        layout_frame = ttk.LabelFrame(main, text="版式配置")
        layout_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        for column in range(5):
            layout_frame.columnconfigure(column, weight=1 if column in {1, 3} else 0)

        ttk.Label(layout_frame, text="线体名称：").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        self.layout_vars["line_label"] = tk.StringVar(value=self.layout["line_label"])
        ttk.Entry(layout_frame, textvariable=self.layout_vars["line_label"], width=12).grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        ttk.Label(layout_frame, text="线体值：").grid(row=0, column=2, padx=6, pady=6, sticky="e")
        self.layout_vars["line_value"] = tk.StringVar(value=self.layout["line_value"])
        ttk.Entry(layout_frame, textvariable=self.layout_vars["line_value"], width=12).grid(row=0, column=3, padx=6, pady=6, sticky="ew")
        ttk.Label(layout_frame, text="留空则自动识别").grid(row=0, column=4, padx=6, pady=6, sticky="w")

        ttk.Label(layout_frame, text="机台名称：").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        self.layout_vars["machine_label"] = tk.StringVar(value=self.layout["machine_label"])
        ttk.Entry(layout_frame, textvariable=self.layout_vars["machine_label"], width=12).grid(row=1, column=1, padx=6, pady=6, sticky="ew")

        self.layout_vars["split_by_station_group"] = tk.BooleanVar(value=self.layout["split_by_station_group"])
        ttk.Checkbutton(
            layout_frame,
            text="同机台内 F/R/MTS 切换时重复标题与表头",
            variable=self.layout_vars["split_by_station_group"],
        ).grid(row=1, column=2, columnspan=2, padx=6, pady=6, sticky="w")

        padding_frame = ttk.LabelFrame(main, text="101-128 映射机器配置")
        padding_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        padding_frame.columnconfigure(0, weight=1)

        ttk.Label(
            padding_frame,
            text="命中列表中的机台时，LF/RF/LR/RR 的站位编号按 101-128 规则转换：1~9 => 101~109，10~28 => 110~128。默认内置 RX-7、RX-8。",
        ).grid(row=0, column=0, columnspan=2, padx=8, pady=(8, 4), sticky="w")

        list_frame = ttk.Frame(padding_frame)
        list_frame.grid(row=1, column=0, padx=8, pady=8, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        padding_frame.rowconfigure(1, weight=1)

        self.station_number_mapping_listbox = tk.Listbox(list_frame, height=5, exportselection=False)
        self.station_number_mapping_listbox.grid(row=0, column=0, sticky="nsew")
        padding_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.station_number_mapping_listbox.yview)
        padding_scrollbar.grid(row=0, column=1, sticky="ns")
        self.station_number_mapping_listbox.configure(yscrollcommand=padding_scrollbar.set)

        action_frame = ttk.Frame(padding_frame)
        action_frame.grid(row=1, column=1, padx=(0, 8), pady=8, sticky="ns")
        ttk.Entry(action_frame, textvariable=self.station_number_mapping_var, width=18).pack(fill="x", pady=(0, 6))
        ttk.Button(action_frame, text="添加", command=self.add_station_number_mapping_machine).pack(fill="x", pady=(0, 6))
        ttk.Button(action_frame, text="删除选中", command=self.remove_station_number_mapping_machine).pack(fill="x")

        self._render_station_number_mapping_list()

        container = ttk.Frame(main)
        container.grid(row=3, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        canvas = tk.Canvas(container, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        self.rows_frame = ttk.Frame(canvas)
        window_id = canvas.create_window((0, 0), window=self.rows_frame, anchor="nw")
        self.rows_frame.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(window_id, width=event.width),
        )

        button_frame = ttk.Frame(main)
        button_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(button_frame, text="恢复默认", command=self.reset_defaults).pack(side="left", padx=6)
        ttk.Button(button_frame, text="保存设置", command=self.save_settings).pack(side="right", padx=6)
        ttk.Button(button_frame, text="关闭", command=self.destroy).pack(side="right", padx=6)

    def _load_settings(self) -> None:
        settings = load_customer_export_settings()
        self.layout = dict(settings.get("layout", {}))
        station_number_mapping = settings.get("station_number_mapping", {})
        if not station_number_mapping and "station_padding" in settings:
            station_number_mapping = settings.get("station_padding", {})
        self.station_number_mapping_items = list(station_number_mapping.get("enabled_machine_patterns", []))
        self.items = [
            {"field": field, "header": settings["headers"].get(field, CUSTOMER_EXPORT_FIELD_LABELS[field])}
            for field in settings["fields"]
        ]

    def _render_station_number_mapping_list(self) -> None:
        if self.station_number_mapping_listbox is None:
            return
        self.station_number_mapping_listbox.delete(0, tk.END)
        for item in self.station_number_mapping_items:
            self.station_number_mapping_listbox.insert(tk.END, item)

    def add_station_number_mapping_machine(self) -> None:
        text = self.station_number_mapping_var.get().strip()
        if not text:
            return
        if text not in self.station_number_mapping_items:
            self.station_number_mapping_items.append(text)
            self._render_station_number_mapping_list()
        self.station_number_mapping_var.set("")

    def remove_station_number_mapping_machine(self) -> None:
        if self.station_number_mapping_listbox is None:
            return
        indexes = list(self.station_number_mapping_listbox.curselection())
        if not indexes:
            return
        for index in reversed(indexes):
            if 0 <= index < len(self.station_number_mapping_items):
                self.station_number_mapping_items.pop(index)
        self._render_station_number_mapping_list()

    def _render_rows(self) -> None:
        if self.rows_frame is None:
            return

        for child in self.rows_frame.winfo_children():
            child.destroy()

        ttk.Label(self.rows_frame, text="字段", width=18).grid(row=0, column=0, padx=6, pady=6, sticky="w")
        ttk.Label(self.rows_frame, text="表头名称", width=24).grid(row=0, column=1, padx=6, pady=6, sticky="w")
        ttk.Label(self.rows_frame, text="顺序调整", width=20).grid(row=0, column=2, padx=6, pady=6, sticky="w")

        for index, item in enumerate(self.items, start=1):
            ttk.Label(self.rows_frame, text=CUSTOMER_EXPORT_FIELD_LABELS[item["field"]]).grid(
                row=index,
                column=0,
                padx=6,
                pady=6,
                sticky="w",
            )

            header_var = tk.StringVar(value=item["header"])
            entry = ttk.Entry(self.rows_frame, textvariable=header_var, width=28)
            entry.grid(row=index, column=1, padx=6, pady=6, sticky="ew")
            header_var.trace_add("write", lambda *_args, idx=index - 1, var=header_var: self._update_header(idx, var.get()))

            action_frame = ttk.Frame(self.rows_frame)
            action_frame.grid(row=index, column=2, padx=6, pady=6, sticky="w")
            ttk.Button(action_frame, text="上移", command=lambda idx=index - 1: self.move_up(idx)).pack(side="left", padx=(0, 4))
            ttk.Button(action_frame, text="下移", command=lambda idx=index - 1: self.move_down(idx)).pack(side="left")

        self.rows_frame.columnconfigure(1, weight=1)

    def _update_header(self, index: int, value: str) -> None:
        self.items[index]["header"] = value

    def move_up(self, index: int) -> None:
        if index <= 0:
            return
        self.items[index - 1], self.items[index] = self.items[index], self.items[index - 1]
        self._render_rows()

    def move_down(self, index: int) -> None:
        if index >= len(self.items) - 1:
            return
        self.items[index + 1], self.items[index] = self.items[index], self.items[index + 1]
        self._render_rows()

    def reset_defaults(self) -> None:
        defaults = default_customer_export_settings()
        self.layout = dict(defaults["layout"])
        for key, var in self.layout_vars.items():
            var.set(self.layout[key])
        self.items = [
            {"field": field, "header": defaults["headers"][field]}
            for field in defaults["fields"]
        ]
        self.station_number_mapping_items = list(defaults["station_number_mapping"]["enabled_machine_patterns"])
        self.station_number_mapping_var.set("")
        self._render_station_number_mapping_list()
        self._render_rows()

    def save_settings(self) -> None:
        headers = {}
        fields = []
        for item in self.items:
            header = str(item["header"]).strip()
            if not header:
                messagebox.showwarning("表头设置", f"{CUSTOMER_EXPORT_FIELD_LABELS[item['field']]} 的表头不能为空。")
                return
            fields.append(item["field"])
            headers[item["field"]] = header

        layout = {
            "line_label": str(self.layout_vars["line_label"].get()).strip(),
            "line_value": str(self.layout_vars["line_value"].get()).strip(),
            "machine_label": str(self.layout_vars["machine_label"].get()).strip(),
            "split_by_station_group": bool(self.layout_vars["split_by_station_group"].get()),
        }
        if not layout["line_label"] or not layout["machine_label"]:
            messagebox.showwarning("表头设置", "线体名称和机台名称不能为空。")
            return

        save_customer_export_settings(
            {
                "fields": fields,
                "headers": headers,
                "layout": layout,
                "station_number_mapping": {
                    "enabled_machine_patterns": list(self.station_number_mapping_items),
                },
            }
        )
        if self.on_saved:
            self.on_saved()
        messagebox.showinfo("表头设置", "设置已保存。")
        self.destroy()
