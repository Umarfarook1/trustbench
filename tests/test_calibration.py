import pytest

from trustbench.evals.calibration import agreement, calibrate, cohen_kappa


def test_agreement_perfect():
    assert agreement([1, 0, 1, 0], [1, 0, 1, 0]) == 1.0


def test_agreement_half():
    assert agreement([1, 1, 0, 0], [1, 0, 0, 1]) == 0.5


def test_agreement_respects_threshold():
    # 0.6 binarizes to 1, 0.4 to 0
    assert agreement([0.6, 0.4], [1.0, 0.0]) == 1.0


def test_kappa_perfect_is_one():
    assert cohen_kappa([1, 0, 1, 0, 1], [1, 0, 1, 0, 1]) == 1.0


def test_kappa_all_same_class_is_one():
    assert cohen_kappa([1, 1, 1], [1, 1, 1]) == 1.0


def test_kappa_in_valid_range():
    human = [1, 0, 1, 0, 1, 0, 1, 0]
    judge = [1, 1, 0, 0, 1, 1, 0, 0]
    k = cohen_kappa(human, judge)
    assert -1.0 <= k <= 1.0


def test_calibrate_returns_struct():
    r = calibrate([1, 0, 1, 1], [1, 0, 0, 1])
    assert r.n == 4
    assert 0.0 <= r.agreement <= 1.0
    assert -1.0 <= r.cohen_kappa <= 1.0


def test_length_mismatch_raises():
    with pytest.raises(ValueError):
        agreement([1, 0], [1])
