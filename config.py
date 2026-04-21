from __future__ import annotations

from pathlib import Path
import sys


APP_NAME = "ISS贴片程序解析工具"
APP_VERSION = "1.1.0"

# 持久化目录与资源目录分离：
# - 源码运行时：仍使用项目根目录。
# - PyInstaller onefile 运行时：持久化文件应落到 exe 同目录，不能写入临时解包目录。
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
DEFAULT_OUTPUT_DIR = BASE_DIR / "output"
LICENSE_DIR = BASE_DIR / "license"
DEFAULT_LICENSE_PATH = LICENSE_DIR / "license.json"
SETTINGS_DIR = BASE_DIR / "settings"
CUSTOMER_EXPORT_SETTINGS_PATH = SETTINGS_DIR / "customer_export.json"

SUPPORTED_EXTENSIONS = {".iss"}

RAW_SHEET_NAMES = {
    "components": "components_raw",
    "placements": "placements_raw",
    "feeders": "feeders_raw",
}

MAIN_SHEET_NAMES = {
    "customer": "客户格式",
    "components": "元件明细",
    "stations": "站位明细",
    "placements": "位号明细",
    "summary": "汇总表",
    "feeder_debug": "飞达规则调试",
}

DATETIME_FORMAT = "%Y%m%d_%H%M%S"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LICENSE_SECRET = "ISSParserTool-Simple-Offline-License-v1"

WINDOW_MIN_SIZE = (1000, 720)

DEFAULT_EXPORT_OPTIONS = {
    "split_by_file": True,
    "merge_export": False,
    "export_components": True,
    "export_stations": True,
    "export_placements": True,
    "export_summary": True,
    "export_raw": False,
}

ABOUT_DIALOG_DEFAULTS = {
    "window_title": f"关于 {APP_NAME}",
    "qr_image_path": "assets/about_qr.jpg",
    "dialog_width": 720,
    "dialog_height": 360,
    "info_lines": [
        {"label": "产品名称", "value": APP_NAME},
        {"label": "版本", "value": f"v{APP_VERSION}"},
        {"label": "联系方式(v)", "value": "mominshou"},
    ],
    "description": "本软件用于解析 SMT 贴片程序并导出客户格式报表。\n扫码添加微信，沟通需求或获取技术支持。",
}

# 客户格式主表配置。后续如客户调整列顺序或表头文字，只改这里。
CUSTOMER_EXPORT_FIELDS = [
    "station",
    "material_code",
    "material_spec",
    "refdes",
    "package",
    "feeder",
    "quantity",
]

CUSTOMER_EXPORT_HEADERS = {
    "station": "站位",
    "material_code": "物料编码",
    "material_spec": "物料规格",
    "refdes": "位号",
    "package": "包装",
    "feeder": "飞达",
    "quantity": "用量",
}

CUSTOMER_EXPORT_FIELD_LABELS = {
    "station": "站位",
    "material_code": "物料编码",
    "material_spec": "物料规格",
    "refdes": "位号",
    "package": "包装",
    "feeder": "飞达",
    "quantity": "用量",
}

CUSTOMER_EXPORT_LAYOUT_DEFAULTS = {
    "line_label": "线体",
    "line_value": "",
    "machine_label": "机台",
    "split_by_station_group": True,
}

CUSTOMER_STATION_NUMBER_MAPPING_DEFAULTS = {
    "enabled_machine_patterns": ["RX-7", "RX-8"],
}

CUSTOMER_EXPORT_WIDTHS = {
    "station": 14,
    "material_code": 22,
    "material_spec": 28,
    "refdes": 26,
    "package": 12,
    "feeder": 18,
    "quantity": 10,
}

# 位号显示方式：
# joined: 同物料的多个位号逗号拼接
# first: 只显示首个位号
CUSTOMER_REFDES_MODE = "joined"

