from src.changed_coverage import ChangedCoverageReport, ChangedFileCoverage
from src.enforcer import EnforcementResult
from src.summary import generate_summary


def test_summary_includes_coverage_and_pass_status():
    result = EnforcementResult(
        passed=True,
        warning=False,
        regression=False,
        coverage=85.0,
        threshold=80.0,
        baseline_coverage=None,
        regression_amount=0.0,
        message="Coverage passed",
    )

    summary = generate_summary(result)

    assert "85.0%" in summary
    assert "80.0%" in summary
    assert "**Status:** PASS" in summary
    assert "**Warning:** No" in summary
    assert "Not checked (no baseline configured)" in summary


def test_summary_includes_fail_status():
    result = EnforcementResult(
        passed=False,
        warning=False,
        regression=False,
        coverage=70.0,
        threshold=80.0,
        baseline_coverage=None,
        regression_amount=0.0,
        message="Coverage failed",
    )

    summary = generate_summary(result)

    assert "**Status:** FAIL" in summary
    assert "**Coverage:** 70.0%" in summary
    assert "**Required threshold:** 80.0%" in summary


def test_summary_includes_warning_status():
    result = EnforcementResult(
        passed=True,
        warning=True,
        regression=False,
        coverage=77.0,
        threshold=75.0,
        baseline_coverage=None,
        regression_amount=0.0,
        message="Coverage warning",
    )

    summary = generate_summary(result)

    assert "**Warning:** Yes" in summary


def test_summary_includes_regression_details():
    result = EnforcementResult(
        passed=True,
        warning=False,
        regression=True,
        coverage=80.0,
        threshold=75.0,
        baseline_coverage=85.0,
        regression_amount=5.0,
        message="Coverage passed",
    )

    summary = generate_summary(result)

    assert "**Regression:** Yes" in summary
    assert "5.0 percentage points" in summary
    assert "85.0%" in summary


def test_summary_includes_per_file_coverage():
    result = EnforcementResult(
        passed=True,
        warning=False,
        regression=False,
        coverage=80.0,
        threshold=80.0,
        baseline_coverage=None,
        regression_amount=0.0,
        message="Coverage passed",
    )

    file_coverage = {
        "src/module_a.py": 90.0,
        "src/module_b.py": 60.0,
    }

    summary = generate_summary(result, file_coverage)

    assert "### Per-file Coverage" in summary
    assert "| File | Coverage |" in summary
    assert "| `src/module_a.py` | 90.0% |" in summary
    assert "| `src/module_b.py` | 60.0% |" in summary


def test_summary_includes_changed_code_coverage():
    result = EnforcementResult(
        passed=True,
        warning=False,
        regression=False,
        coverage=85.0,
        threshold=80.0,
        baseline_coverage=None,
        regression_amount=0.0,
        message="Coverage passed",
    )

    changed_coverage = ChangedCoverageReport(
        available=True,
        files=[
            ChangedFileCoverage(
                filename="src/parser.py",
                changed_lines=3,
                covered_lines=1,
                uncovered_lines=2,
                uncovered_line_numbers=[11, 12],
            )
        ],
        message="Changed-code coverage report generated.",
    )

    summary = generate_summary(
        result,
        changed_coverage=changed_coverage,
    )

    assert "### Changed-Code Coverage" in summary
    assert "`src/parser.py`" in summary
    assert "| `src/parser.py` | 3 | 1 | 2 | 11, 12 |" in summary


def test_summary_reports_unavailable_changed_code_coverage():
    result = EnforcementResult(
        passed=True,
        warning=False,
        regression=False,
        coverage=85.0,
        threshold=80.0,
        baseline_coverage=None,
        regression_amount=0.0,
        message="Coverage passed",
    )

    changed_coverage = ChangedCoverageReport(
        available=False,
        files=[],
        message="Changed-code coverage not available: line data is missing.",
    )

    summary = generate_summary(
        result,
        changed_coverage=changed_coverage,
    )

    assert "Changed-Code Coverage" in summary
    assert "Not available" in summary
    assert "line data is missing" in summary
