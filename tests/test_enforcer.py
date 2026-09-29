import pytest

from src.enforcer import enforce
from src.parser import CoverageMetrics


def test_enforce_pass():
    metrics = CoverageMetrics(total_coverage=85.0)

    result = enforce(metrics, 80.0)

    assert result.passed is True
    assert result.coverage == 85.0
    assert result.threshold == 80.0


def test_enforce_fail():
    metrics = CoverageMetrics(total_coverage=75.0)

    result = enforce(metrics, 80.0)

    assert result.passed is False
    assert result.coverage == 75.0
    assert result.threshold == 80.0


def test_enforce_invalid_threshold_below_zero():
    metrics = CoverageMetrics(total_coverage=85.0)

    with pytest.raises(ValueError, match="Threshold must be between 0 and 100"):
        enforce(metrics, -10.0)


def test_enforce_invalid_threshold_above_hundred():
    metrics = CoverageMetrics(total_coverage=85.0)

    with pytest.raises(ValueError, match="Threshold must be between 0 and 100"):
        enforce(metrics, 150.0) 