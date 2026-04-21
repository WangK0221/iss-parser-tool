from __future__ import annotations

from copy import deepcopy
from typing import Any

from config import (
    CUSTOMER_SIDE_PREFIX_ORDER,
    CUSTOMER_FEEDER_DEVICE_VALUE_MAP,
    CUSTOMER_REFDES_MODE,
    CUSTOMER_STATION_PREFIX_MAP,
    CUSTOMER_SUPPLY_VALUE_MAP,
    CUSTOMER_TRAY_FEEDER_FALLBACK_VALUE,
    CUSTOMER_TRAY_PACKAGE_VALUES,
    CUSTOMER_TRAY_STATION_PREFIX,
)
from iss_parser_core.iss_parser import IssParseResult
from utils.export_settings import load_customer_export_settings
from utils.logger import get_logger

logger = get_logger("data_mapper")


def _safe_int(value: Any) -> int | None:
    try:
        text = str(value).strip()
        if not text:
            return None
        return int(float(text))
    except (TypeError, ValueError):
        return None


def build_feeder_pitch_signature(pitch: Any, pitch_count: Any) -> tuple[str, str]:
    pitch_value = _safe_int(pitch)
    count_value = _safe_int(pitch_count)
    if pitch_value is None or count_value is None:
        return "", ""
    if pitch_value <= 0 or count_value <= 0:
        return "", ""
    total = pitch_value * count_value
    return str(total), f"{total}mm({pitch_value}*{count_value})"


def _build_feeder_source_facts(component: Any, feeder: Any) -> dict[str, str]:
    extra = getattr(component, "extra", {}) or {}
    pitch_value = str(extra.get("feederPitch.pitch", "")).strip()
    pitch_count_value = str(extra.get("feederPitch.count", "")).strip()
    pitch_total, pitch_signature = build_feeder_pitch_signature(pitch_value, pitch_count_value)
    feeder_extra = getattr(feeder, "extra", {}) or {}
    return {
        "package": str(extra.get("package", "")).strip().upper(),
        "reelTypeId": str(extra.get("feeder.reelTypeId", "")).strip(),
        "pitch": pitch_value,
        "pitchCount": pitch_count_value,
        "pitchTotal": pitch_total,
        "pitchSignature": pitch_signature,
        "feederTypeId": str(getattr(feeder, "feeder_type", "")).strip(),
        "bankKind": str(getattr(feeder, "bank_kind", "")).strip(),
        "componentType": str(extra.get("componentType", "")).strip().upper(),
        "supplyUnitType": str(feeder_extra.get("supplyUnit.type", "")).strip(),
        "sourceKind": str(feeder_extra.get("source.kind", "")).strip().lower(),
    }


def build_feeder_interval_display(component: Any) -> str:
    extra = getattr(component, "extra", {}) or {}
    _, pitch_signature = build_feeder_pitch_signature(
        extra.get("feederPitch.pitch", ""),
        extra.get("feederPitch.count", ""),
    )
    return pitch_signature


def build_feeder_device_display(component: Any, feeder: Any) -> str:
    """供料装置显示规则。按 ISS 原始字段拆解，不依赖完整拼接串。"""
    if component is None or feeder is None:
        return ""

    facts = _build_feeder_source_facts(component, feeder)
    package_value = facts["package"]
    if package_value == "TRAY":
        direct_type = facts["supplyUnitType"]
        if direct_type:
            return direct_type
        return CUSTOMER_TRAY_FEEDER_FALLBACK_VALUE

    if package_value != "TAPE":
        return ""

    display = CUSTOMER_FEEDER_DEVICE_VALUE_MAP.get(facts["reelTypeId"], "")
    if display:
        return display

    if any(facts.values()):
        logger.warning("供料装置映射未命中: component=%s facts=%s", getattr(component, "component_name", ""), facts)
    return ""


