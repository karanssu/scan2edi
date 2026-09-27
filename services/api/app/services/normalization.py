import re


def normalize_description(value: str) -> str:
    value = value.upper().strip()
    value = re.sub(r"[^A-Z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()
