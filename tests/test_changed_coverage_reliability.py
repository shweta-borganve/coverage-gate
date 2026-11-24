from src.changed_coverage import ChangedCoverageReport
from src.enforcer import enforce_changed_coverage


def test_unavailable_changed_coverage_fails_when_threshold_is_positive():
    report = ChangedCoverageReport(
        available=False,
        files=[],
        message="Coverage data is missing.",
    )

    result = enforce_changed_coverage(report, 80.0)

    assert result.passed is False
    assert result.available is False
    assert result.coverage is None
    assert "failed" in result.message
    assert "could not be completed" in result.message


def test_unavailable_changed_coverage_is_skipped_when_threshold_is_zero():
    report = ChangedCoverageReport(
        available=False,
        files=[],
        message="Coverage data is missing.",
    )

    result = enforce_changed_coverage(report, 0.0)

    assert result.passed is True
    assert result.available is False
    assert result.coverage is None
    assert "skipped" in result.message


def test_no_changed_executable_lines_are_skipped_with_positive_threshold():
    report = ChangedCoverageReport(
        available=True,
        files=[],
        message="Changed-code coverage report generated.",
    )

    result = enforce_changed_coverage(report, 80.0)

    assert result.passed is True
    assert result.available is True
    assert result.coverage is None
    assert "no changed executable lines" in result.message


def test_changed_coverage_below_positive_threshold_fails():
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
    assert result.available is True
