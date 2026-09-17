import csv
import glob
import json
import os

from confidence import FIELDS, compute_confidence, needs_review
from extract import extract

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "sample-data", "inspection-certs")
CLEAN_OUTPUT = os.path.join(BASE_DIR, "clean_output.csv")
REVIEW_QUEUE = os.path.join(BASE_DIR, "review_queue.jsonl")


def run():
    clean_rows = []
    review_rows = []

    for path in sorted(glob.glob(os.path.join(DATA_DIR, "*.pdf"))):
        file = os.path.basename(path)
        layout, fields, result = extract(path)
        confidence = compute_confidence(fields, result)
        error = str(result) if result.__class__.__name__ == "ValidationError" else None

        if needs_review(confidence, result):
            review_rows.append({
                "file": file,
                "layout": layout,
                "fields": {f: fields.get(f) for f in FIELDS},
                "confidence": confidence,
                "error": error,
                "status": "pending",
            })
        else:
            clean_rows.append({"file": file, **{f: str(fields.get(f)) for f in FIELDS}})

    with open(CLEAN_OUTPUT, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file"] + FIELDS)
        writer.writeheader()
        writer.writerows(clean_rows)

    with open(REVIEW_QUEUE, "w") as f:
        for row in review_rows:
            f.write(json.dumps(row) + "\n")

    print(f"clean: {len(clean_rows)}, review: {len(review_rows)}")


if __name__ == "__main__":
    run()
