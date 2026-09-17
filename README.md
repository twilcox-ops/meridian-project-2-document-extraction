# Document Extraction With a Review Queue

Extracts structured data from elevator inspection certificate PDFs across
three inconsistent layouts, validates it, and routes anything uncertain to
a human review queue instead of silently guessing. Built against a
36-document synthetic corpus (`sample-data/inspection-certs/`) with a
`GROUND_TRUTH.csv` key, so accuracy is measured, not estimated.

## Why

Most business documents are PDFs designed for humans, not machines. The
gap between "a script that mostly works" and a pipeline someone would
trust with money is where the value is. The corpus deliberately includes a
few documents missing their capacity field entirely; the correct behavior
is to flag them for review, never to invent a plausible number.

## Architecture

```
PDF -> detect_layout() -> parse_layout_[a|b|c]() -> InspectionCert (Pydantic) -> confidence + routing
                                                                                      |
                                                                    clean_output.csv  or  review_queue.jsonl
                                                                                              |
                                                                                    review_ui.py (Streamlit)
                                                                                              |
                                                                          clean_output.csv + audit_log.csv
```

- **`detect_layout.py`**: classifies each PDF as Layout A, B, or C using a
  fixed text marker unique to each layout.
- **`parse_layout_a.py` / `parse_layout_b.py` / `parse_layout_c.py`**:
  one deterministic `pdfplumber`-based parser per layout (no LLM). Layout A
  is a clean label/value form, Layout B has an unlabeled positional header
  block, Layout C embeds fields in prose and two-column labels with
  different wording, and can genuinely be missing the capacity field.
- **`schema.py`**: `InspectionCert`, a Pydantic model enforcing field
  types plus three cross-field rules: `next_due` must be later than
  `inspection_date`, `invoice_total` must be positive, and a `FAIL` result
  with zero defects is contradictory.
- **`extract.py`**: the single detect → parse → validate entry point used
  by everything else.
- **`confidence.py`**: assigns each field a rule-based confidence: `1.0`
  if it was extracted and passed its expected type/shape, `0.0` if missing
  or malformed. These are states, not probabilities; the pipeline is
  fully deterministic through Stage 4.
- **`pipeline.py`**: runs the full corpus through extraction and routes
  each record to `clean_output.csv` (validated, all fields confident) or
  `review_queue.jsonl` (anything missing, low-confidence, or failing a
  validation rule).
- **`review_ui.py`**: a small Streamlit app showing the PDF page beside
  the extracted fields for each queued record. A reviewer enters their
  name, edits fields as needed, and either **Approve as-is** or **Save
  corrections**. Both require a reviewer name. **Approve as-is** is also
  disabled whenever any field is missing or low-confidence, since it can't
  supply a value; **Save corrections** is disabled until every such field
  has an edited value. A record can't leave the queue with an unresolved
  gap. Every decision is appended to `audit_log.csv`
  with timestamp, reviewer, file, field, action, and old/new value.
- **`evaluate.py`**: the accuracy harness: runs all 36 documents through
  `extract()` and reports overall/per-layout/per-field accuracy against
  `GROUND_TRUTH.csv`, plus any layout misroutes or field mismatches.

## Running it

From this directory:

```
pip install pdfplumber pydantic streamlit
python evaluate.py          # accuracy report against GROUND_TRUTH.csv
python pipeline.py          # run the corpus, produce clean_output.csv / review_queue.jsonl
python -m streamlit run review_ui.py  # review queued records
```

## Verified results (Stages 1–4)

- **Extraction accuracy**: 468/468 fields (100%) across all 36 documents,
  broken out at 156/156 (100%) for each of Layouts A, B, and C, and 100%
  for every individual field, measured by `evaluate.py` against
  `GROUND_TRUTH.csv`.
- **Layout detection**: 36/36 (100%) correctly classified.
- **Missing-capacity handling**: all 4 documents missing the capacity
  field are routed to the review queue with the field explicitly `None`;
  none receive a fabricated value.
- **Review queue routing**: 32 clean / 4 review on the full corpus,
  matching the 4 known missing-capacity documents exactly.
- **Review workflow**: manually verified end-to-end: PDF/field display,
  correction with audit logging, and the approve/correction gating that
  blocks an unresolved field from reaching clean output.
- **Validation-failure routing** (a record failing a cross-field rule
  rather than missing a field) is verified via a controlled test, since no
  document in this corpus actually violates a cross-field rule; the
  routing and audit logic are the same code path already exercised above.

## Known limitations

- Confidence is currently binary and rule-based (extraction succeeded or
  it didn't); there's no probabilistic model in the loop yet.
- Idempotency (reprocessing the same PDF twice produces identical output)
  has not yet been formally tested.
- All extraction is deterministic; no LLM fallback exists at this stage.
