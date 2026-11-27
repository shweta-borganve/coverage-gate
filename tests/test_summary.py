from src.changed_coverage import ChangedCoverageReport, ChangedFileCoverage
from src.enforcer import ChangedCoverageEnforcementResult, EnforcementResult
from src.summary import generate_summary


def get_changed_enforcement_section(summary):
    heading = "### Changed-Line Coverage Enforcement"
    return summary.split(heading, 1)[1]


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
        "src/parser.py": 90.0,
        "src/enforcer.py": 60.0,
    }

    summary = generate_summary(result, file_coverage)

    assert "### Per-file Coverage" in summary
    assert "<details>" in summary
    assert "<summary>Show per-file coverage</summary>" in summary
    assert "| File | Coverage |" in summary
    assert "| `src/enforcer.py` | 60.0% |" in summary
    assert "| `src/parser.py` | 90.0% |" in summary
    assert "</details>" in summary


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


def test_summary_reports_fail_when_changed_coverage_is_unavailable():
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

    changed_enforcement = ChangedCoverageEnforcementResult(
        passed=False,
        coverage=None,
        threshold=80.0,
        available=False,
        message="Changed-line coverage enforcement failed: coverage data is unavailable.",
    )

    summary = generate_summary(
        result,
        changed_enforcement=changed_enforcement,
    )
    section = get_changed_enforcement_section(summary)

    assert "- **Status:** FAIL" in section
    assert (
        "- **Details:** Changed-line coverage enforcement failed: "
        "coverage data is unavailable."
    ) in section
    assert "Changed-line coverage is unavailable." not in section


def test_summary_reports_skipped_when_unavailable_and_not_required():
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

    changed_enforcement = ChangedCoverageEnforcementResult(
        passed=True,
        coverage=None,
        threshold=0.0,
        available=False,
        message="No positive changed-line threshold was configured.",
    )

    summary = generate_summary(
        result,
        changed_enforcement=changed_enforcement,
    )
    section = get_changed_enforcement_section(summary)

    assert "- **Status:** Skipped" in section
    assert "No positive changed-line threshold was configured." in section


def test_summary_reports_skipped_when_no_changed_executable_lines():
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

    changed_enforcement = ChangedCoverageEnforcementResult(
        passed=True,
        coverage=None,
        threshold=80.0,
        available=True,
        message="No changed executable lines were found.",
    )

    summary = generate_summary(
        result,
        changed_enforcement=changed_enforcement,
    )
    section = get_changed_enforcement_section(summary)

    assert "Not applicable (no changed lines)" in section
    assert "- **Status:** Skipped" in section


def test_summary_reports_pass_for_changed_line_coverage():
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

    changed_enforcement = ChangedCoverageEnforcementResult(
        passed=True,
        coverage=90.0,
        threshold=80.0,
        available=True,
        message="Changed-line coverage passed",
    )

    summary = generate_summary(
        result,
        changed_enforcement=changed_enforcement,
    )
    section = get_changed_enforcement_section(summary)

    assert "- **Coverage:** 90.0%" in section
    assert "- **Status:** PASS" in section


def test_summary_reports_fail_for_changed_line_coverage():
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

    changed_enforcement = ChangedCoverageEnforcementResult(
        passed=False,
        coverage=60.0,
        threshold=80.0,
        available=True,
        message="Changed-line coverage failed",
    )

    summary = generate_summary(
        result,
        changed_enforcement=changed_enforcement,
    )
    section = get_changed_enforcement_section(summary)

    assert "- **Coverage:** 60.0%" in section
    assert "- **Status:** FAIL" in section


def test_summary_reports_non_pr_event_as_skipped():
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

    changed_enforcement = ChangedCoverageEnforcementResult(
        passed=True,
        coverage=None,
        threshold=80.0,
        available=False,
        message=(
            "Changed-line coverage enforcement skipped: " "not a pull request event."
        ),
    )

    summary = generate_summary(
        result,
        changed_enforcement=changed_enforcement,
    )
    section = get_changed_enforcement_section(summary)

    assert "- **Status:** Skipped" in section
    assert "not a pull request event" in section
    assert "Skipped (changed-line coverage unavailable)" not in section


def test_summary_suppresses_unavailable_changed_coverage_for_non_pr_event():
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
        message="Changed-code coverage not available: pull request diff is unavailable.",
    )

    changed_enforcement = ChangedCoverageEnforcementResult(
        passed=True,
        coverage=None,
        threshold=80.0,
        available=False,
        message=(
            "Changed-line coverage enforcement skipped: " "not a pull request event."
        ),
    )

    summary = generate_summary(
        result,
        changed_coverage=changed_coverage,
        changed_enforcement=changed_enforcement,
    )

    assert "### Changed-Line Coverage Enforcement" in summary
    assert "- **Status:** Skipped" in summary
    assert "not a pull request event" in summary
    assert "### Changed-Code Coverage" not in summary
    assert "pull request diff is unavailable" not in summary


def test_summary_suppresses_duplicate_unavailable_coverage_on_pr_failure():
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
        message=(
            "Changed-code coverage not available: "
            "unable to read the pull request diff or line-level coverage data."
        ),
    )

    enforcement_message = (
        "Changed-line coverage enforcement failed: " "coverage data is unavailable."
    )

    changed_enforcement = ChangedCoverageEnforcementResult(
        passed=False,
        coverage=None,
        threshold=80.0,
        available=False,
        message=enforcement_message,
    )

    summary = generate_summary(
        result,
        changed_coverage=changed_coverage,
        changed_enforcement=changed_enforcement,
    )

    assert "### Changed-Line Coverage Enforcement" in summary
    assert "- **Status:** FAIL" in summary
    assert enforcement_message in summary
    assert summary.count(enforcement_message) == 1
    assert "### Changed-Code Coverage" not in summary
    assert "unable to read the pull request diff" not in summary


def test_summary_includes_branch_coverage():
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

    summary = generate_summary(
        result,
        covered_branches=8,
        valid_branches=10,
    )

    assert "### Branch Coverage" in summary
    assert "**Branch coverage:** 80.0%" in summary
    assert "**Covered branches:** 8/10" in summary


def test_branch_coverage_does_not_change_enforcement_status():
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

    summary = generate_summary(
        result,
        covered_branches=1,
        valid_branches=10,
    )

    assert "**Status:** PASS" in summary
    assert "**Branch coverage:** 10.0%" in summary
