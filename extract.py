import os

from pydantic import ValidationError

from detect_layout import detect_layout
from parse_layout_a import parse_layout_a
from parse_layout_b import parse_layout_b
from parse_layout_c import parse_layout_c
from schema import InspectionCert

PARSERS = {"A": parse_layout_a, "B": parse_layout_b, "C": parse_layout_c}


def extract(pdf_path):
    """detect -> parse -> validate. Returns (layout, fields_dict, record_or_error_or_None)."""
    layout = detect_layout(pdf_path)
    if layout not in PARSERS:
        return layout, {}, None

    fields = PARSERS[layout](pdf_path)
    try:
        record = InspectionCert(**fields)
    except ValidationError as e:
        return layout, fields, e
    return layout, fields, record


def demo():
    sample = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..",
        "sample-data", "inspection-certs", "MES-2026-4100.pdf",
    )
    layout, fields, result = extract(sample)
    assert layout == "A"
    assert fields["cert_no"] == "MES-2026-4100"
    assert not isinstance(result, ValidationError)
    print("ok:", layout, result)


if __name__ == "__main__":
    demo()
