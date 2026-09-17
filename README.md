# Document Extraction With a Review Queue

Extracts structured data from elevator inspection certificate PDFs across
three inconsistent layouts, validates it, and routes anything uncertain to
a human review queue instead of silently guessing. Built against a
36-document synthetic corpus (`sample-data/inspection-certs/`) with a
`GROUND_TRUTH.csv` key, so accuracy is measured, not estimated. A few
documents are deliberately missing their capacity field; the correct
behavior is to flag them for review, never invent a value.

## How it works

Each PDF is classified by layout, parsed deterministically (no LLM),
and validated against a schema with type and business-rule checks. Every
field gets a confidence score. Records that are missing a field, low
confidence, or fail validation go to a review queue instead of clean
output. A small Streamlit app shows the PDF beside the extracted fields
so a reviewer can approve or correct it; every decision is written to an
audit log with who, what, when, and the old and new value. A record can't
leave the queue with an unresolved field still blank.

## Verified results

- Extraction accuracy: 468/468 fields (100%) across all 36 documents, 100%
  for each layout and each field, measured against `GROUND_TRUTH.csv`.
- Layout detection: 36/36 (100%) correct.
- All 4 documents missing capacity are routed to review, none fabricated.
- Review queue routing: 32 clean, 4 review, matching the missing-capacity
  documents exactly.
- Review workflow (display, correction, audit logging, and the gating
  that blocks unresolved fields) manually verified end to end.

## Running it

```
pip install pdfplumber pydantic streamlit
python evaluate.py          # accuracy report against GROUND_TRUTH.csv
python pipeline.py          # run the corpus, produce clean_output.csv / review_queue.jsonl
python -m streamlit run review_ui.py  # review queued records
```

## Known limitations

- Confidence is binary and rule-based, not a probability; no model is
  involved yet.
- Idempotency (reprocessing the same PDF twice) has not been tested.
- Extraction is fully deterministic; no LLM fallback exists yet.
