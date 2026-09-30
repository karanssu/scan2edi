import pytest
from pydantic import ValidationError

from app.schemas import LineMappingConfirm


def test_confirmed_upc_strips_spaces_and_hyphens():
    payload = LineMappingConfirm(upc="6112-6910 8026", units_per_case=12)
    assert payload.upc == "611269108026"


def test_confirmed_upc_rejects_non_barcode_length():
    with pytest.raises(ValidationError):
        LineMappingConfirm(upc="1234", units_per_case=12)
