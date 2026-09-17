import csv
import json
import os
from datetime import datetime, timezone

import pdfplumber
import streamlit as st

from confidence import FIELDS
from pipeline import CLEAN_OUTPUT, DATA_DIR, REVIEW_QUEUE

AUDIT_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_log.csv")


def load_queue():
    if not os.path.exists(REVIEW_QUEUE):
        return []
    with open(REVIEW_QUEUE) as f:
        return [json.loads(line) for line in f if line.strip()]


def save_queue(rows):
    with open(REVIEW_QUEUE, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def append_clean_row(file, fields):
    write_header = not os.path.exists(CLEAN_OUTPUT)
    with open(CLEAN_OUTPUT, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file"] + FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow({"file": file, **fields})


def append_audit(reviewer, file, field, action, old_value, new_value):
    write_header = not os.path.exists(AUDIT_LOG)
    with open(AUDIT_LOG, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["timestamp", "reviewer", "file", "field", "action", "old_value", "new_value"])
        writer.writerow([datetime.now(timezone.utc).isoformat(), reviewer, file, field, action, old_value, new_value])


if __name__ == "__main__":
    st.title("Inspection Certificate Review Queue")

    queue = load_queue()
    pending = [r for r in queue if r["status"] == "pending"]

    if not pending:
        st.write("No records pending review.")
        st.stop()

    reviewer = st.text_input("Reviewer name")

    file_names = [r["file"] for r in pending]
    selected_file = st.selectbox("Record", file_names)
    record = next(r for r in pending if r["file"] == selected_file)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("PDF")
        with pdfplumber.open(os.path.join(DATA_DIR, selected_file)) as pdf:
            st.image(pdf.pages[0].to_image(resolution=150).original)

    with col2:
        st.subheader("Extracted fields")
        if record["error"]:
            st.warning(record["error"])

        edited = {}
        for field in FIELDS:
            value = record["fields"].get(field)
            label = field
            if record["confidence"].get(field, 1.0) < 1.0:
                label += " (low confidence)"
            edited[field] = st.text_input(label, value="" if value is None else str(value), key=f"{selected_file}_{field}")

        low_confidence_fields = [f for f in FIELDS if record["confidence"].get(f, 1.0) < 1.0]
        unresolved_fields = [f for f in low_confidence_fields if not edited[f].strip()]

        if low_confidence_fields:
            st.caption(f"Low-confidence/missing fields must be filled in before this record can leave review: {', '.join(low_confidence_fields)}")

        approve_col, correct_col = st.columns(2)

        if approve_col.button("Approve as-is", disabled=not reviewer or bool(low_confidence_fields)):
            for field in FIELDS:
                old_value = record["fields"].get(field)
                append_audit(reviewer, selected_file, field, "approve", old_value, old_value)
            append_clean_row(selected_file, {f: record["fields"].get(f) for f in FIELDS})
            queue.remove(record)
            save_queue(queue)
            st.rerun()

        if correct_col.button("Save corrections", disabled=not reviewer or bool(unresolved_fields)):
            for field in FIELDS:
                old_value = record["fields"].get(field)
                new_value = edited[field]
                action = "correct" if str(old_value) != new_value else "approve"
                append_audit(reviewer, selected_file, field, action, old_value, new_value)
            append_clean_row(selected_file, edited)
            queue.remove(record)
            save_queue(queue)
            st.rerun()