def build_station_display(row: dict[str, Any]) -> str:
    """站位生成规则。tray 按区位输出，multiTray 固定回退到 MTS。"""
    package_value = str(row.get("package", "")).strip()
    supply_value = str(row.get("supply", "")).strip()
    number_value = str(row.get("number", "")).strip()
    component_name = str(row.get("componentName", "")).strip()
    source_kind = str(row.get("source_kind", "")).strip()
    zone_prefix = str(row.get("zone_prefix", "")).strip().upper()
    zone_number = str(row.get("zone_number", "")).strip()

    if not number_value:
        logger.warning("站位生成失败，缺少编号: %s", component_name or row)
        return ""

    if zone_prefix:
        display_number = zone_number or number_value
        return f"{zone_prefix}-{display_number}"

    if source_kind.lower() == "multitray" and package_value in CUSTOMER_TRAY_PACKAGE_VALUES:
        return f"{CUSTOMER_TRAY_STATION_PREFIX}-{number_value}"

    prefix = CUSTOMER_STATION_PREFIX_MAP.get(supply_value, "")
    if prefix:
        return f"{prefix}-{number_value}"

    if package_value in CUSTOMER_TRAY_PACKAGE_VALUES:
        return f"{CUSTOMER_TRAY_STATION_PREFIX}-{number_value}"

    logger.warning(
        "站位生成失败，未知包装或供应: component=%s package=%s supply=%s number=%s",
        component_name,
        package_value,
        supply_value,
        number_value,
    )
    return ""


def build_machine_station_display(machine_no: str, station_display: str) -> str:
    machine_text = str(machine_no or "").strip()
    station_text = str(station_display or "").strip()
    if not machine_text or not station_text:
        return ""
    if station_text.upper().startswith("MTS-"):
        return ""
    return f"{machine_text}{station_text}"


def build_package_display(component: Any, feeder: Any) -> str:
    """包装显示规则。当前仅使用源文件中可明确识别的信息。"""
    package_value = str(getattr(component, "extra", {}).get("package", "")).strip().upper()
    if package_value == "TAPE":
        return "带状"
    if package_value == "TRAY":
        return "托盘"
    return ""


def build_feeder_display(component: Any, feeder: Any) -> str:
    """客户飞达列显示。输出“供料装置 + 输送间隔”，tray 保持原始类型。"""
    device_display = str(build_feeder_device_display(component, feeder) or "").strip()
    if not device_display:
        return ""
    if device_display.upper().startswith("TR"):
        return device_display

    interval_display = str(build_feeder_interval_display(component) or "").strip()
    if interval_display:
        return f"{device_display} {interval_display}"
    return device_display


def build_supply_display(feeder: Any) -> str:
    if feeder is None:
        return ""
    bank_kind = str(getattr(feeder, "bank_kind", "")).strip()
    return CUSTOMER_SUPPLY_VALUE_MAP.get(bank_kind, "")


