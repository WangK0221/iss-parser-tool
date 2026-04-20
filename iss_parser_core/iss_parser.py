from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
import re
from typing import Any
import xml.etree.ElementTree as ET

from utils.logger import get_logger

logger = get_logger("parser")


@dataclass
class FileInfo:
    file_name: str
    file_path: str
    program_name: str = ""
    product_name: str = ""
    date_code: str = ""
    side: str = ""
    machine_name: str = ""
    line_name: str = ""
    exported_at: str = ""
    machines: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ComponentRecord:
    component_name: str = ""
    comment: str = ""
    package: str = ""
    package_code: str = ""
    width: str = ""
    length: str = ""
    height: str = ""
    source_tag: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class PlacementRecord:
    placement_id: str = ""
    component_name: str = ""
    position_raw: str = ""
    pos_x: str = ""
    pos_y: str = ""
    angle: str = ""
    head_no: str = ""
    nozzle_no: str = ""
    station_no: str = ""
    source_tag: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class FeederRecord:
    component_name: str = ""
    machine_no: str = ""
    machine_name: str = ""
    pick_index: str = ""
    hole_no: str = ""
    station_id: str = ""
    bank_pos: str = ""
    bank_kind: str = ""
    feeder_type: str = ""
    lane: str = ""
    pick_x: str = ""
    pick_y: str = ""
    pick_z: str = ""
    source_tag: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParseWarning:
    level: str
    message: str


@dataclass
class IssParseResult:
    file_info: FileInfo
    components: list[ComponentRecord]
    placements: list[PlacementRecord]
    feeders: list[FeederRecord]
    warnings: list[ParseWarning] = field(default_factory=list)

    def to_raw_tables(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "components": [asdict(item) for item in self.components],
            "placements": [asdict(item) for item in self.placements],
            "feeders": [asdict(item) for item in self.feeders],
        }


