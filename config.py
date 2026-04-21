from __future__ import annotations

from pathlib import Path
import sys


APP_NAME = "juki站位表生成工具"
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
    "description": "本软件用于解析.iss文件并导出站位表。\n扫码添加微信，沟通需求或获取技术支持。",
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
    {"name": "8mm纸带-A", "match": {"package": "TAPE", "reelTypeId": "2", "pitch": "2", "pitchCount": "1"}, "display": "M 8mm 纸带"},
    {"name": "8mm纸带-B", "match": {"package": "TAPE", "reelTypeId": "3", "pitch": "4", "pitchCount": "1"}, "display": "M 8mm 纸带"},
    {"name": "8mm胶带-A", "match": {"package": "TAPE", "reelTypeId": "4", "pitch": "2", "pitchCount": "1"}, "display": "M 8mm 胶带"},
    {"name": "8mm胶带-B", "match": {"package": "TAPE", "reelTypeId": "5", "pitch": "4", "pitchCount": "1"}, "display": "M 8mm 胶带"},
    {"name": "12mm-A", "match": {"package": "TAPE", "reelTypeId": "6", "pitch": "4"}, "display": "M 12mm"},
    {"name": "12mm-B", "match": {"package": "TAPE", "reelTypeId": "7", "pitch": "4"}, "display": "M 12mm"},
    {"name": "12mm-B-8pitch", "match": {"package": "TAPE", "reelTypeId": "7", "pitch": "8", "pitchCount": "1"}, "display": "M 12mm"},
    {"name": "12mm-C", "match": {"package": "TAPE", "reelTypeId": "8", "pitch": "6"}, "display": "M 12mm"},
    {"name": "16mm-A", "match": {"package": "TAPE", "reelTypeId": "10", "pitch": "4"}, "display": "M 16mm"},
    {"name": "16mm-B", "match": {"package": "TAPE", "reelTypeId": "11", "pitch": "6"}, "display": "M 16mm"},
    {"name": "24mm-A", "match": {"package": "TAPE", "reelTypeId": "14", "pitch": "6"}, "display": "M 24mm"},
    {"name": "24mm-B", "match": {"package": "TAPE", "reelTypeId": "15", "pitch": "8"}, "display": "M 24mm"},
    {"name": "32mm-A", "match": {"package": "TAPE", "reelTypeId": "19", "pitch": "6", "pitchCount": "2"}, "display": "M 32mm"},
    {"name": "32mm", "match": {"package": "TAPE", "reelTypeId": "19", "pitch": "12", "pitchCount": "1"}, "display": "M 32mm"},
    {"name": "32mm-B", "match": {"package": "TAPE", "reelTypeId": "20", "pitch": "8", "pitchCount": "2"}, "display": "M 32mm"},
    {"name": "44mm", "match": {"package": "TAPE", "reelTypeId": "30", "pitch": "12"}, "display": "M 44mm"},
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

# 供料装置映射。
# 目标是从 ISS 原始字段直接推导“供料装置”，不依赖软件界面中的完整拼接串。
# 主键以 package + reelTypeId 为主；pitch/count 应单独派生为“输送间隔”。
# 注意：
# - 当前规则按已知 reelTypeId 显式枚举，不按数值区间推导。
# - 现有样本已经证明 61 仍可能映射回 8mm 家族，因此不能使用“49+ 全是 72mm”之类的区间假设。
CUSTOMER_FEEDER_DEVICE_VALUE_MAP = {
    # 8mm 家族
    "2": "8mm 纸带",
    "3": "8mm 纸带",
    "4": "8mm 胶带",
    "5": "8mm 胶带",
    # 12mm 家族
    "6": "12mm 胶带",
    "7": "12mm 胶带",
    "8": "12mm 胶带",
    # 16mm 家族
    "9": "16mm 胶带",
    "10": "16mm 胶带",
    "11": "16mm 胶带",
    "12": "16mm 胶带",
    # 24mm 家族
    "13": "24mm 胶带",
    "14": "24mm 胶带",
    "15": "24mm 胶带",
    "16": "24mm 胶带",
    "17": "24mm 胶带",
    "18": "24mm 胶带",
    # 32mm 家族
    "19": "32mm 胶带",
    "20": "32mm 胶带",
    "21": "32mm 胶带",
    "22": "32mm 胶带",
    "23": "32mm 胶带",
    "24": "32mm 胶带",
    "25": "32mm 胶带",
    "26": "32mm 胶带",
    # 44mm 家族
    "27": "44mm 胶带",
    "28": "44mm 胶带",
    "29": "44mm 胶带",
    "30": "44mm 胶带",
    "31": "44mm 胶带",
    "32": "44mm 胶带",
    "34": "44mm 胶带",
    "35": "44mm 胶带",
    # 56mm 家族
    "36": "56mm 胶带",
    "37": "56mm 胶带",
    "38": "56mm 胶带",
    "39": "56mm 胶带",
    "40": "56mm 胶带",
    "41": "56mm 胶带",
    "42": "56mm 胶带",
    "43": "56mm 胶带",
    "44": "56mm 胶带",
    "45": "56mm 胶带",
    "46": "56mm 胶带",
    "47": "56mm 胶带",
    # 72mm 家族
    "48": "72mm 胶带",
    "49": "72mm 胶带",
    "50": "72mm 胶带",
    "51": "72mm 胶带",
    "52": "72mm 胶带",
    "53": "72mm 胶带",
    "54": "72mm 胶带",
    "55": "72mm 胶带",
    "56": "72mm 胶带",
    "57": "72mm 胶带",
    "58": "72mm 胶带",
    "59": "72mm 胶带",
    # 72/88mm 边界样本中的特殊枚举。74 来自 56-72mm 样本分组，81-83 来自 72-88mm 样本分组。
    "74": "72mm 胶带",
    # 88mm 家族（目前仅样本覆盖到这 3 个值）
    "81": "88mm 胶带",
    "82": "88mm 胶带",
    "83": "88mm 胶带",
    # 8mm 特例，不能按区间归到 72mm
    "61": "8mm 胶带",
}

CUSTOMER_TRAY_FEEDER_FALLBACK_VALUE = "TR5S"

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
