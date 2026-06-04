from __future__ import annotations

from pydantic import BaseModel


class CalibrationResult(BaseModel):
    n: int
    agreement: float       # fraction of items where judge and human agree (binarized)
    cohen_kappa: float     # chance-corrected agreement


def _binarize(score: float, threshold: float = 0.5) -> int:
    return 1 if score >= threshold else 0


def agreement(human: list[float], judge: list[float], threshold: float = 0.5) -> float:
    if len(human) != len(judge):
        raise ValueError("human and judge score lists must be the same length")
    if not human:
        raise ValueError("cannot compute agreement on empty input")
    matches = sum(
        _binarize(h, threshold) == _binarize(j, threshold) for h, j in zip(human, judge)
    )
    return matches / len(human)


def cohen_kappa(human: list[float], judge: list[float], threshold: float = 0.5) -> float:
    """Binary Cohen's kappa. Returns 1.0 for perfect agreement, 0 for chance, negative for worse."""
    if len(human) != len(judge):
        raise ValueError("human and judge score lists must be the same length")
    n = len(human)
    if n == 0:
        raise ValueError("cannot compute kappa on empty input")
    h = [_binarize(x, threshold) for x in human]
    j = [_binarize(x, threshold) for x in judge]
    po = sum(a == b for a, b in zip(h, j)) / n
    p_yes_h = sum(h) / n
    p_yes_j = sum(j) / n
    pe = p_yes_h * p_yes_j + (1 - p_yes_h) * (1 - p_yes_j)
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def calibrate(human: list[float], judge: list[float], threshold: float = 0.5) -> CalibrationResult:
    return CalibrationResult(
        n=len(human),
        agreement=agreement(human, judge, threshold),
        cohen_kappa=cohen_kappa(human, judge, threshold),
    )
