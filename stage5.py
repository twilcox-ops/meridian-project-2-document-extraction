import csv
import json
import os

import pdfplumber

from llm_fallback import llm_capacity_fallback
from pipeline import DATA_DIR, REVIEW_QUEUE

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GROUND_TRUTH = os.path.join(DATA_DIR, "GROUND_TRUTH.csv")
RESULTS = os.path.join(BASE_DIR, "stage5_results.jsonl")


def candidates():
    """Records the deterministic pipeline couldn't get capacity_lbs for."""
    with open(REVIEW_QUEUE) as f:
        records = [json.loads(line) for line in f if line.strip()]
    return [r for r in records if r["layout"] == "C" and r["confidence"].get("capacity_lbs") == 0.0]


def run(client=None):
    with open(GROUND_TRUTH, newline="") as f:
        truth = {row["file"]: row["capacity_lbs"] for row in csv.DictReader(f)}

    results = []
    correct_without = 0
    correct_with = 0

    for record in candidates():
        path = os.path.join(DATA_DIR, record["file"])
        with pdfplumber.open(path) as pdf:
            text = pdf.pages[0].extract_text()

        capacity, cost, latency = llm_capacity_fallback(text, client=client)
        expected = truth[record["file"]]

        without_ok = expected == ""  # deterministic parser always returned None here
        with_ok = str(capacity) == expected if capacity is not None else expected == ""
        correct_without += without_ok
        correct_with += with_ok

        results.append({
            "file": record["file"],
            "expected_capacity_lbs": expected or None,
            "llm_capacity_lbs": capacity,
            "cost_usd": cost,
            "latency_s": latency,
        })

    with open(RESULTS, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    n = len(results)
    total_cost = sum(r["cost_usd"] for r in results)
    total_latency = sum(r["latency_s"] for r in results)
    print(f"documents: {n}")
    print(f"capacity_lbs accuracy without fallback: {correct_without}/{n}")
    print(f"capacity_lbs accuracy with fallback: {correct_with}/{n}")
    print(f"total cost: ${total_cost:.6f} (${total_cost/n:.6f}/doc)" if n else "total cost: $0")
    print(f"total latency: {total_latency:.2f}s ({total_latency/n:.2f}s/doc)" if n else "total latency: 0s")
    return results


if __name__ == "__main__":
    run()
