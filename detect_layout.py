import pdfplumber

MARKERS = {
    "A": "Annual Safety Inspection Certificate",
    "B": "Meridian Elevator Services, Inc.",
    "C": "Premises:",
}


def detect_layout(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text()
    for layout, marker in MARKERS.items():
        if marker in text:
            return layout
    return "UNKNOWN"


def demo():
    cases = {
        "sample-data/inspection-certs/MES-2026-4100.pdf": "A",
        "sample-data/inspection-certs/MES-2026-4101.pdf": "B",
        "sample-data/inspection-certs/MES-2026-4102.pdf": "C",
    }
    for path, expected in cases.items():
        actual = detect_layout(path)
        assert actual == expected, f"{path}: {actual!r} != {expected!r}"
    print("ok")


if __name__ == "__main__":
    demo()
