import re
import pdfplumber

COLUMN_LABELS = [
    ("Premises:", "building", "Equipment No.:", "unit_id"),
    ("Street:", None, "Classification:", "unit_type"),
    ("Municipality:", "city_state", "Rated Load:", "capacity_lbs"),
    ("Postal:", None, "Outcome:", "result"),
]


def parse_layout_c(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text()
    lines = text.splitlines()
    joined = " ".join(lines)

    fields = {}

    date, inspector = re.search(r"examined on (\S+) by ([^,]+), acting", joined).groups()
    fields["inspection_date"] = date
    fields["inspector"] = inspector

    fields["cert_no"] = re.search(r"certificate reference (\S+) and", joined).group(1)

    amount, next_due = re.search(
        r"total \$([\d,]+\.\d{2}), payable net 30\. Re-examination shall occur no later than (\S+)\.",
        joined,
    ).groups()
    fields["invoice_total"] = amount.replace(",", "")
    fields["next_due"] = next_due

    for left_label, left_key, right_label, right_key in COLUMN_LABELS:
        line = next(l for l in lines if l.startswith(left_label))
        left_part, right_part = line.split(right_label)
        left_value = left_part.removeprefix(left_label).strip()
        right_value = right_part.strip()
        if left_key:
            fields[left_key] = left_value
        fields[right_key] = right_value

    city, state = fields.pop("city_state").split(", ")
    fields["city"] = city
    fields["state"] = state

    first_token = fields["capacity_lbs"].split()[0]
    fields["capacity_lbs"] = first_token if first_token.isdigit() else None

    defects = [
        line.removeprefix("(cid:127)").strip()
        for line in lines
        if line.startswith("(cid:127)")
    ]
    fields["defect_count"] = len(defects)

    return fields


def demo():
    result = parse_layout_c("sample-data/inspection-certs/MES-2026-4102.pdf")
    expected = {
        "cert_no": "MES-2026-4102",
        "unit_id": "E11-2",
        "building": "Harborview Tower",
        "city": "Portland",
        "state": "OR",
        "unit_type": "Freight",
        "capacity_lbs": None,
        "inspection_date": "04/02/2026",
        "next_due": "04/02/2027",
        "inspector": "D. Whitfield",
        "result": "FAIL",
        "invoice_total": "1001.53",
        "defect_count": 3,
    }
    for key, value in expected.items():
        assert result.get(key) == value, f"{key}: {result.get(key)!r} != {value!r}"
    print("ok:", result)


if __name__ == "__main__":
    demo()
