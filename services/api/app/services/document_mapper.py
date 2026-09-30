from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation
import re
from typing import Any, Iterable

from app.schemas import ExtractedInvoice, ExtractedLine


ALIASES = {
    "supplier": "vendor",
    "supplier_name": "vendor",
    "vendor_name": "vendor",
    "invoice_id": "invoice_number",
    "invoice_no": "invoice_number",
    "total_cases": "reported_cases",
    "cases_delivered": "reported_cases",
    "total_units": "reported_units",
    "units_delivered": "reported_units",
    "subtotal": "invoice_subtotal",
    "total_due": "invoice_total",
    "line": "line_item",
    "items": "line_item",
    "item": "line_item",
    "product": "line_item",
    "sku": "vendor_sku",
    "item_id": "vendor_sku",
    "product_id": "vendor_sku",
    "product_description": "description",
    "item_description": "description",
    "upc": "printed_upc",
    "barcode": "printed_upc",
    "qty": "case_quantity",
    "quantity": "direct_quantity",
    "units": "units_per_case",
    "pack": "units_per_case",
    "unit_price": "price",
    "product_amount": "base_amount",
    "ext": "line_total",
    "extended_amount": "line_total",
    "total": "line_total",
    "disc": "discount",
    "dep": "deposit",
}

LINE_FIELDS = {
    "vendor_sku",
    "description",
    "printed_upc",
    "case_quantity",
    "units_per_case",
    "direct_quantity",
    "price",
    "base_amount",
    "deposit",
    "discount",
    "sugar_tax",
    "line_total",
}

TOP_FIELDS = {
    "vendor",
    "invoice_number",
    "invoice_date",
    "reported_cases",
    "reported_units",
    "invoice_subtotal",
    "invoice_discount",
    "invoice_deposit",
    "invoice_tax",
    "invoice_total",
}


def normalize_type(value: str) -> str:
    value = value.strip().lower().rsplit("/", 1)[-1]
    value = value.replace("-", "_").replace(" ", "_")
    value = re.sub(r"[^a-z0-9_]+", "", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return ALIASES.get(value, value)


def text_of(entity: Any) -> str:
    normalized = getattr(entity, "normalized_value", None)
    if normalized:
        text = getattr(normalized, "text", None)
        if text:
            return str(text).strip()
    mention = getattr(entity, "mention_text", None)
    return str(mention).strip() if mention else ""


def decimal_or_none(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    text = str(value).strip()
    if not text:
        return None
    negative = text.endswith("-")
    text = text.replace("$", "").replace(",", "").replace("%", "")
    text = re.sub(r"[^0-9.\-]", "", text)
    if negative and not text.startswith("-"):
        text = "-" + text.rstrip("-")
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def int_or_none(value: Any) -> int | None:
    number = decimal_or_none(value)
    if number is None or number != number.to_integral_value():
        return None
    return int(number)


def entity_to_tree(entity: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    grouped: dict[str, list[Any]] = defaultdict(list)
    for prop in getattr(entity, "properties", []) or []:
        grouped[normalize_type(prop.type_)].append(prop)

    for key, props in grouped.items():
        values = []
        for prop in props:
            if getattr(prop, "properties", None):
                values.append(entity_to_tree(prop))
            else:
                values.append(text_of(prop))
        result[key] = values if len(values) > 1 else values[0]

    if not result:
        return {"value": text_of(entity)}
    return result


def _first(value: Any) -> Any:
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _value(value: Any) -> Any:
    value = _first(value)
    if isinstance(value, dict) and set(value) == {"value"}:
        return value["value"]
    return value


def parse_line(data: dict[str, Any], confidence: float | None = None) -> ExtractedLine:
    clean: dict[str, Any] = {}
    for raw_key, raw_value in data.items():
        key = normalize_type(raw_key)
        value = _value(raw_value)
        if key in {"case_quantity", "direct_quantity", "price", "base_amount", "deposit", "discount", "sugar_tax", "line_total"}:
            clean[key] = decimal_or_none(value)
        elif key == "units_per_case":
            clean[key] = int_or_none(value)
        elif key in LINE_FIELDS:
            clean[key] = str(value).strip() if value not in (None, "") else None
    clean["description"] = clean.get("description") or "Unlabeled product"
    clean["confidence"] = confidence
    return ExtractedLine(**clean)


def map_document(document: Any) -> ExtractedInvoice:
    top: dict[str, Any] = {}
    lines: list[ExtractedLine] = []
    raw_entities: list[dict[str, Any]] = []

    for entity in getattr(document, "entities", []) or []:
        entity_type = normalize_type(entity.type_)
        tree = entity_to_tree(entity)
        raw_entities.append({"type": entity.type_, "text": text_of(entity), "tree": tree})

        if entity_type == "line_item":
            lines.append(parse_line(tree, getattr(entity, "confidence", None)))
            continue

        if entity_type in TOP_FIELDS:
            value = text_of(entity)
            if entity_type in {
                "reported_cases",
                "reported_units",
                "invoice_subtotal",
                "invoice_discount",
                "invoice_deposit",
                "invoice_tax",
                "invoice_total",
            }:
                top[entity_type] = decimal_or_none(value)
            else:
                top[entity_type] = value or None
            continue

        # Some custom schemas expose line fields directly as nested parent entities
        if any(normalize_type(k) in LINE_FIELDS for k in tree):
            candidate = parse_line(tree, getattr(entity, "confidence", None))
            if candidate.description != "Unlabeled product" or candidate.vendor_sku:
                lines.append(candidate)

    return ExtractedInvoice(
        **top,
        lines=lines,
        raw={
            "text": getattr(document, "text", ""),
            "entities": raw_entities,
        },
    )
