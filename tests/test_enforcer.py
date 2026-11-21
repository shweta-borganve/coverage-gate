import pytest

from src.changed_coverage import ChangedCoverageReport
from src.enforcer import enforce, enforce_changed_coverage
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
        "WARNING: Coverage is within 5.0% of the threshold."
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


def test_enforce_custom_warning_margin():
    metrics = CoverageMetrics(total_coverage=87.0)

    result = enforce(metrics, 80.0, warning_margin=10.0)

    assert result.passed is True
    assert result.warning is True
    assert result.message == (
        "Coverage 87.0% vs threshold 80.0% — PASS — "
        "WARNING: Coverage is within 10.0% of the threshold."
    )


def test_enforce_custom_warning_margin_without_warning():
    metrics = CoverageMetrics(total_coverage=91.0)

    result = enforce(metrics, 80.0, warning_margin=10.0)

    assert result.passed is True
    assert result.warning is False
    assert result.message == "Coverage 91.0% vs threshold 80.0% — PASS"


def test_enforce_invalid_threshold_below_zero():
    metrics = CoverageMetrics(total_coverage=85.0)

    with pytest.raises(ValueError, match="Threshold must be between 0 and 100"):
        enforce(metrics, -10.0)


def test_enforce_invalid_threshold_above_hundred():
    metrics = CoverageMetrics(total_coverage=85.0)

    with pytest.raises(ValueError, match="Threshold must be between 0 and 100"):
        enforce(metrics, 150.0)


def test_enforce_invalid_warning_margin_below_zero():
    metrics = CoverageMetrics(total_coverage=85.0)

    with pytest.raises(
        ValueError,
        match="Warning margin must be between 0 and 100",
    ):
        enforce(metrics, 80.0, warning_margin=-5.0)


def test_enforce_invalid_warning_margin_above_hundred():
    metrics = CoverageMetrics(total_coverage=85.0)

    with pytest.raises(
        ValueError,
        match="Warning margin must be between 0 and 100",
    ):
        enforce(metrics, 80.0, warning_margin=150.0)


def test_enforce_no_regression():
    metrics = CoverageMetrics(total_coverage=86.0)

    result = enforce(
        metrics,
        80.0,
        baseline_coverage=90.0,
        max_regression=5.0,
    )

    assert result.passed is True
    assert result.regression is False
    assert result.baseline_coverage == 90.0
    assert result.regression_amount == 4.0


def test_enforce_detects_regression():
    metrics = CoverageMetrics(total_coverage=84.0)

    result = enforce(
        metrics,
        80.0,
        baseline_coverage=90.0,
        max_regression=5.0,
    )

    assert result.passed is False
    assert result.regression is True
    assert result.baseline_coverage == 90.0
    assert result.regression_amount == 6.0
    assert "REGRESSION" in result.message


def test_enforce_at_max_regression_limit():
    metrics = CoverageMetrics(total_coverage=85.0)

    result = enforce(
        metrics,
        80.0,
        baseline_coverage=90.0,
        max_regression=5.0,
    )

    assert result.passed is True
    assert result.regression is False
    assert result.regression_amount == 5.0


def test_enforce_coverage_improvement_is_not_regression():
    metrics = CoverageMetrics(total_coverage=90.0)

    result = enforce(
        metrics,
        80.0,
        baseline_coverage=80.0,
        max_regression=5.0,
    )

    assert result.passed is True
    assert result.regression is False
    assert result.regression_amount == -10.0


def test_enforce_invalid_baseline_coverage():
    metrics = CoverageMetrics(total_coverage=85.0)

    with pytest.raises(
        ValueError,
        match="Baseline coverage must be between 0 and 100",
    ):
        enforce(
            metrics,
            80.0,
            baseline_coverage=110.0,
        )


def test_enforce_invalid_max_regression():
    metrics = CoverageMetrics(total_coverage=85.0)

    with pytest.raises(
        ValueError,
        match="Maximum regression must be between 0 and 100",
    ):
        enforce(
            metrics,
            80.0,
            max_regression=-5.0,
        )


def test_enforce_changed_coverage_pass():
    report = ChangedCoverageReport(
        available=True,
        files=[],
        message="Changed-code coverage report generated.",
        total_changed_lines=10,
        covered_changed_lines=9,
        coverage_percentage=90.0,
    )

    result = enforce_changed_coverage(report, 80.0)

    assert result.passed is True
    assert result.coverage == 90.0
    assert result.threshold == 80.0
    assert result.available is True
    assert result.message == ("Changed-line coverage 90.0% vs threshold 80.0% — PASS")


def test_enforce_changed_coverage_fail():
    report = ChangedCoverageReport(
        available=True,
        files=[],
        message="Changed-code coverage report generated.",
        total_changed_lines=10,
        covered_changed_lines=6,
        coverage_percentage=60.0,
    )

    result = enforce_changed_coverage(report, 80.0)

    assert result.passed is False
    assert result.coverage == 60.0
    assert result.threshold == 80.0
    assert result.available is True
    assert result.message == ("Changed-line coverage 60.0% vs threshold 80.0% — FAIL")


def test_enforce_changed_coverage_at_threshold():
    report = ChangedCoverageReport(
        available=True,
        files=[],
        message="Changed-code coverage report generated.",
        total_changed_lines=10,
        covered_changed_lines=8,
        coverage_percentage=80.0,
    )

    result = enforce_changed_coverage(report, 80.0)

    assert result.passed is True
    assert result.coverage == 80.0


def test_enforce_changed_coverage_unavailable():
    report = ChangedCoverageReport(
        available=False,
        files=[],
        message="Coverage data is missing.",
    )

    result = enforce_changed_coverage(report, 80.0)

    assert result.passed is True
    assert result.coverage is None
    assert result.available is False
    assert "skipped" in result.message


def test_enforce_changed_coverage_no_changed_lines():
    report = ChangedCoverageReport(
        available=True,
        files=[],
        message="Changed-code coverage report generated.",
    )

    result = enforce_changed_coverage(report, 80.0)

    assert result.passed is True
    assert result.coverage is None
    assert result.available is True
    assert "no changed lines" in result.message


@pytest.mark.parametrize("threshold", [-1.0, 101.0])
def test_enforce_changed_coverage_invalid_threshold(threshold):
    report = ChangedCoverageReport(
        available=True,
        files=[],
        message="Changed-code coverage report generated.",
        total_changed_lines=10,
        covered_changed_lines=9,
        coverage_percentage=90.0,
    )

    with pytest.raises(
        ValueError,
        match="Changed-lines threshold must be between 0 and 100",
    ):
        enforce_changed_coverage(report, threshold)