class IssParser:
    """ISS 文件解析器，按标签名宽松提取数据。"""

    FIELD_ALIASES = {
        "component_name": ["componentName", "component_name", "partName", "materialCode"],
        "comment": ["comment", "description", "specification", "desc"],
        "package": ["package", "packageName", "packageType"],
        "placement_id": ["placementId", "refdes", "designator", "reference"],
        "position": ["placementPosition", "position", "mountPosition"],
        "angle": ["placementAngle", "angle", "rotation"],
    }

    def parse_file(self, file_path: str | Path) -> IssParseResult:
        path = Path(file_path)
        file_info = self._build_file_info(path)
        warnings: list[ParseWarning] = []
        root = self._load_xml_root(path, warnings)
        if root is None:
            return IssParseResult(file_info=file_info, components=[], placements=[], feeders=[], warnings=warnings)

        machine_defs = self._parse_machine_definitions(root)
        self._fill_file_info_from_xml(root, file_info, machine_defs)
        components = self._parse_components(root, warnings)
        placements = self._parse_placements(root, warnings)
        feeders = self._parse_feeders(root, warnings, machine_defs)

        if not components:
            warnings.append(ParseWarning("warning", "未找到 component 数据"))
        if not placements:
            warnings.append(ParseWarning("warning", "未找到 placement 数据"))
        if not feeders:
            warnings.append(ParseWarning("warning", "未找到 feeder 数据"))

        return IssParseResult(file_info=file_info, components=components, placements=placements, feeders=feeders, warnings=warnings)

    def _load_xml_root(self, path: Path, warnings: list[ParseWarning]) -> ET.Element | None:
        last_error: Exception | None = None
        for encoding in ("utf-8", "utf-8-sig", "gbk", "gb18030"):
            try:
                with path.open("r", encoding=encoding) as file:
                    content = file.read()
                return ET.fromstring(content)
            except Exception as exc:
                last_error = exc
        message = f"XML 解析失败: {path.name} | {last_error}"
        logger.exception(message)
        warnings.append(ParseWarning("error", message))
        return None

    def _build_file_info(self, path: Path) -> FileInfo:
        stem = path.stem
        side_match = re.search(r"(TOP|BOT)", stem, flags=re.IGNORECASE)
        date_match = re.search(r"(\d{8})", stem)
        product_name = re.sub(r"[-_](TOP|BOT)\b", "", stem, flags=re.IGNORECASE)
        return FileInfo(
            file_name=path.name,
            file_path=str(path),
            program_name=stem,
            product_name=product_name,
            date_code=date_match.group(1) if date_match else "",
            side=side_match.group(1).upper() if side_match else "",
            exported_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    def _fill_file_info_from_xml(
        self,
        root: ET.Element,
        file_info: FileInfo,
        machine_defs: list[dict[str, str]],
    ) -> None:
        line_name = root.find(".//lineName")
        if line_name is not None and (line_name.text or "").strip():
            file_info.line_name = (line_name.text or "").strip()

        file_info.machines = machine_defs
        for machine in machine_defs:
            text = machine.get("name", "").strip()
            if text:
                file_info.machine_name = text
                break

        reference_side = root.find(".//referenceSide")
        if reference_side is not None and not file_info.side:
            text = (reference_side.text or "").strip().upper()
            file_info.side = {"FRONT": "TOP", "BACK": "BOT"}.get(text, text)

    def _parse_components(self, root: ET.Element, warnings: list[ParseWarning]) -> list[ComponentRecord]:
        result: list[ComponentRecord] = []
        for component in root.findall(".//componentData/component"):
            component_basic = component.find("./componentBasic")
            data_source = component_basic if component_basic is not None else component
            component_name = self._read_text_from_candidates(data_source, self.FIELD_ALIASES["component_name"])
            if not component_name:
                warnings.append(ParseWarning("warning", "存在缺少 componentName 的 component 节点"))
                continue

            package_code = ""
            package_node = data_source.find("./packageCode")
            if package_node is not None:
                package_code = package_node.attrib.get("Name", "") or package_node.attrib.get("ID", "")

            size_node = data_source.find("./componentSize")
            result.append(
                ComponentRecord(
                    component_name=component_name,
                    comment=self._read_text_from_candidates(data_source, self.FIELD_ALIASES["comment"]),
                    package=self._read_text_from_candidates(data_source, self.FIELD_ALIASES["package"]) or package_code,
                    package_code=package_code,
                    width=size_node.attrib.get("width", "") or size_node.attrib.get("witdh", "") if size_node is not None else "",
                    length=size_node.attrib.get("length", "") if size_node is not None else "",
                    height=size_node.attrib.get("height", "") if size_node is not None else "",
                    source_tag=component.tag,
                    extra=self._flatten_node(component),
                )
            )
        return result

    def _parse_placements(self, root: ET.Element, warnings: list[ParseWarning]) -> list[PlacementRecord]:
        result: list[PlacementRecord] = []
        for placement in root.findall(".//placementData/placement"):
            placement_id = self._read_text_from_candidates(placement, self.FIELD_ALIASES["placement_id"])
            component_name = self._read_text_from_candidates(placement, self.FIELD_ALIASES["component_name"])
            if not placement_id and not component_name:
                continue

            pos_node = self._find_child(placement, self.FIELD_ALIASES["position"])
            pos_x, pos_y, raw_position = self._extract_position(pos_node, warnings, placement_id or component_name)
            angle_node = self._find_child(placement, self.FIELD_ALIASES["angle"])
            attribute_node = placement.find("./attribute")

            result.append(
                PlacementRecord(
                    placement_id=placement_id,
                    component_name=component_name,
                    position_raw=raw_position,
                    pos_x=pos_x,
                    pos_y=pos_y,
                    angle=self._extract_value(angle_node, ["angle"]) if angle_node is not None else "",
                    head_no=self._extract_nested_attribute(attribute_node, "head", "placement"),
                    nozzle_no=self._extract_nested_attribute(attribute_node, "nozzle", "placement"),
                    station_no=self._extract_nested_attribute(attribute_node, "station", "placement"),
                    source_tag=placement.tag,
                    extra=self._flatten_node(placement),
                )
            )
        return result

    def _parse_feeders(
        self,
        root: ET.Element,
        warnings: list[ParseWarning],
        machine_defs: list[dict[str, str]],
    ) -> list[FeederRecord]:
        result: list[FeederRecord] = []

        pick_data_nodes = root.findall("./machine/pickData")
        if pick_data_nodes:
            machine_map = {
                str(index): machine
                for index, machine in enumerate(
                    sorted(machine_defs, key=lambda item: int(item.get("no", "9999") or "9999"))
                )
            }
            for pick_data in pick_data_nodes:
                for pick_position in pick_data.findall("./pickPositionData"):
                    pick_index = pick_position.attrib.get("index", "")
                    machine_info = machine_map.get(pick_index, {})
                    for feeder in pick_position.findall("./feederPosition/feeder"):
                        result.append(self._build_feeder_record(feeder, pick_index, machine_info))
                    for tray in pick_position.findall("./trayPosition/tray"):
                        result.append(self._build_tray_record(tray, pick_index, machine_info))
                    for multi_tray in pick_position.findall("./multiTrayPosition/multiTray"):
                        result.append(self._build_tray_record(multi_tray, pick_index, machine_info))
        else:
            feeder_nodes = root.findall(".//feederPosition/feeder")
            for feeder in feeder_nodes:
                result.append(self._build_feeder_record(feeder, "", {}))
            for tray in root.findall(".//trayPosition/tray"):
                result.append(self._build_tray_record(tray, "", {}))
            for multi_tray in root.findall(".//multiTrayPosition/multiTray"):
                result.append(self._build_tray_record(multi_tray, "", {}))

        if not result:
            warnings.append(ParseWarning("warning", "未找到 feeder/tray 节点"))
        return result

    def _build_feeder_record(
        self,
        feeder: ET.Element,
        pick_index: str,
        machine_info: dict[str, str],
    ) -> FeederRecord:
        component_name = self._read_text_from_candidates(feeder, self.FIELD_ALIASES["component_name"])
        position_node = feeder.find("./position")
        feeder_type_node = feeder.find("./feeder")
        pick_node = feeder.find("./pickPosition")
        extra = self._flatten_node(feeder)
        if pick_index:
            extra["pickPositionData.index"] = pick_index
        if machine_info.get("no"):
            extra["machine.no"] = machine_info["no"]
        if machine_info.get("name"):
            extra["machine.name"] = machine_info["name"]

        return FeederRecord(
            component_name=component_name,
            machine_no=machine_info.get("no", ""),
            machine_name=machine_info.get("name", ""),
            pick_index=pick_index,
            hole_no=self._extract_value(position_node, ["holeNo", "slotNo", "hole"]) if position_node is not None else "",
            station_id=self._extract_value(position_node, ["stationId", "station", "stationNo"]) if position_node is not None else "",
            bank_pos=self._extract_value(position_node, ["bankPos", "bankPosition"]) if position_node is not None else "",
            bank_kind=self._extract_value(position_node, ["bankKind", "bankType"]) if position_node is not None else "",
            feeder_type=self._extract_value(feeder_type_node, ["typeId", "reelTypeId", "type"]) if feeder_type_node is not None else "",
            lane=self._read_text_from_candidates(feeder, ["lane"]),
            pick_x=self._extract_value(pick_node, ["x"]) if pick_node is not None else "",
            pick_y=self._extract_value(pick_node, ["y"]) if pick_node is not None else "",
            pick_z=self._extract_value(pick_node, ["z"]) if pick_node is not None else "",
            source_tag=feeder.tag,
            extra=extra,
        )

    def _build_tray_record(
        self,
        tray_node: ET.Element,
        pick_index: str,
        machine_info: dict[str, str],
    ) -> FeederRecord:
        component_name = self._read_text_from_candidates(tray_node, self.FIELD_ALIASES["component_name"])
        position_node = tray_node.find("./position")
        feeder_type_node = tray_node.find("./feeder")
        pick_node = tray_node.find("./pickPosition")
        extra = self._flatten_node(tray_node)
        extra["source.kind"] = tray_node.tag
        if pick_index:
            extra["pickPositionData.index"] = pick_index
        if machine_info.get("no"):
            extra["machine.no"] = machine_info["no"]
        if machine_info.get("name"):
            extra["machine.name"] = machine_info["name"]

        tray_no = self._extract_value(position_node, ["no", "trayNo", "tray", "holeNo", "slotNo", "hole"])
        return FeederRecord(
            component_name=component_name,
            machine_no=machine_info.get("no", ""),
            machine_name=machine_info.get("name", ""),
            pick_index=pick_index,
            hole_no=tray_no,
            station_id=self._extract_value(position_node, ["stationId", "station", "stationNo"]) if position_node is not None else "",
            bank_pos=self._extract_value(position_node, ["bankPos", "bankPosition"]) if position_node is not None else "",
            bank_kind=self._extract_value(position_node, ["bankKind", "bankType"]) if position_node is not None else "",
            feeder_type=self._extract_value(feeder_type_node, ["typeId", "reelTypeId", "type"]) if feeder_type_node is not None else "",
            lane="TRAY",
            pick_x=self._extract_value(pick_node, ["x"]) if pick_node is not None else "",
            pick_y=self._extract_value(pick_node, ["y"]) if pick_node is not None else "",
            pick_z=self._extract_value(pick_node, ["z"]) if pick_node is not None else "",
            source_tag=tray_node.tag,
            extra=extra,
        )

    def _parse_machine_definitions(self, root: ET.Element) -> list[dict[str, Any]]:
        machines: list[dict[str, Any]] = []
        for machine in root.findall("./headerData/lineConfiguration//machine"):
            machine_no = (machine.attrib.get("no") or "").strip()
            machine_name = (machine.findtext("./name") or "").strip()
            if not machine_no or not machine_name:
                continue
            station_ids: list[str] = []
            bank_kinds: list[str] = []
            for station_unit in machine.findall("./stationUnit"):
                station_id = (station_unit.attrib.get("id") or "").strip()
                if station_id and station_id not in station_ids:
                    station_ids.append(station_id)
                for bank_unit in station_unit.findall("./bankUnit"):
                    bank_kind = (bank_unit.attrib.get("kind") or "").strip()
                    if bank_kind and bank_kind not in bank_kinds:
                        bank_kinds.append(bank_kind)

            machines.append(
                {
                    "no": machine_no,
                    "name": machine_name,
                    "station_ids": station_ids,
                    "bank_kinds": bank_kinds,
                    "type_code": (machine.findtext("./typeCode") or "").strip(),
                }
            )
        return machines

    def _extract_position(self, position_node: ET.Element | None, warnings: list[ParseWarning], row_id: str) -> tuple[str, str, str]:
        if position_node is None:
            return "", "", ""
        x = position_node.attrib.get("x", "")
        y = position_node.attrib.get("y", "")
        if x or y:
            return x, y, f"{x},{y}".strip(",")

        raw = (position_node.text or "").strip()
        if not raw:
            return "", "", ""

        parts = [item.strip() for item in raw.split(",")]
        if len(parts) >= 2:
            return parts[0], parts[1], raw

        warnings.append(ParseWarning("warning", f"坐标拆分失败: {row_id} -> {raw}"))
        return "", "", raw

    def _read_text_from_candidates(self, parent: ET.Element, candidates: list[str]) -> str:
        node = self._find_child(parent, candidates)
        if node is None:
            return ""
        return (node.text or "").strip()

    def _find_child(self, parent: ET.Element, candidates: list[str]) -> ET.Element | None:
        lowered = {name.lower() for name in candidates}
        for child in list(parent):
            if child.tag.lower() in lowered:
                return child
        return None

    def _extract_value(self, node: ET.Element | None, keys: list[str]) -> str:
        if node is None:
            return ""
        for key in keys:
            if key in node.attrib:
                return node.attrib.get(key, "")
        return (node.text or "").strip()

    def _extract_nested_attribute(self, parent: ET.Element | None, child_tag: str, attr_name: str) -> str:
        if parent is None:
            return ""
        child = parent.find(f"./{child_tag}")
        if child is None:
            return ""
        return child.attrib.get(attr_name, "")

    def _flatten_node(self, element: ET.Element) -> dict[str, Any]:
        flat: dict[str, Any] = {}
        for node in element.iter():
            if node is element:
                continue
            key_base = node.tag
            text = (node.text or "").strip()
            if text:
                flat.setdefault(key_base, text)
            for attr_key, attr_value in node.attrib.items():
                flat.setdefault(f"{key_base}.{attr_key}", attr_value)
        return flat
