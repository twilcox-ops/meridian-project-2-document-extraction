from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, field_validator, model_validator


class InspectionCert(BaseModel):
    cert_no: str
    unit_id: str
    building: str
    city: str
    state: str
    unit_type: str
    capacity_lbs: Optional[int] = None
    inspection_date: date
    next_due: date
    inspector: str
    result: Literal["PASS", "FAIL", "PASS WITH DEFECTS"]
    invoice_total: Decimal
    defect_count: int

    @field_validator("inspection_date", "next_due", mode="before")
    @classmethod
    def parse_mmddyyyy(cls, value):
        if isinstance(value, str):
            return datetime.strptime(value, "%m/%d/%Y").date()
        return value

    @model_validator(mode="after")
    def check_cross_field_rules(self):
        if self.next_due <= self.inspection_date:
            raise ValueError("next_due must be later than inspection_date")
        if self.invoice_total <= 0:
            raise ValueError("invoice_total must be positive")
        if self.result == "FAIL" and self.defect_count == 0:
            raise ValueError("FAIL result with zero defects is contradictory")
        return self


def demo():
    ok = InspectionCert(
        cert_no="MES-2026-4100", unit_id="D97-6", building="Kestrel Plaza",
        city="Denver", state="CO", unit_type="Freight", capacity_lbs=4000,
        inspection_date="01/13/2026", next_due="01/13/2027", inspector="A. Vasquez",
        result="FAIL", invoice_total="1766.82", defect_count=3,
    )
    assert ok.invoice_total == Decimal("1766.82")

    for bad_field, bad_value in [
        ("next_due", "01/13/2026"),
        ("invoice_total", "0"),
        ("defect_count", 0),
    ]:
        kwargs = dict(
            cert_no="X", unit_id="X", building="X", city="X", state="X",
            unit_type="X", capacity_lbs=None, inspection_date="01/13/2026",
            next_due="01/13/2027", inspector="X", result="FAIL",
            invoice_total="100", defect_count=1,
        )
        kwargs[bad_field] = bad_value
        try:
            InspectionCert(**kwargs)
            raise AssertionError(f"expected validation error for {bad_field}")
        except ValueError:
            pass
    print("ok")


if __name__ == "__main__":
    demo()
