import pdfplumber

UNIT_TYPES = ["Hydraulic Passenger", "Traction Passenger", "Escalator", "Freight"]

LABELS = {
    "Date of Inspection ": "inspection_date",
    "Re-inspection Due ": "next_due",
    "Certified By ": "inspector",
    "Disposition ": "result",
    "Amount Billed ": "invoice_total",
}


def parse_layout_b(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        lines = pdf.pages[0].extract_text().splitlines()

    fields = {}

    cert_line = lines[2].removeprefix("CERT ")
    fields["cert_no"], fields["unit_id"] = cert_line.split(" Unit: ")

    building_type_line = lines[3]
    match = next((t for t in UNIT_TYPES if building_type_line.endswith(t)), None)
    if match is None:
        fields["building"] = None
        fields["unit_type"] = None
    else:
        fields["unit_type"] = match
        fields["building"] = building_type_line[: -len(match)].strip()

    capacity_line = lines[4].removesuffix(" lb")
    fields["capacity_lbs"] = capacity_line.rsplit(" ", 1)[1]

    city, state_zip = lines[5].split(", ")
    fields["city"] = city
    fields["state"] = state_zip.split()[0]

    defects = []
    in_defects = False
    for line in lines[6:]:
        if line == "DEFICIENCIES":
            in_defects = True
            continue
        if in_defects and line[:1].isdigit() and line[1:3] == ". ":
            defects.append(line.split(". ", 1)[1])
            continue
        for prefix, key in LABELS.items():
            if line.startswith(prefix):
                fields[key] = line[len(prefix):]
                break

    fields["invoice_total"] = fields["invoice_total"].replace("$", "").replace(",", "")
    fields["defect_count"] = len(defects)
    return fields


def demo():
    result = parse_layout_b("sample-data/inspection-certs/MES-2026-4113.pdf")
    expected = {
        "cert_no": "MES-2026-4113",
        "unit_id": "B95-6",
        "building": "Alder Commons",
        "unit_type": "Freight",
        "capacity_lbs": "2100",
        "city": "Boise",
        "state": "ID",
        "inspection_date": "06/09/2026",
        "next_due": "06/09/2027",
        "inspector": "T. Moreau",
        "result": "FAIL",
        "invoice_total": "285.82",
        "defect_count": 2,
    }
    for key, value in expected.items():
        assert result.get(key) == value, f"{key}: {result.get(key)!r} != {value!r}"
    print("ok:", result)


if __name__ == "__main__":
    demo()
