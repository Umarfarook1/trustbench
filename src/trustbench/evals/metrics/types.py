from __future__ import annotations

from pydantic import BaseModel


class MetricResult(BaseModel):
    name: str
    score: float  # normalized 0.0 to 1.0
    passed: bool
    detail: str = ""
