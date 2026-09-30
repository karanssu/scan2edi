from types import SimpleNamespace

from app.services.document_mapper import decimal_or_none, map_document, normalize_type


def entity(type_, text="", props=None, confidence=0.99):
    return SimpleNamespace(
        type_=type_,
        mention_text=text,
        normalized_value=None,
        properties=props or [],
        confidence=confidence,
    )


def test_decimal_normalization():
    assert str(decimal_or_none("$1,234.56")) == "1234.56"
    assert str(decimal_or_none("4.00-")) == "-4.00"


def test_entity_type_aliases():
    assert normalize_type("line_item/vendor_sku") == "vendor_sku"
    assert normalize_type("supplier_name") == "vendor"


def test_nested_line_item_maps_to_normalized_invoice():
    document = SimpleNamespace(
        text="raw invoice text",
        entities=[
            entity("vendor", "Red Bull Distribution Company Inc"),
            entity("invoice_number", "2037919435"),
            entity("reported_cases", "14"),
            entity("reported_units", "300"),
            entity("invoice_total", "$604.70"),
            entity(
                "line_item",
                props=[
                    entity("line_item/vendor_sku", "RB2861"),
                    entity("line_item/description", "RED BULL 8.4OZ 4PK"),
                    entity("line_item/printed_upc", "611269108026"),
                    entity("line_item/case_quantity", "2"),
                    entity("line_item/units_per_case", "12"),
                    entity("line_item/line_total", "$79.38"),
                ],
                confidence=0.97,
            ),
        ],
    )

    parsed = map_document(document)
    assert parsed.vendor == "Red Bull Distribution Company Inc"
    assert parsed.invoice_number == "2037919435"
    assert str(parsed.reported_cases) == "14"
    assert str(parsed.invoice_total) == "604.70"
    assert len(parsed.lines) == 1
    assert parsed.lines[0].vendor_sku == "RB2861"
    assert parsed.lines[0].printed_upc == "611269108026"
    assert parsed.lines[0].units_per_case == 12
    assert parsed.lines[0].confidence == 0.97
