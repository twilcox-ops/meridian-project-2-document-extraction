from pydantic import ValidationError

from schema import InspectionCert

FIELDS = list(InspectionCert.model_fields.keys())
THRESHOLD = 1.0


def compute_confidence(fields, result):
    """1.0 if the field extracted and passed its type/shape check, else 0.0."""
    bad_fields = set()
    if isinstance(result, ValidationError):
        for err in result.errors():
            if err["loc"]:
                bad_fields.add(err["loc"][0])
    return {
        f: 0.0 if fields.get(f) is None or f in bad_fields else 1.0
        for f in FIELDS
    }


def needs_review(confidence, result):
    """Below-threshold field, or a validation failure (incl. cross-field rules)."""
    if isinstance(result, ValidationError):
        return True
    return any(c < THRESHOLD for c in confidence.values())


def demo():
    from extract import extract
    import os

    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample-data", "inspection-certs")

    _, fields, result = extract(os.path.join(base, "MES-2026-4100.pdf"))
    conf = compute_confidence(fields, result)
    assert all(v == 1.0 for v in conf.values())
    assert not needs_review(conf, result)

    _, fields, result = extract(os.path.join(base, "MES-2026-4102.pdf"))
    conf = compute_confidence(fields, result)
    assert conf["capacity_lbs"] == 0.0
    assert needs_review(conf, result)
    print("ok")


if __name__ == "__main__":
    demo()
