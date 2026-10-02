import pytest

from src.enforcer import enforce
from src.parser import CoverageMetrics


def test_enforce_pass():
    metrics = CoverageMetrics(total_coverage=85.0)

    result = enforce(metrics, 80.0)

    assert result.passed is True
    assert result.warning is True
    assert result.coverage == 85.0
    assert result.threshold == 80.0
    assert (
        result.message == "Coverage 85.0% vs threshold 80.0% — PASS — "
        "WARNING: Coverage is within 5% of the threshold."
    )


def test_enforce_pass_without_warning():
    metrics = CoverageMetrics(total_coverage=90.0)

    result = enforce(metrics, 80.0)

    assert result.passed is True
    assert result.warning is False
    assert result.coverage == 90.0
    assert result.threshold == 80.0
    assert result.message == "Coverage 90.0% vs threshold 80.0% — PASS"


def test_enforce_warning():
    metrics = CoverageMetrics(total_coverage=83.0)

    result = enforce(metrics, 80.0)

    assert result.passed is True
    assert result.warning is True
    assert result.coverage == 83.0
    assert result.threshold == 80.0


def test_enforce_at_threshold_warning():
    metrics = CoverageMetrics(total_coverage=80.0)

    result = enforce(metrics, 80.0)

    assert result.passed is True
    assert result.warning is True


def test_enforce_fail():
    metrics = CoverageMetrics(total_coverage=75.0)

    result = enforce(metrics, 80.0)

    assert result.passed is False
    assert result.warning is False
    assert result.coverage == 75.0
    assert result.threshold == 80.0
    assert result.message == "Coverage 75.0% vs threshold 80.0% — FAIL"


def test_enforce_invalid_threshold_below_zero():
    metrics = CoverageMetrics(total_coverage=85.0)

    with pytest.raises(ValueError, match="Threshold must be between 0 and 100"):
        enforce(metrics, -10.0)


def test_enforce_invalid_threshold_above_hundred():
    metrics = CoverageMetrics(total_coverage=85.0)

    with pytest.raises(ValueError, match="Threshold must be between 0 and 100"):
        enforce(metrics, 150.0)
