from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from config import (
    CUSTOMER_EXPORT_FIELDS,
    CUSTOMER_EXPORT_FIELD_LABELS,
    CUSTOMER_EXPORT_HEADERS,
    CUSTOMER_EXPORT_LAYOUT_DEFAULTS,
    CUSTOMER_STATION_NUMBER_MAPPING_DEFAULTS,
    CUSTOMER_EXPORT_SETTINGS_PATH,
    SETTINGS_DIR,
)


def default_customer_export_settings() -> dict[str, Any]:
    return {
        "fields": list(CUSTOMER_EXPORT_FIELDS),
        "headers": deepcopy(CUSTOMER_EXPORT_HEADERS),
        "layout": deepcopy(CUSTOMER_EXPORT_LAYOUT_DEFAULTS),
        "station_number_mapping": deepcopy(CUSTOMER_STATION_NUMBER_MAPPING_DEFAULTS),
    }


def load_customer_export_settings() -> dict[str, Any]:
    defaults = default_customer_export_settings()
    path = CUSTOMER_EXPORT_SETTINGS_PATH
    if not path.exists():
        return defaults

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return defaults

    fields = data.get("fields", [])
    headers = data.get("headers", {})
    layout = data.get("layout", {})
    station_number_mapping = data.get("station_number_mapping", {})
    if not station_number_mapping and "station_padding" in data:
        station_number_mapping = data.get("station_padding", {})

    valid_fields = [field for field in fields if field in CUSTOMER_EXPORT_FIELD_LABELS]
    for field in CUSTOMER_EXPORT_FIELDS:
        if field not in valid_fields:
            default_index = CUSTOMER_EXPORT_FIELDS.index(field)
            insert_at = len(valid_fields)
            for later_field in CUSTOMER_EXPORT_FIELDS[default_index + 1:]:
                if later_field in valid_fields:
                    insert_at = valid_fields.index(later_field)
                    break
            valid_fields.insert(insert_at, field)

    valid_headers = deepcopy(defaults["headers"])
    for field in valid_fields:
        if field in headers and str(headers[field]).strip():
            valid_headers[field] = str(headers[field]).strip()

    return {
        "fields": valid_fields,
        "headers": valid_headers,
        "layout": _normalize_layout(layout, defaults["layout"]),
        "station_number_mapping": _normalize_station_number_mapping(
            station_number_mapping,
            defaults["station_number_mapping"],
        ),
    }


def save_customer_export_settings(settings: dict[str, Any]) -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    normalized = load_customer_export_settings()
    normalized["fields"] = [field for field in settings.get("fields", []) if field in CUSTOMER_EXPORT_FIELD_LABELS]

    headers = settings.get("headers", {})
    for field in normalized["fields"]:
        text = str(headers.get(field, "")).strip()
        if text:
            normalized["headers"][field] = text

    normalized["layout"] = _normalize_layout(settings.get("layout", {}), normalized["layout"])
    station_number_mapping = settings.get("station_number_mapping", {})
    if not station_number_mapping and "station_padding" in settings:
        station_number_mapping = settings.get("station_padding", {})
    normalized["station_number_mapping"] = _normalize_station_number_mapping(
        station_number_mapping,
        normalized["station_number_mapping"],
    )

    CUSTOMER_EXPORT_SETTINGS_PATH.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _normalize_layout(layout: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(defaults)
    line_label = str(layout.get("line_label", normalized["line_label"])).strip()
    line_value = str(layout.get("line_value", normalized["line_value"])).strip()
    machine_label = str(layout.get("machine_label", normalized["machine_label"])).strip()

    if line_label:
        normalized["line_label"] = line_label
    normalized["line_value"] = line_value
    if machine_label:
        normalized["machine_label"] = machine_label

    normalized["split_by_station_group"] = bool(layout.get("split_by_station_group", normalized["split_by_station_group"]))
    return normalized


def _normalize_station_number_mapping(settings: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(defaults)
    if "enabled_machine_patterns" in settings:
        raw_patterns = settings.get("enabled_machine_patterns", [])
        if not isinstance(raw_patterns, list):
            raw_patterns = []
    else:
        raw_patterns = normalized["enabled_machine_patterns"]

    patterns: list[str] = []
    for item in raw_patterns:
        text = str(item or "").strip()
        if text and text not in patterns:
            patterns.append(text)

    normalized["enabled_machine_patterns"] = patterns
    return normalized