class DataMapper:
    """将原始解析结果转换为 Excel 工作表行。"""

    def map_result(
        self,
        parse_result: IssParseResult,
        export_components: bool = True,
        export_stations: bool = True,
        export_placements: bool = True,
        export_summary: bool = True,
        export_raw: bool = False,
    ) -> dict[str, Any]:
        component_map = self._build_component_map(parse_result)

        placements_by_component: dict[str, list[Any]] = {}
        for placement in parse_result.placements:
            placements_by_component.setdefault(placement.component_name, []).append(placement)

        feeders_by_component: dict[str, list[Any]] = {}
        for feeder in parse_result.feeders:
            feeders_by_component.setdefault(feeder.component_name, []).append(feeder)

        sheets: dict[str, Any] = {}
        sheets["customer"] = self._build_customer_sheet(
            parse_result,
            component_map,
            placements_by_component,
            feeders_by_component,
        )
        if export_components:
            sheets["components"] = self._build_component_sheet(parse_result, component_map, placements_by_component)
        if export_stations:
            sheets["stations"] = self._build_station_sheet(parse_result, component_map, feeders_by_component)
        if export_placements:
            sheets["placements"] = self._build_placement_sheet(parse_result, component_map)
        if export_summary:
            sheets["summary"] = self._build_summary_sheet(parse_result, component_map, placements_by_component, feeders_by_component)
        if export_raw:
            raw = parse_result.to_raw_tables()
            sheets["components_raw"] = raw["components"]
            sheets["placements_raw"] = raw["placements"]
            sheets["feeders_raw"] = raw["feeders"]
            sheets["feeder_debug"] = self._build_feeder_debug_sheet(
                parse_result,
                component_map,
                placements_by_component,
                feeders_by_component,
            )
        return sheets

    def merge_sheet_sets(self, sheet_sets: list[dict[str, Any]]) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        for sheet_set in sheet_sets:
            for sheet_name, sheet_data in sheet_set.items():
                if isinstance(sheet_data, dict) and sheet_data.get("sheet_type") == "customer_format":
                    current = merged.setdefault(
                        sheet_name,
                        {
                            "sheet_type": "customer_format",
                            "title": "juki批量站位表",
                            "machine_label": "",
                            "fields": list(sheet_data.get("fields", [])),
                            "headers": dict(sheet_data.get("headers", {})),
                            "rows": [],
                        },
                    )
                    current["rows"].extend(sheet_data.get("rows", []))
                else:
                    merged.setdefault(sheet_name, []).extend(sheet_data)

        for rows in merged.values():
            if isinstance(rows, list):
                for index, row in enumerate(rows, start=1):
                    if "序号" in row:
                        row["序号"] = index
        return merged

    def _build_component_sheet(self, parse_result, component_map, placements_by_component):
        rows: list[dict[str, Any]] = []
        names = self._get_all_component_names(component_map, placements_by_component, {})
        for index, component_name in enumerate(names, start=1):
            component = component_map.get(component_name)
            placements = placements_by_component.get(component_name, [])
            rows.append(
                {
                    "序号": index,
                    "物料编码": component_name,
                    "物料规格": component.comment if component else "",
                    "封装": component.package if component else "",
                    "用量": len(placements),
                    "位号列表": ",".join(item.placement_id for item in placements if item.placement_id),
                    "面别": parse_result.file_info.side,
                    "程序名": parse_result.file_info.program_name,
                    "文件名": parse_result.file_info.file_name,
                }
            )
        return rows

    def _build_customer_sheet(self, parse_result, component_map, placements_by_component, feeders_by_component):
        export_settings = load_customer_export_settings()
        machine_station_context = self._build_machine_station_context(parse_result.file_info.machines, parse_result.feeders)
        rows: list[dict[str, Any]] = []
        names = self._get_all_component_names(component_map, placements_by_component, feeders_by_component)
        for component_name in names:
            component = component_map.get(component_name)
            placements = placements_by_component.get(component_name, [])
            feeders = feeders_by_component.get(component_name, [])
            customer_feeders = self._iter_customer_feeders(feeders)
            for feeder in customer_feeders:
                station_rule = self._build_station_rule(component_name, component, feeder, machine_station_context)
                station_display = build_station_display(
                    {
                        "package": build_package_display(component, feeder),
                        "supply": build_supply_display(feeder),
                        "number": feeder.hole_no if feeder else "",
                        "componentName": component_name,
                        "source_kind": str(getattr(feeder, "extra", {}).get("source.kind", "")) if feeder else "",
                        "zone_prefix": station_rule["zone_prefix"],
                        "zone_number": station_rule["zone_number"],
                    }
                )

                rows.append(
                    {
                        "station": station_display,
                        "material_code": component_name,
                        "material_spec": component.comment if component else "",
                        "refdes": self._build_refdes_display(placements),
                        "package": build_package_display(component, feeder),
                        "feeder": build_feeder_display(component, feeder),
                        "quantity": len(placements),
                        "_machine_no": str(getattr(feeder, "machine_no", "")).strip(),
                        "_machine_name": str(getattr(feeder, "machine_name", "")).strip(),
                        "_machine_sort": self._safe_int(getattr(feeder, "machine_no", "")),
                        "_supply_sort": station_rule["sort_key"],
                        "_number_sort": self._safe_int(getattr(feeder, "hole_no", "")),
                    }
                )

        rows.sort(
            key=lambda item: (
                item.get("_machine_sort", 9999),
                item.get("_supply_sort", 9999),
                item.get("_number_sort", 9999),
                str(item.get("material_code", "")),
            )
        )
        for row in rows:
            row.pop("_machine_sort", None)
            row.pop("_supply_sort", None)
            row.pop("_number_sort", None)

        sections = self._build_customer_sections(rows)

        return {
            "sheet_type": "customer_format",
            "title": parse_result.file_info.program_name,
            "machine_label": self._build_machine_label(parse_result),
            "fields": list(export_settings["fields"]),
            "headers": dict(export_settings["headers"]),
            "layout": dict(export_settings.get("layout", {})),
            "detected_line_name": parse_result.file_info.line_name,
            "rows": rows,
            "sections": sections,
        }

    def _build_station_sheet(self, parse_result, component_map, feeders_by_component):
        machine_station_context = self._build_machine_station_context(parse_result.file_info.machines, parse_result.feeders)
        rows: list[dict[str, Any]] = []
        index = 1
        for component_name, feeders in feeders_by_component.items():
            component = component_map.get(component_name)
            for feeder in feeders:
                station_rule = self._build_station_rule(component_name, component, feeder, machine_station_context)
                feeder_dict = {
                    "package": build_package_display(component, feeder),
                    "supply": build_supply_display(feeder),
                    "number": feeder.hole_no,
                    "componentName": component_name,
                    "source_kind": str(getattr(feeder, "extra", {}).get("source.kind", "")),
                    "zone_prefix": station_rule["zone_prefix"],
                    "zone_number": station_rule["zone_number"],
                }
                rows.append(
                    {
                        "序号": index,
                        "物料编码": component_name,
                        "物料规格": component.comment if component else "",
                        "孔号": feeder.hole_no,
                        "stationId": feeder.station_id,
                        "bankPos": feeder.bank_pos,
                        "bankKind": feeder.bank_kind,
                        "feederType": feeder.feeder_type,
                        "站位": build_station_display(feeder_dict),
                        "面别": parse_result.file_info.side,
                        "程序名": parse_result.file_info.program_name,
                        "文件名": parse_result.file_info.file_name,
                    }
                )
                index += 1
        return rows

    def _build_feeder_debug_sheet(self, parse_result, component_map, placements_by_component, feeders_by_component):
        machine_station_context = self._build_machine_station_context(parse_result.file_info.machines, parse_result.feeders)
        rows: list[dict[str, Any]] = []
        names = self._get_all_component_names(component_map, placements_by_component, feeders_by_component)
        for index, component_name in enumerate(names, start=1):
            component = component_map.get(component_name)
            placements = placements_by_component.get(component_name, [])
            feeders = feeders_by_component.get(component_name, [])
            component_extra = getattr(component, "extra", {}) or {}
            pitch_total, pitch_signature = build_feeder_pitch_signature(
                component_extra.get("feederPitch.pitch", ""),
                component_extra.get("feederPitch.count", ""),
            )

            if feeders:
                for feeder in feeders:
                    station_rule = self._build_station_rule(component_name, component, feeder, machine_station_context)
                    rows.append(
                        {
                            "序号": index,
                            "物料编码": component_name,
                            "物料规格": component.comment if component else "",
                            "位号列表": ",".join(item.placement_id for item in placements if item.placement_id),
                            "package原值": component_extra.get("package", ""),
                            "供应": build_supply_display(feeder),
                            "编号": feeder.hole_no,
                            "componentType": component_extra.get("componentType", ""),
                            "reelTypeId": component_extra.get("feeder.reelTypeId", ""),
                            "feederPitch.pitch": component_extra.get("feederPitch.pitch", ""),
                            "feederPitch.count": component_extra.get("feederPitch.count", ""),
                            "feederPitch.total": pitch_total,
                            "feederPitch.signature": pitch_signature,
                            "供料装置显示": build_feeder_device_display(component, feeder),
                            "输送间隔显示": build_feeder_interval_display(component),
                            "供料单元类型": str(getattr(feeder, "extra", {}).get("supplyUnit.type", "")),
                            "position.stationId": feeder.station_id,
                            "position.bankPos": feeder.bank_pos,
                            "position.bankKind": feeder.bank_kind,
                            "position.holeNo": feeder.hole_no,
                            "feeder.typeId": feeder.feeder_type,
                            "machine.no": getattr(feeder, "machine_no", ""),
                            "machine.name": getattr(feeder, "machine_name", ""),
                            "pickPositionData.index": getattr(feeder, "pick_index", ""),
                            "lane": feeder.lane,
                            "package显示": build_package_display(component, feeder),
                            "站位显示": build_station_display(
                                {
                                    "package": build_package_display(component, feeder),
                                    "supply": build_supply_display(feeder),
                                    "number": feeder.hole_no,
                                    "componentName": component_name,
                                    "source_kind": str(getattr(feeder, "extra", {}).get("source.kind", "")),
                                    "zone_prefix": station_rule["zone_prefix"],
                                    "zone_number": station_rule["zone_number"],
                                }
                            ),
                            "区位前缀": station_rule["zone_prefix"],
                            "区位编号": station_rule["zone_number"],
                            "飞达显示": build_feeder_display(component, feeder),
                            "程序名": parse_result.file_info.program_name,
                            "面别": parse_result.file_info.side,
                        }
                    )
            else:
                rows.append(
                    {
                        "序号": index,
                        "物料编码": component_name,
                        "物料规格": component.comment if component else "",
                        "位号列表": ",".join(item.placement_id for item in placements if item.placement_id),
                        "package原值": component_extra.get("package", ""),
                        "供应": "",
                        "编号": "",
                        "componentType": component_extra.get("componentType", ""),
                        "reelTypeId": component_extra.get("feeder.reelTypeId", ""),
                        "feederPitch.pitch": component_extra.get("feederPitch.pitch", ""),
                        "feederPitch.count": component_extra.get("feederPitch.count", ""),
                        "feederPitch.total": pitch_total,
                        "feederPitch.signature": pitch_signature,
                        "供料装置显示": "",
                        "输送间隔显示": build_feeder_interval_display(component),
                        "供料单元类型": "",
                        "position.stationId": "",
                        "position.bankPos": "",
                        "position.bankKind": "",
                        "position.holeNo": "",
                        "feeder.typeId": "",
                        "lane": "",
                        "package显示": build_package_display(component, None),
                        "站位显示": "",
                        "飞达显示": "",
                        "程序名": parse_result.file_info.program_name,
                        "面别": parse_result.file_info.side,
                    }
                )
        return rows

    def _build_placement_sheet(self, parse_result, component_map):
        rows: list[dict[str, Any]] = []
        for index, placement in enumerate(parse_result.placements, start=1):
            component = component_map.get(placement.component_name)
            rows.append(
                {
                    "序号": index,
                    "位号": placement.placement_id,
                    "物料编码": placement.component_name,
                    "物料规格": component.comment if component else "",
                    "坐标X": placement.pos_x,
                    "坐标Y": placement.pos_y,
                    "角度": placement.angle,
                    "面别": parse_result.file_info.side,
                    "程序名": parse_result.file_info.program_name,
                    "文件名": parse_result.file_info.file_name,
                }
            )
        return rows

    def _build_summary_sheet(self, parse_result, component_map, placements_by_component, feeders_by_component):
        machine_station_context = self._build_machine_station_context(parse_result.file_info.machines, parse_result.feeders)
        rows: list[dict[str, Any]] = []
        names = self._get_all_component_names(component_map, placements_by_component, feeders_by_component)
        for index, component_name in enumerate(names, start=1):
            component = component_map.get(component_name)
            placements = placements_by_component.get(component_name, [])
            feeders = feeders_by_component.get(component_name, [])
            feeder = feeders[0] if feeders else None
            station_rule = self._build_station_rule(component_name, component, feeder, machine_station_context)
            feeder_dict = {
                "package": build_package_display(component, feeder),
                "supply": build_supply_display(feeder),
                "number": feeder.hole_no if feeder else "",
                "componentName": component_name,
                "source_kind": str(getattr(feeder, "extra", {}).get("source.kind", "")) if feeder else "",
                "zone_prefix": station_rule["zone_prefix"],
                "zone_number": station_rule["zone_number"],
            }
            rows.append(
                {
                    "序号": index,
                    "站位": build_station_display(feeder_dict),
                    "供料器编号/孔号": feeder.hole_no if feeder else "",
                    "物料编码": component_name,
                    "物料规格": component.comment if component else "",
                    "用量": len(placements),
                    "位号数量": len(placements),
                    "面别": parse_result.file_info.side,
                    "程序名": parse_result.file_info.program_name,
                    "文件名": parse_result.file_info.file_name,
                }
            )
        return rows

    def _get_all_component_names(self, component_map, placements_by_component, feeders_by_component) -> list[str]:
        names = set(component_map)
        names.update(name for name in placements_by_component if name)
        names.update(name for name in feeders_by_component if name)
        return sorted(names)

    def _build_machine_label(self, parse_result: IssParseResult) -> str:
        feeders = parse_result.feeders
        machine_pairs: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()

        for feeder in feeders:
            pair = (str(getattr(feeder, "machine_no", "")).strip(), str(getattr(feeder, "machine_name", "")).strip())
            if not pair[0] or not pair[1] or pair in seen:
                continue
            seen.add(pair)
            machine_pairs.append(pair)

        if not machine_pairs:
            for machine in parse_result.file_info.machines:
                pair = (str(machine.get("no", "")).strip(), str(machine.get("name", "")).strip())
                if not pair[0] or not pair[1] or pair in seen:
                    continue
                seen.add(pair)
                machine_pairs.append(pair)

        if not machine_pairs:
            machine_name = parse_result.file_info.machine_name or "UNKNOWN"
            return f"[#1({machine_name})]"

        machine_pairs.sort(key=lambda item: self._safe_int(item[0]))
        return " ".join(f"[#{machine_no}({machine_name})]" for machine_no, machine_name in machine_pairs)

    def _build_customer_sections(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        sections: list[dict[str, Any]] = []
        section_map: dict[str, dict[str, Any]] = {}

        for row in rows:
            machine_no = str(row.get("_machine_no", "")).strip()
            machine_name = str(row.get("_machine_name", "")).strip()

            key = machine_no or "UNKNOWN"
            if key not in section_map:
                label = f"[#{machine_no}({machine_name})]" if machine_no and machine_name else f"[#{machine_no}]" if machine_no else "[未关联机台]"
                section_map[key] = {
                    "machine_no": machine_no,
                    "machine_name": machine_name,
                    "machine_label": label,
                    "rows": [],
                    "groups": [],
                }
                sections.append(section_map[key])

            section_row = dict(row)
            section_row.pop("_machine_no", None)
            section_row.pop("_machine_name", None)
            section_map[key]["rows"].append(section_row)

        for section in sections:
            section["rows"].sort(
                key=lambda item: (
                    self._supply_sort_key_from_station(str(item.get("station", ""))),
                    self._number_sort_from_station(str(item.get("station", ""))),
                    str(item.get("material_code", "")),
                )
            )
            section["groups"] = self._split_section_groups(section["rows"])

        return sections

    def _split_section_groups(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        groups: list[dict[str, Any]] = []
        current_group: dict[str, Any] | None = None

        for row in rows:
            group_key = self._station_group_key(str(row.get("station", "")))
            if group_key == "TRAY" and current_group is not None:
                current_group["rows"].append(row)
                continue
            if current_group is None or current_group["group_key"] != group_key:
                current_group = {
                    "group_key": group_key,
                    "rows": [],
                }
                groups.append(current_group)
            current_group["rows"].append(row)

        return groups

    def _build_refdes_display(self, placements: list[Any]) -> str:
        refdes_list = [item.placement_id for item in placements if item.placement_id]
        if not refdes_list:
            return ""
        if CUSTOMER_REFDES_MODE == "first":
            return refdes_list[0]
        return ",".join(refdes_list)

    def _iter_customer_feeders(self, feeders: list[Any]) -> list[Any]:
        if not feeders:
            return [None]

        ordered = sorted(
            feeders,
            key=lambda item: (
                self._safe_int(getattr(item, "machine_no", "")),
                self._safe_int(getattr(item, "station_id", "")),
                self._supply_sort_key(build_supply_display(item)),
                self._safe_int(getattr(item, "hole_no", "")),
            ),
        )
        return ordered

    def _build_component_map(self, parse_result: IssParseResult) -> dict[str, Any]:
        component_map: dict[str, Any] = {}
        for item in parse_result.components:
            if not item.component_name:
                continue
            current = component_map.get(item.component_name)
            if current is None:
                component_map[item.component_name] = deepcopy(item)
            else:
                component_map[item.component_name] = self._merge_component_record(current, item)
        return component_map

    def _component_score(self, component: Any) -> int:
        score = 0
        if getattr(component, "comment", ""):
            score += 3
        if getattr(component, "package", ""):
            score += 2
        if getattr(component, "package_code", ""):
            score += 1
        if getattr(component, "width", "") or getattr(component, "length", "") or getattr(component, "height", ""):
            score += 1
        return score

    def _merge_component_record(self, current: Any, incoming: Any) -> Any:
        merged = deepcopy(current)
        for field_name in ["comment", "package", "package_code", "width", "length", "height", "source_tag"]:
            current_value = getattr(merged, field_name, "")
            incoming_value = getattr(incoming, field_name, "")
            if self._is_better_value(current_value, incoming_value):
                setattr(merged, field_name, incoming_value)

        merged.extra = dict(getattr(merged, "extra", {}) or {})
        for key, value in (getattr(incoming, "extra", {}) or {}).items():
            if key not in merged.extra or self._is_better_value(merged.extra.get(key, ""), value):
                merged.extra[key] = value
        return merged

    def _is_better_value(self, current_value: Any, incoming_value: Any) -> bool:
        current_text = str(current_value or "").strip()
        incoming_text = str(incoming_value or "").strip()
        if not incoming_text:
            return False
        if not current_text:
            return True
        return len(incoming_text) > len(current_text)

    def _safe_int(self, value: Any) -> int:
        text = str(value or "").strip()
        if text.isdigit():
            return int(text)
        return 9999

    def _supply_sort_key(self, supply: str) -> int:
        if supply == "前面":
            return 1
        if supply == "后面":
            return 2
        return 9999

    def _supply_sort_key_from_station(self, station: str) -> int:
        station_text = station.strip().upper()
        if station_text.startswith("LF-"):
            return 1
        if station_text.startswith("RF-"):
            return 2
        if station_text.startswith("LR-"):
            return 3
        if station_text.startswith("RR-"):
            return 4
        if station_text.startswith("F-"):
            return 5
        if station_text.startswith("R-"):
            return 6
        if station_text.startswith("MTS-"):
            return 7
        return 9999

    def _number_sort_from_station(self, station: str) -> int:
        station_text = station.strip().upper()
        for prefix in ("LF-", "RF-", "LR-", "RR-", "F-", "R-", "MTS-"):
            if station_text.startswith(prefix):
                return self._safe_int(station_text[len(prefix):])
        return 9999

    def _station_group_key(self, station: str) -> str:
        station_text = station.strip().upper()
        if station_text.startswith("LF-"):
            return "FRONT_DUAL"
        if station_text.startswith("RF-"):
            return "FRONT_DUAL"
        if station_text.startswith("LR-"):
            return "REAR_DUAL"
        if station_text.startswith("RR-"):
            return "REAR_DUAL"
        if station_text.startswith("F-"):
            return "F"
        if station_text.startswith("R-"):
            return "R"
        if station_text.startswith("MTS-"):
            return "TRAY"
        return "UNKNOWN"

    def _build_machine_station_context(self, machine_defs: list[dict[str, Any]], feeders: list[Any]) -> dict[str, dict[str, Any]]:
        context: dict[str, dict[str, Any]] = {}
        for machine in machine_defs:
            machine_no = str(machine.get("no", "")).strip()
            machine_name = str(machine.get("name", "")).strip()
            machine_key = machine_no or machine_name
            if not machine_key:
                continue
            item = context.setdefault(
                machine_key,
                {
                    "machine_name": machine_name,
                    "station_ids": set(),
                    "bank_kinds": set(),
                },
            )
            for station_id in machine.get("station_ids", []):
                text = str(station_id or "").strip()
                if text:
                    item["station_ids"].add(text)
            for bank_kind in machine.get("bank_kinds", []):
                text = str(bank_kind or "").strip()
                if text:
                    item["bank_kinds"].add(text)

        for feeder in feeders:
            machine_key = str(getattr(feeder, "machine_no", "")).strip() or str(getattr(feeder, "machine_name", "")).strip()
            if not machine_key:
                continue
            item = context.setdefault(
                machine_key,
                {
                    "machine_name": str(getattr(feeder, "machine_name", "")).strip(),
                    "station_ids": set(),
                    "bank_kinds": set(),
                },
            )
            station_id = str(getattr(feeder, "station_id", "")).strip()
            bank_kind = str(getattr(feeder, "bank_kind", "")).strip()
            if station_id:
                item["station_ids"].add(station_id)
            if bank_kind:
                item["bank_kinds"].add(bank_kind)
        return context

    def _build_station_rule(self, component_name: str, component: Any, feeder: Any, context: dict[str, dict[str, Any]]) -> dict[str, Any]:
        if feeder is None:
            return {"zone_prefix": "", "zone_number": "", "sort_key": 9999}

        source_kind = str(getattr(feeder, "extra", {}).get("source.kind", "")).strip().lower()
        machine_key = str(getattr(feeder, "machine_no", "")).strip() or str(getattr(feeder, "machine_name", "")).strip()
        machine_context = context.get(machine_key, {})
        station_ids = sorted(machine_context.get("station_ids", set()), key=self._safe_int)
        bank_kinds = sorted(machine_context.get("bank_kinds", set()), key=self._safe_int)
        station_id = str(getattr(feeder, "station_id", "")).strip()
        bank_kind = str(getattr(feeder, "bank_kind", "")).strip()
        number_value = str(getattr(feeder, "hole_no", "")).strip()

        zone_prefix = ""
        zone_number = number_value

        if source_kind == "multitray":
            station_text = f"{CUSTOMER_TRAY_STATION_PREFIX}-{zone_number}" if zone_number else ""
            return {
                "zone_prefix": "",
                "zone_number": zone_number,
                "sort_key": self._supply_sort_key_from_station(station_text),
            }

        # 四区设备：同时存在左右 stationId 与前后 bankKind
        if len(station_ids) > 1 and len(bank_kinds) > 1:
            zone_prefix = self._compose_side_bank_prefix(station_id, station_ids, bank_kind)
            zone_number = self._compose_multi_zone_number(
                machine_no=str(getattr(feeder, "machine_no", "")).strip(),
                machine_name=str(getattr(feeder, "machine_name", "")).strip(),
                hole_no=number_value,
            )
        # 两区设备：只存在左右 stationId
        elif len(station_ids) > 1:
            side_prefix = self._side_prefix_for_station(station_id, station_ids)
            if side_prefix:
                if bank_kind == "2":
                    zone_prefix = f"{side_prefix}R"
                else:
                    zone_prefix = f"{side_prefix}F"
                zone_number = self._compose_multi_zone_number(
                    machine_no=str(getattr(feeder, "machine_no", "")).strip(),
                    machine_name=str(getattr(feeder, "machine_name", "")).strip(),
                    hole_no=number_value,
                )
        # 前后设备：使用 bankKind
        elif len(bank_kinds) > 1 or bank_kind:
            supply = build_supply_display(feeder)
            zone_prefix = CUSTOMER_STATION_PREFIX_MAP.get(supply, "")

        if not zone_prefix and machine_context:
            logger.warning(
                "站位区位规则未命中，回退普通规则: component=%s machine=%s stationId=%s bankKind=%s number=%s",
                component_name,
                machine_key,
                station_id,
                bank_kind,
                number_value,
            )

        return {
            "zone_prefix": zone_prefix,
            "zone_number": zone_number,
            "sort_key": self._supply_sort_key_from_station(f"{zone_prefix}-{zone_number}" if zone_prefix else ""),
        }

    def _side_prefix_for_station(self, station_id: str, station_ids: list[str]) -> str:
        if not station_id or station_id not in station_ids:
            return ""
        index = station_ids.index(station_id)
        if index < len(CUSTOMER_SIDE_PREFIX_ORDER):
            return CUSTOMER_SIDE_PREFIX_ORDER[index]
        return CUSTOMER_SIDE_PREFIX_ORDER[-1]

    def _compose_side_bank_prefix(self, station_id: str, station_ids: list[str], bank_kind: str) -> str:
        side_prefix = self._side_prefix_for_station(station_id, station_ids)
        if not side_prefix:
            return ""
        if bank_kind == "2":
            return f"{side_prefix}R"
        return f"{side_prefix}F"

    def _compose_multi_zone_number(self, machine_no: str, machine_name: str, hole_no: str) -> str:
        hole_text = str(hole_no or "").strip()
        if not hole_text:
            return hole_text
        if not self._should_pad_station_number(machine_no, machine_name):
            return hole_text
        if not hole_text.isdigit():
            return hole_text

        hole_number = int(hole_text)
        if 1 <= hole_number <= 28:
            return f"1{hole_number:02d}"
        return hole_text

    def _should_pad_station_number(self, machine_no: str, machine_name: str) -> bool:
        settings = load_customer_export_settings()
        station_number_mapping = settings.get("station_number_mapping", {})
        if not station_number_mapping and "station_padding" in settings:
            station_number_mapping = settings.get("station_padding", {})
        patterns = station_number_mapping.get("enabled_machine_patterns", [])
        machine_name_text = str(machine_name or "").strip().upper().replace(" ", "")
        machine_no_text = str(machine_no or "").strip().upper().replace(" ", "")

        for pattern in patterns:
            pattern_text = str(pattern or "").strip().upper().replace(" ", "")
            if not pattern_text:
                continue
            if machine_name_text and pattern_text in machine_name_text:
                return True
            if machine_no_text and pattern_text == machine_no_text:
                return True
        return False
