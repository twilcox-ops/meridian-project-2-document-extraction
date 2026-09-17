import csv
import os
from collections import defaultdict

from pydantic import ValidationError

from extract import extract

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample-data", "inspection-certs")
GROUND_TRUTH = os.path.join(DATA_DIR, "GROUND_TRUTH.csv")

FIELDS = [
    "cert_no", "unit_id", "building", "city", "state", "unit_type",
    "capacity_lbs", "inspection_date", "next_due", "inspector",
    "result", "invoice_total", "defect_count",
]


def evaluate():
    with open(GROUND_TRUTH, newline="") as f:
        rows = list(csv.DictReader(f))

    layout_totals = defaultdict(lambda: [0, 0])
    field_totals = defaultdict(lambda: [0, 0])
    mismatches = []
    validation_failures = []
    overall = [0, 0]

    print("Detected layout per document:")
    for row in rows:
        path = f"{DATA_DIR}/{row['file']}"
        detected, extracted, result = extract(path)
        print(f"  {row['file']}: {detected}")

        misrouted = detected != row["layout"]
        if misrouted:
            mismatches.append((row["file"], "layout", row["layout"], detected))
        elif isinstance(result, ValidationError):
            validation_failures.append((row["file"], result))

        fields = {} if misrouted else extracted
        for field in FIELDS:
            expected = row[field]
            actual = fields.get(field)
            actual_str = "" if actual is None else str(actual)
            match = (not misrouted) and actual_str == expected

            overall[1] += 1
            layout_totals[row["layout"]][1] += 1
            field_totals[field][1] += 1
            if match:
                overall[0] += 1
                layout_totals[row["layout"]][0] += 1
                field_totals[field][0] += 1
            else:
                mismatches.append((row["file"], field, expected, actual))

    print(f"\nOverall: {overall[0]}/{overall[1]} = {overall[0]/overall[1]:.1%}")

    print("\nBy layout:")
    for layout in sorted(layout_totals):
        correct, total = layout_totals[layout]
        print(f"  {layout}: {correct}/{total} = {correct/total:.1%}")

    print("\nBy field:")
    for field in FIELDS:
        correct, total = field_totals[field]
        print(f"  {field}: {correct}/{total} = {correct/total:.1%}")

    print(f"\nMismatches ({len(mismatches)}):")
    for m in mismatches:
        print(" ", m)

    print(f"\nValidation failures ({len(validation_failures)}):")
    for file, error in validation_failures:
        print(" ", file, "-", error)


if __name__ == "__main__":
    evaluate()
