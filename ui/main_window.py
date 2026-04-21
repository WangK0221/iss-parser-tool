from __future__ import annotations

import os
import re
import threading
import tkinter as tk
from pathlib import Path
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from config import APP_NAME, APP_VERSION, DEFAULT_EXPORT_OPTIONS, DEFAULT_OUTPUT_DIR, WINDOW_MIN_SIZE
from iss_parser_core.iss_parser import IssParser
from services.data_mapper import DataMapper
from services.excel_exporter import ExcelExporter
from services.license_service import LicenseService
from ui.about_dialog import AboutDialog
from ui.export_settings_dialog import ExportSettingsDialog
from utils.file_utils import ensure_directory, get_runtime_resource_path, scan_iss_files
from utils.logger import get_logger

logger = get_logger("ui")


class MainWindow(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master)
        self.master = master
        self.parser = IssParser()
        self.mapper = DataMapper()
        self.exporter = ExcelExporter()
        self.license_service = LicenseService()

        self.selected_files: list[str] = []
        self.selected_folder = tk.StringVar()
        self.selected_source_var = tk.StringVar()
        self.output_dir = tk.StringVar(value=str(DEFAULT_OUTPUT_DIR))
        self.option_vars = {key: tk.BooleanVar(value=value) for key, value in DEFAULT_EXPORT_OPTIONS.items()}
        self.is_processing = False
        self.machine_code_var = tk.StringVar()
        self.license_status_var = tk.StringVar()
        self.license_detail_var = tk.StringVar()

        self._setup_window()
        self._build_ui()
        self.refresh_license_status()

    def _setup_window(self) -> None:
        self.master.title(f"{APP_NAME} v{APP_VERSION}")
        self.master.minsize(*WINDOW_MIN_SIZE)
        self.master.geometry("1220x900")
        self._apply_window_icon()
        self._setup_styles()
        self.pack(fill="both", expand=True)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

    def _apply_window_icon(self) -> None:
        icon_path = get_runtime_resource_path(Path("assets") / "app.ico")
        if not icon_path.exists():
            return
        try:
            self.master.iconbitmap(str(icon_path))
        except Exception:
            logger.warning("窗口图标加载失败: %s", icon_path, exc_info=True)

    def _setup_styles(self) -> None:
        style = ttk.Style()
        style.configure("Action.TButton", padding=(16, 10), font=("Microsoft YaHei UI", 11, "bold"))
        style.configure("Secondary.TButton", padding=(12, 7), font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Compact.TButton", padding=(8, 6), font=("Microsoft YaHei UI", 10))

    def _build_ui(self) -> None:
        self._build_license_section()
        self._build_file_section()
        self._build_output_section()
        self._build_option_section()
        self._build_log_section()

    def _build_license_section(self) -> None:
        frame = ttk.LabelFrame(self, text="授权信息")
        frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(4, weight=1)

        ttk.Label(frame, text="机器码：").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        ttk.Entry(frame, textvariable=self.machine_code_var, state="readonly").grid(row=0, column=1, padx=6, pady=6, sticky="ew")
        ttk.Button(frame, text="复制机器码", command=self.copy_machine_code, style="Compact.TButton").grid(row=0, column=2, padx=6, pady=6)
        ttk.Button(frame, text="导入授权文件", command=self.import_license, style="Compact.TButton").grid(row=0, column=3, padx=6, pady=6, sticky="w")
        about_button_frame = ttk.Frame(frame)
        about_button_frame.grid(row=0, column=4, padx=6, pady=6, sticky="e")
        ttk.Button(about_button_frame, text="关于", command=self.open_about_dialog, style="Compact.TButton").pack(side="left")

        ttk.Label(frame, text="状态：").grid(row=1, column=0, padx=6, pady=4, sticky="e")
        self.status_value_label = tk.Label(frame, textvariable=self.license_status_var, anchor="w")
        self.status_value_label.grid(row=1, column=1, padx=6, pady=4, sticky="w")
        self.license_detail_label = tk.Label(frame, textvariable=self.license_detail_var, anchor="w")
        self.license_detail_label.grid(row=1, column=2, columnspan=3, padx=6, pady=4, sticky="w")

    def _build_file_section(self) -> None:
        frame = ttk.LabelFrame(self, text="文件选择")
        frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        for column in range(7):
            frame.columnconfigure(column, weight=1 if column == 5 else 0)
        frame.rowconfigure(2, weight=1)

        ttk.Button(frame, text="选择 .iss 文件", command=self.select_files, style="Compact.TButton").grid(row=0, column=0, padx=6, pady=8, sticky="w")
        ttk.Button(frame, text="选择文件夹", command=self.select_folder, style="Compact.TButton").grid(row=0, column=1, padx=6, pady=8, sticky="w")

        ttk.Button(frame, text="表头设置", command=self.open_export_settings, style="Compact.TButton").grid(row=0, column=2, padx=6, pady=8, sticky="w")
        ttk.Button(frame, text="清空文件", command=self.clear_files, style="Compact.TButton").grid(row=0, column=3, padx=6, pady=8, sticky="w")
        ttk.Button(frame, text="移除选中", command=self.remove_selected_files, style="Compact.TButton").grid(row=0, column=4, padx=6, pady=8, sticky="w")

        self.start_button = tk.Button(
            frame,
            text="生成站位表",
            command=self.start_processing,
            font=("Microsoft YaHei UI", 11, "bold"),
            bg="#1677ff",
            fg="white",
            activebackground="#0f5ec7",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=18,
            pady=10,
            cursor="hand2",
        )
        self.start_button.grid(row=0, column=6, padx=(16, 6), pady=8, sticky="e")

        ttk.Label(frame, text="已选路径：").grid(row=1, column=0, padx=6, pady=(0, 6), sticky="e")
        selected_entry = ttk.Entry(frame, textvariable=self.selected_source_var, state="readonly", justify="left")
        selected_entry.grid(row=1, column=1, columnspan=6, padx=6, pady=(0, 6), sticky="ew")

        self.file_listbox = tk.Listbox(frame, height=8)
        self.file_listbox.grid(row=2, column=0, columnspan=7, padx=6, pady=(0, 8), sticky="nsew")

    def _build_output_section(self) -> None:
        frame = ttk.LabelFrame(self, text="导出目录")
        frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="目录：").grid(row=0, column=0, padx=6, pady=6)
        output_entry = ttk.Entry(frame, textvariable=self.output_dir, state="readonly")
        output_entry.grid(row=0, column=1, padx=6, pady=6, sticky="ew")
        output_entry.bind("<Double-Button-1>", lambda _event: self.open_output_dir())
        ttk.Button(frame, text="选择目录", command=self.select_output_dir, style="Compact.TButton").grid(row=0, column=2, padx=6, pady=6)

    def _build_option_section(self) -> None:
        frame = ttk.LabelFrame(self, text="导出选项")
        frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        for column in range(3):
            frame.columnconfigure(column, weight=1)

        groups = [
            ("导出方式", [("split_by_file", "按文件分别导出"), ("merge_export", "合并导出")]),
            ("主输出", [("export_components", "导出元件明细"), ("export_stations", "导出站位明细"), ("export_placements", "导出位号明细"), ("export_summary", "导出汇总表")]),
            ("调试", [("export_raw", "导出原始解析中间表")]),
        ]

        for column_index, (group_title, options) in enumerate(groups):
            group_frame = ttk.LabelFrame(frame, text=group_title)
            group_frame.grid(row=0, column=column_index, padx=6, pady=6, sticky="nsew")
            for row_index, (key, label) in enumerate(options):
                ttk.Checkbutton(group_frame, text=label, variable=self.option_vars[key]).grid(
                    row=row_index,
                    column=0,
                    padx=8,
                    pady=4,
                    sticky="w",
                )

    def _build_log_section(self) -> None:
        frame = ttk.LabelFrame(self, text="日志输出")
        frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=(5, 10))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        tool_frame = ttk.Frame(frame)
        tool_frame.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 0))
        ttk.Button(tool_frame, text="打开导出目录", command=self.open_output_dir, style="Secondary.TButton").pack(side="left", padx=(0, 6))
        ttk.Button(tool_frame, text="清空日志", command=self.clear_log, style="Secondary.TButton").pack(side="left")

        self.log_text = tk.Text(
            frame,
            wrap="word",
            height=14,
            font=("Consolas", 10),
            bg="#fbfbfc",
            fg="#1f1f1f",
            insertbackground="#1f1f1f",
            relief="solid",
            bd=1,
            padx=8,
            pady=6,
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=6)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.tag_configure("timestamp", foreground="#6b7280")
        self.log_text.tag_configure("info", foreground="#111827")
        self.log_text.tag_configure("success", foreground="#0f766e")
        self.log_text.tag_configure("warning", foreground="#b45309")
        self.log_text.tag_configure("error", foreground="#b91c1c")
        self.log_text.tag_configure("dim", foreground="#4b5563")

    def refresh_license_status(self) -> None:
        status = self.license_service.check_license()
        self.machine_code_var.set(status.machine_code)
        self.license_status_var.set(status.message)
        if status.valid:
            detail = f"客户: {status.customer or '未填写'}"
            if status.expire_at:
                detail += f" | 到期: {status.expire_at}"
            if status.license_path:
                detail += f" | 授权文件: {status.license_path}"
            self.start_button.configure(state="normal", bg="#1677ff", activebackground="#0f5ec7")
            self.status_value_label.configure(fg="#0b7a0b")
        else:
            detail = "将 license.json 放到程序同目录，或点击“导入授权文件”"
            self.start_button.configure(state="disabled", bg="#bfbfbf", activebackground="#bfbfbf")
            self.status_value_label.configure(fg="#c62828")
        self.license_detail_var.set(detail)
        self.license_detail_label.configure(fg="#404040")

    def copy_machine_code(self) -> None:
        code = self.machine_code_var.get().strip()
        if not code:
            return
        self.master.clipboard_clear()
        self.master.clipboard_append(code)
        self.append_log("机器码已复制到剪贴板。")

    def import_license(self) -> None:
        file_path = filedialog.askopenfilename(title="选择授权文件", filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")])
        if not file_path:
            return
        try:
            status = self.license_service.install_license(file_path)
            self.refresh_license_status()
            if status.valid:
                self.append_log(f"授权导入成功。客户: {status.customer} 到期: {status.expire_at or '长期'}")
                messagebox.showinfo(APP_NAME, "授权导入成功。下次可直接将 license.json 放到程序同目录自动识别。")
            else:
                self.append_log(f"[ERROR] 授权导入后校验失败: {status.message}")
                messagebox.showerror(APP_NAME, status.message)
        except Exception as exc:
            logger.exception("导入授权失败")
            self.append_log(f"[ERROR] 导入授权失败: {exc}")
            messagebox.showerror(APP_NAME, f"导入授权失败: {exc}")

    def open_export_settings(self) -> None:
        ExportSettingsDialog(self.master, on_saved=lambda: self.append_log("表头设置已更新。"))

    def open_about_dialog(self) -> None:
        AboutDialog(self.master)

    def select_files(self) -> None:
        files = filedialog.askopenfilenames(title="选择 .iss 文件", filetypes=[("ISS 文件", "*.iss"), ("所有文件", "*.*")])
        if not files:
            return
        self.selected_folder.set("")
        self.selected_files = sorted(set([*self.selected_files, *files]))
        self._refresh_file_list()
        self.append_log(f"已选择文件 {len(files)} 个。")

    def select_folder(self) -> None:
        folder = filedialog.askdirectory(title="选择包含 .iss 文件的文件夹")
        if folder:
            self.selected_folder.set(folder)
            self.selected_files = []
            self._refresh_file_list()
            self.append_log(f"已选择文件夹：{folder}")

    def select_output_dir(self) -> None:
        folder = filedialog.askdirectory(title="选择导出目录")
        if folder:
            self.output_dir.set(folder)
            self.append_log(f"导出目录已设置为：{folder}")

    def clear_files(self) -> None:
        self.selected_files = []
        self.selected_folder.set("")
        self._refresh_file_list()
        self.append_log("已清空已选文件。")

    def remove_selected_files(self) -> None:
        indexes = list(self.file_listbox.curselection())
        if not indexes:
            return
        for index in reversed(indexes):
            if 0 <= index < len(self.selected_files):
                self.selected_files.pop(index)
        self._refresh_file_list()
        self.append_log("已移除选中文件。")

    def clear_log(self) -> None:
        self.log_text.delete("1.0", tk.END)

    def open_output_dir(self) -> None:
        os.startfile(ensure_directory(self.output_dir.get()))

    def append_log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        tag = self._resolve_log_tag(message)
        self.log_text.insert(tk.END, f"[{timestamp}] ", ("timestamp",))
        self.log_text.insert(tk.END, message, (tag,))
        self.log_text.insert(tk.END, "\n")
        self.log_text.see(tk.END)
        logger.info(message)

    def _refresh_file_list(self) -> None:
        self.file_listbox.delete(0, tk.END)
        if self.selected_folder.get().strip():
            self.file_listbox.insert(tk.END, f"[文件夹] {self.selected_folder.get().strip()}")
        for file_path in self.selected_files:
            self.file_listbox.insert(tk.END, self._format_file_display(file_path))
        self._update_selected_source_display()

    def _update_selected_source_display(self) -> None:
        if self.selected_folder.get().strip():
            self.selected_source_var.set(self.selected_folder.get().strip())
            return
        if not self.selected_files:
            self.selected_source_var.set("")
            return
        if len(self.selected_files) == 1:
            self.selected_source_var.set(self.selected_files[0])
            return
        self.selected_source_var.set(f"已选择 {len(self.selected_files)} 个文件")

    def _format_file_display(self, file_path: str) -> str:
        path = Path(file_path)
        stem = path.stem
        side_match = re.search(r"(TOP|BOT)", stem, flags=re.IGNORECASE)
        side = side_match.group(1).upper() if side_match else "--"
        return f"[{side}] {path.name}"

    def _resolve_log_tag(self, message: str) -> str:
        upper_text = message.upper()
        if "[ERROR]" in upper_text or "失败" in message or "异常" in message:
            return "error"
        if "[WARNING]" in upper_text or "警告" in message:
            return "warning"
        if "成功" in message or "已导出" in message or "已生成" in message:
            return "success"
        if "开始" in message or "解析完成" in message or "处理结束" in message:
            return "info"
        return "dim"

    def start_processing(self) -> None:
        if self.is_processing:
            return
        status = self.license_service.check_license()
        self.refresh_license_status()
        if not status.valid:
            messagebox.showwarning(APP_NAME, f"未授权，无法继续。\n{status.message}")
            return
        self.is_processing = True
        self.start_button.configure(state="disabled", bg="#bfbfbf", activebackground="#bfbfbf")
        threading.Thread(target=self._process_files, daemon=True).start()

    def _process_files(self) -> None:
        try:
            files = scan_iss_files(self.selected_files, self.selected_folder.get())
            if not files:
                self._ui_call(lambda: messagebox.showwarning(APP_NAME, "未找到可处理的 .iss 文件。"))
                return

            output_dir = ensure_directory(self.output_dir.get())
            options = {key: var.get() for key, var in self.option_vars.items()}
            if not any([options["export_components"], options["export_stations"], options["export_placements"], options["export_summary"], options["export_raw"]]):
                self._ui_call(lambda: messagebox.showwarning(APP_NAME, "至少需要勾选一个导出内容。"))
                return

            mapped_results = []
            success_exports: list[Path] = []
            error_count = 0

            for file_path in files:
                self._ui_call(lambda p=file_path: self.append_log(f"开始解析：{p.name}"))
                try:
                    parse_result = self.parser.parse_file(file_path)
                    self._ui_call(lambda r=parse_result: self.append_log(f"解析完成：{r.file_info.file_name} | 元件 {len(r.components)} | 位号 {len(r.placements)} | 站位 {len(r.feeders)}"))
                    for warn in parse_result.warnings:
                        self._ui_call(lambda w=warn: self.append_log(f"[{w.level.upper()}] {w.message}"))

                    sheet_data = self.mapper.map_result(
                        parse_result,
                        export_components=options["export_components"],
                        export_stations=options["export_stations"],
                        export_placements=options["export_placements"],
                        export_summary=options["export_summary"],
                        export_raw=options["export_raw"],
                    )
                    mapped_results.append(sheet_data)

                    if options["split_by_file"]:
                        export_path = self.exporter.export(output_dir, f"{file_path.stem}_站位表", sheet_data)
                        success_exports.append(export_path)
                        self._ui_call(lambda p=export_path: self.append_log(f"已导出：{p.name}"))
                except PermissionError:
                    error_count += 1
                    self._ui_call(lambda p=file_path: self.append_log(f"[ERROR] 文件被占用或无权限访问：{p}"))
                except Exception as exc:
                    error_count += 1
                    logger.exception("处理文件失败: %s", file_path)
                    self._ui_call(lambda p=file_path, e=exc: self.append_log(f"[ERROR] 处理失败：{p.name} | {e}"))

            if options["merge_export"] and mapped_results:
                try:
                    merged = self.mapper.merge_sheet_sets(mapped_results)
                    export_path = self.exporter.export(output_dir, "juki批量站位表", merged)
                    success_exports.append(export_path)
                    self._ui_call(lambda p=export_path: self.append_log(f"已导出合并文件：{p.name}"))
                except PermissionError:
                    error_count += 1
                    self._ui_call(lambda: self.append_log("[ERROR] 合并导出失败：目标 Excel 文件可能被占用。"))
                except Exception as exc:
                    error_count += 1
                    logger.exception("合并导出失败")
                    self._ui_call(lambda e=exc: self.append_log(f"[ERROR] 合并导出失败：{e}"))

            summary = f"处理结束。成功导出 {len(success_exports)} 个文件，失败 {error_count} 个。"
            self._ui_call(lambda: self.append_log(summary))
            self._ui_call(lambda: messagebox.showinfo(APP_NAME, summary))
        finally:
            self.is_processing = False
            self._ui_call(self.refresh_license_status)

    def _ui_call(self, callback: Callable[[], None]) -> None:
        self.master.after(0, callback)
