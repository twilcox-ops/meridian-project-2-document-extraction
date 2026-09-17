import pdfplumber

LABELS = {
    "Certificate No": "cert_no",
    "Unit ID": "unit_id",
    "Building": "building",
    "Address": "address",
    "Unit Type": "unit_type",
    "Capacity (lbs)": "capacity_lbs",
    "Inspection Date": "inspection_date",
    "Next Due": "next_due",
    "Inspector": "inspector",
    "Result": "result",
    "Invoice Total": "invoice_total",
}


def parse_layout_a(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text()

    fields = {}
    defects = []
    in_defects = False
    for line in text.splitlines():
        if line == "Defects Noted:":
            in_defects = True
            continue
        if in_defects and line.startswith("- "):
            defects.append(line[2:])
            continue
        if ": " in line:
            label, value = line.split(": ", 1)
            if label in LABELS:
                fields[LABELS[label]] = value

    if "address" in fields:
        street, city, state_zip = fields.pop("address").split(", ")
        fields["city"] = city
        fields["state"] = state_zip.split()[0]

    if "invoice_total" in fields:
        fields["invoice_total"] = fields["invoice_total"].replace("$", "").replace(",", "")

    fields["defect_count"] = len(defects)
    return fields


def demo():
    result = parse_layout_a("sample-data/inspection-certs/MES-2026-4100.pdf")
    expected = {
        "cert_no": "MES-2026-4100",
        "unit_id": "D97-6",
        "building": "Kestrel Plaza",
        "city": "Denver",
        "state": "CO",
        "unit_type": "Freight",
        "capacity_lbs": "4000",
        "inspection_date": "01/13/2026",
        "next_due": "01/13/2027",
        "inspector": "A. Vasquez",
        "result": "FAIL",
        "invoice_total": "1766.82",
        "defect_count": 3,
    }
    for key, value in expected.items():
        assert result.get(key) == value, f"{key}: {result.get(key)!r} != {value!r}"
    print("ok:", result)


if __name__ == "__main__":
    demo()