# 飞达显示业务规则。按样品验证结果配置，按顺序命中。
# 字段支持：
# package, reelTypeId, pitch, pitchCount, pitchTotal, pitchSignature, feederTypeId, bankKind, componentType
CUSTOMER_FEEDER_RULES = [
    {"name": "托盘料", "match": {"package": "TRAY"}, "display": "TR5S"},
    {"name": "8mm纸带-A", "match": {"package": "TAPE", "reelTypeId": "2", "pitch": "2", "pitchCount": "1", "feederTypeId": "1"}, "display": "M 8mm 纸带"},
    {"name": "8mm纸带-B", "match": {"package": "TAPE", "reelTypeId": "3", "pitch": "4", "pitchCount": "1", "feederTypeId": "1"}, "display": "M 8mm 纸带"},
    {"name": "8mm胶带-A", "match": {"package": "TAPE", "reelTypeId": "4", "pitch": "2", "pitchCount": "1", "feederTypeId": "2"}, "display": "M 8mm 胶带"},
    {"name": "8mm胶带-B", "match": {"package": "TAPE", "reelTypeId": "5", "pitch": "4", "pitchCount": "1", "feederTypeId": "2"}, "display": "M 8mm 胶带"},
    {"name": "12mm-A", "match": {"package": "TAPE", "reelTypeId": "6", "pitch": "4", "feederTypeId": "3"}, "display": "M 12mm"},
    {"name": "12mm-B", "match": {"package": "TAPE", "reelTypeId": "7", "pitch": "4", "feederTypeId": "3"}, "display": "M 12mm"},
    {"name": "12mm-C", "match": {"package": "TAPE", "reelTypeId": "8", "pitch": "6", "feederTypeId": "3"}, "display": "M 12mm"},
    {"name": "16mm-A", "match": {"package": "TAPE", "reelTypeId": "10", "pitch": "4", "feederTypeId": "4"}, "display": "M 16mm"},
    {"name": "16mm-B", "match": {"package": "TAPE", "reelTypeId": "11", "pitch": "6", "feederTypeId": "4"}, "display": "M 16mm"},
    {"name": "24mm-A", "match": {"package": "TAPE", "reelTypeId": "14", "pitch": "6", "feederTypeId": "5"}, "display": "M 24mm"},
    {"name": "24mm-B", "match": {"package": "TAPE", "reelTypeId": "15", "pitch": "8", "feederTypeId": "5"}, "display": "M 24mm"},
    {"name": "32mm", "match": {"package": "TAPE", "reelTypeId": "19", "pitch": "12", "pitchCount": "1"}, "display": "M 32mm"},
    {"name": "32mm-B", "match": {"package": "TAPE", "reelTypeId": "20", "pitch": "8", "pitchCount": "2"}, "display": "M 32mm"},
    {"name": "44mm", "match": {"package": "TAPE", "reelTypeId": "30", "pitch": "12", "feederTypeId": "8"}, "display": "M 44mm"},
    {"name": "44mm-20pitch", "match": {"package": "TAPE", "reelTypeId": "29", "pitch": "20", "pitchCount": "1"}, "display": "M 44mm"},
    {"name": "56mm", "match": {"package": "TAPE", "reelTypeId": "39", "pitch": "12", "pitchCount": "2"}, "display": "M 56mm"},
    {"name": "72mm", "match": {"package": "TAPE", "reelTypeId": "52", "pitch": "14", "pitchCount": "2"}, "display": "M 72mm"},
    {"name": "8mm胶带-C", "match": {"package": "TAPE", "reelTypeId": "61", "pitch": "1", "pitchCount": "1"}, "display": "M 8mm 胶带"},
]

# 飞达通用回退规则。
# 当精确规则未命中时，按 reelTypeId 家族回退，优先解决新机型/新 feederTypeId 下的空值问题。
# 这套规则是候选通用规律，不覆盖已确认的精确规则。
CUSTOMER_FEEDER_FALLBACK_RULES = [
    {"name": "托盘通用", "match": {"package": "TRAY"}, "display": "TR5S"},
    {"name": "8mm纸带通用-A", "match": {"package": "TAPE", "reelTypeId": "2"}, "display": "M 8mm 纸带"},
    {"name": "8mm纸带通用-B", "match": {"package": "TAPE", "reelTypeId": "3"}, "display": "M 8mm 纸带"},
    {"name": "8mm胶带通用-A", "match": {"package": "TAPE", "reelTypeId": "4"}, "display": "M 8mm 胶带"},
    {"name": "8mm胶带通用-B", "match": {"package": "TAPE", "reelTypeId": "5"}, "display": "M 8mm 胶带"},
    {"name": "12mm通用-A", "match": {"package": "TAPE", "reelTypeId": "6"}, "display": "M 12mm"},
    {"name": "12mm通用-B", "match": {"package": "TAPE", "reelTypeId": "7"}, "display": "M 12mm"},
    {"name": "12mm通用-C", "match": {"package": "TAPE", "reelTypeId": "8"}, "display": "M 12mm"},
    {"name": "16mm通用-A", "match": {"package": "TAPE", "reelTypeId": "10"}, "display": "M 16mm"},
    {"name": "16mm通用-B", "match": {"package": "TAPE", "reelTypeId": "11"}, "display": "M 16mm"},
    {"name": "24mm通用-A", "match": {"package": "TAPE", "reelTypeId": "14"}, "display": "M 24mm"},
    {"name": "24mm通用-B", "match": {"package": "TAPE", "reelTypeId": "15"}, "display": "M 24mm"},
    {"name": "32mm通用", "match": {"package": "TAPE", "reelTypeId": "19"}, "display": "M 32mm"},
    {"name": "32mm通用-B", "match": {"package": "TAPE", "reelTypeId": "20"}, "display": "M 32mm"},
    {"name": "44mm通用-20pitch", "match": {"package": "TAPE", "reelTypeId": "29"}, "display": "M 44mm"},
    {"name": "44mm通用", "match": {"package": "TAPE", "reelTypeId": "30"}, "display": "M 44mm"},
    {"name": "56mm通用", "match": {"package": "TAPE", "reelTypeId": "39"}, "display": "M 56mm"},
    {"name": "72mm通用", "match": {"package": "TAPE", "reelTypeId": "52"}, "display": "M 72mm"},
    {"name": "8mm胶带通用-C", "match": {"package": "TAPE", "reelTypeId": "61"}, "display": "M 8mm 胶带"},
]

# 站位业务规则配置
CUSTOMER_SUPPLY_VALUE_MAP = {
    "1": "前面",
    "2": "后面",
}

CUSTOMER_STATION_PREFIX_MAP = {
    "前面": "F",
    "后面": "R",
}

CUSTOMER_TRAY_PACKAGE_VALUES = {"托盘"}
CUSTOMER_TRAY_STATION_PREFIX = "MTS"

# 左右区位映射。当前按样本约定：
# stationId 升序映射为左、右；若同时存在前后区，则组合成 LF/RF/LR/RR。
CUSTOMER_SIDE_PREFIX_ORDER = ["L", "R"]
