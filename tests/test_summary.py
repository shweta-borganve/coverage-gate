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
