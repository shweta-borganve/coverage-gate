import json
import subprocess
import sys
from types import SimpleNamespace

import src.main as main_module
from src.changed_coverage import ChangedCoverageReport
from src.main import main


def configure_action_environment(monkeypatch, tmp_path, threshold="80"):
    workspace = tmp_path
    summary_path = workspace / "summary.md"
    output_path = workspace / "github-output.txt"

    monkeypatch.setenv("GITHUB_WORKSPACE", str(workspace))
    monkeypatch.setenv("COVERAGE_FILE", "coverage.xml")
    monkeypatch.setenv("COVERAGE_THRESHOLD", threshold)
    monkeypatch.setenv("WARNING_MARGIN", "5")
    monkeypatch.setenv("BASELINE_COVERAGE", "")
    monkeypatch.setenv("MAX_REGRESSION", "5")
    monkeypatch.setenv("CHANGED_LINES_THRESHOLD", "0")
    monkeypatch.setenv("PR_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_path))
    monkeypatch.setenv("ENABLE_COVERAGE_TREND", "false")
    monkeypatch.setattr(sys, "argv", ["main.py", "--github-action"])

    metrics = SimpleNamespace(
        total_coverage=85.0,
        file_coverage={"src/example.py": 85.0},
    )

    monkeypatch.setattr(
        main_module,
        "parse_cobertura",
        lambda _path: metrics,
    )

    def fake_generate_summary(
        result,
        file_coverage,
        changed_coverage,
        changed_enforcement,
    ):
        return (
            "Action summary\n"
            f"{changed_coverage.message}\n"
            f"{changed_enforcement.message}\n"
        )

    monkeypatch.setattr(
        main_module,
        "generate_summary",
        fake_generate_summary,
    )

    return workspace, summary_path, output_path, metrics


def configure_trend_environment(monkeypatch, tmp_path):
    """Configure the GitHub metadata required by coverage trend tracking."""
    history_path = tmp_path / "coverage-gate-history.json"

    monkeypatch.setenv("ENABLE_COVERAGE_TREND", "true")
    monkeypatch.setenv("HISTORY_TOKEN", "test-history-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("COVERAGE_HISTORY_BRANCH", "feature/test-branch")
    monkeypatch.setenv("COVERAGE_HISTORY_COMMIT_SHA", "current-commit-sha")
    monkeypatch.setenv("GITHUB_RUN_ID", "12345")
    monkeypatch.setenv("GITHUB_RUN_NUMBER", "42")
    monkeypatch.setenv(
        "GITHUB_WORKFLOW_REF",
        "owner/repo/.github/workflows/ci.yml@refs/heads/feature/test-branch",
    )
    monkeypatch.setenv("GITHUB_API_URL", "https://api.github.com")
    monkeypatch.setenv("HISTORY_OUTPUT_PATH", str(history_path))

    return history_path


def install_trend_summary_mock(monkeypatch):
    """Install a summary mock that accepts optional trend data."""
    summaries = []

    def fake_generate_summary(
        result,
        file_coverage,
        changed_coverage,
        changed_enforcement,
        trend_data=None,
    ):
        summaries.append(trend_data)
        return (
            "Action summary\n"
            f"Trend data: {trend_data}\n"
            f"{changed_coverage.message}\n"
            f"{changed_enforcement.message}\n"
        )

    monkeypatch.setattr(
        main_module,
        "generate_summary",
        fake_generate_summary,
    )

    return summaries


def test_main_uses_default_warning_margin(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "tests/fixtures/sample.xml", "80"],
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 0
    assert "WARNING: Coverage is within 5.0% of the threshold." in captured.out


def test_main_uses_custom_warning_margin(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "tests/fixtures/sample.xml", "80", "10"],
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 0
    assert "WARNING: Coverage is within 10.0% of the threshold." in captured.out


def test_main_invalid_threshold(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "tests/fixtures/sample.xml", "invalid"],
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "Invalid threshold: invalid" in captured.out


def test_main_invalid_warning_margin(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "tests/fixtures/sample.xml", "80", "invalid"],
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "Invalid warning margin: invalid" in captured.out


def test_main_missing_arguments(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["main.py"])

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "Usage:" in captured.out


def test_main_fails_when_coverage_is_below_threshold(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "tests/fixtures/sample.xml", "90"],
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "FAIL" in captured.out


def test_main_uses_baseline_and_max_regression(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "tests/fixtures/sample.xml", "80", "5", "90", "5"],
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 0
    assert "Coverage 85.0% vs threshold 80.0% — PASS" in captured.out


def test_main_fails_when_regression_exceeds_limit(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "tests/fixtures/sample.xml", "80", "5", "95", "5"],
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "REGRESSION" in captured.out
    assert "Coverage 85.0% vs threshold 80.0% — FAIL" in captured.out


def test_main_invalid_baseline_coverage(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "tests/fixtures/sample.xml", "80", "5", "invalid", "5"],
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "Invalid baseline coverage: invalid" in captured.out


def test_main_invalid_max_regression(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "tests/fixtures/sample.xml", "80", "5", "90", "invalid"],
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "Invalid max regression: invalid" in captured.out


def test_action_success_writes_summary_and_coverage_output(
    monkeypatch, tmp_path, capsys
):
    _, summary_path, output_path, _ = configure_action_environment(
        monkeypatch, tmp_path
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 0
    assert "[Coverage Gate] RESULT: PASSED" in captured.out
    summary = summary_path.read_text(encoding="utf-8")
    assert "Action summary" in summary
    assert "Changed-code coverage not available" in summary
    assert "coverage=85.0" in output_path.read_text(encoding="utf-8")


def test_action_failure_writes_summary_before_returning_failure(
    monkeypatch, tmp_path, capsys
):
    _, summary_path, output_path, _ = configure_action_environment(
        monkeypatch, tmp_path, threshold="90"
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "[Coverage Gate] RESULT: FAILED" in captured.out
    assert "Action summary" in summary_path.read_text(encoding="utf-8")
    assert "coverage=85.0" in output_path.read_text(encoding="utf-8")


def test_action_with_baseline_regression_failure(monkeypatch, tmp_path, capsys):
    configure_action_environment(monkeypatch, tmp_path)
    monkeypatch.setenv("BASELINE_COVERAGE", "95")
    monkeypatch.setenv("MAX_REGRESSION", "5")

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "Baseline coverage: 95.00%" in captured.out
    assert "REGRESSION" in captured.out
    assert "[Coverage Gate] RESULT: FAILED" in captured.out


def test_action_skips_changed_coverage_for_non_pr_event(monkeypatch, tmp_path, capsys):
    _, _, output_path, _ = configure_action_environment(monkeypatch, tmp_path)

    result = main()

    captured = capsys.readouterr()
    output = output_path.read_text(encoding="utf-8")

    assert result == 0
    assert "Not a pull request event" in captured.out
    assert "changed-lines-passed=skipped" in output
    assert "changed-lines-coverage=" in output


def test_push_event_skips_changed_coverage_with_positive_threshold(
    monkeypatch, tmp_path, capsys
):
    _, _, output_path, _ = configure_action_environment(monkeypatch, tmp_path)
    monkeypatch.setenv("PR_EVENT_NAME", "push")
    monkeypatch.setenv("CHANGED_LINES_THRESHOLD", "80")

    result = main()

    captured = capsys.readouterr()
    output = output_path.read_text(encoding="utf-8")

    assert result == 0
    assert "not a pull request event" in captured.out
    assert "changed-lines-passed=skipped" in output
    assert "RESULT: PASSED" in captured.out


def test_action_skips_changed_coverage_when_pr_shas_are_missing(
    monkeypatch, tmp_path, capsys
):
    configure_action_environment(monkeypatch, tmp_path)
    monkeypatch.setenv("PR_EVENT_NAME", "pull_request")
    monkeypatch.delenv("PR_BASE_SHA", raising=False)
    monkeypatch.delenv("PR_HEAD_SHA", raising=False)

    result = main()

    captured = capsys.readouterr()

    assert result == 0
    assert "Base or head commit SHA is unavailable" in captured.out


def test_action_calculates_changed_coverage_for_pull_request(
    monkeypatch, tmp_path, capsys
):
    workspace, summary_path, _, _ = configure_action_environment(monkeypatch, tmp_path)
    monkeypatch.setenv("PR_EVENT_NAME", "pull_request")
    monkeypatch.setenv("PR_BASE_SHA", "base-sha")
    monkeypatch.setenv("PR_HEAD_SHA", "head-sha")

    monkeypatch.setattr(
        main_module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(stdout="diff output"),
    )
    monkeypatch.setattr(
        main_module,
        "parse_changed_lines",
        lambda _diff: {"src/example.py": {1}},
    )

    line_coverage_calls = []

    def fake_parse_line_coverage(path, root_dir):
        line_coverage_calls.append((path, root_dir))
        return {"src/example.py": {1: True}}

    monkeypatch.setattr(
        main_module,
        "parse_line_coverage",
        fake_parse_line_coverage,
    )

    report = ChangedCoverageReport(
        available=True,
        files=[],
        message="Changed-code coverage calculated.",
    )
    monkeypatch.setattr(
        main_module,
        "generate_changed_coverage_report",
        lambda _changed_lines, _line_coverage: report,
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 0
    assert "Changed-code coverage calculated." in captured.out
    assert line_coverage_calls == [(str(workspace / "coverage.xml"), str(workspace))]

    summary = summary_path.read_text(encoding="utf-8")
    assert "Changed-code coverage calculated." in summary


def test_action_warns_when_changed_coverage_calculation_fails(
    monkeypatch, tmp_path, capsys
):
    _, summary_path, _, _ = configure_action_environment(monkeypatch, tmp_path)
    monkeypatch.setenv("PR_EVENT_NAME", "pull_request")
    monkeypatch.setenv("PR_BASE_SHA", "base-sha")
    monkeypatch.setenv("PR_HEAD_SHA", "head-sha")

    def fail_diff(*_args, **_kwargs):
        raise subprocess.CalledProcessError(1, ["git", "diff"])

    monkeypatch.setattr(main_module.subprocess, "run", fail_diff)

    result = main()

    captured = capsys.readouterr()
    summary = summary_path.read_text(encoding="utf-8")

    assert result == 0
    assert "WARNING: Changed-code coverage could not be calculated" in captured.out
    assert "Changed-code coverage not available" in summary
    assert "unable to read the pull request diff" in summary


def test_action_without_summary_or_output_paths(monkeypatch, tmp_path, capsys):
    configure_action_environment(monkeypatch, tmp_path)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY")
    monkeypatch.delenv("GITHUB_OUTPUT")

    result = main()

    captured = capsys.readouterr()

    assert result == 0
    assert "summary path is unavailable" in captured.out
    assert "output path is unavailable" in captured.out


def test_action_missing_required_environment_variable_returns_failure(
    monkeypatch, tmp_path, capsys
):
    configure_action_environment(monkeypatch, tmp_path)
    monkeypatch.delenv("GITHUB_WORKSPACE")

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "[Coverage Gate] ERROR:" in captured.out


def test_action_invalid_threshold_returns_failure(monkeypatch, tmp_path, capsys):
    configure_action_environment(monkeypatch, tmp_path, threshold="invalid")

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "[Coverage Gate] ERROR:" in captured.out


def test_action_rejects_coverage_file_outside_workspace(monkeypatch, tmp_path, capsys):
    configure_action_environment(monkeypatch, tmp_path)
    monkeypatch.setenv("COVERAGE_FILE", "../outside.xml")

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "must be located inside GITHUB_WORKSPACE" in captured.out


def test_action_rejects_absolute_coverage_path_outside_workspace(
    monkeypatch, tmp_path, capsys
):
    configure_action_environment(monkeypatch, tmp_path)
    monkeypatch.setenv("COVERAGE_FILE", str(tmp_path.parent / "outside.xml"))

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "must be located inside GITHUB_WORKSPACE" in captured.out


def test_action_accepts_nested_coverage_file_path(monkeypatch, tmp_path):
    _, _, _, _ = configure_action_environment(monkeypatch, tmp_path)
    monkeypatch.setenv("COVERAGE_FILE", "reports/coverage.xml")

    parsed_paths = []

    monkeypatch.setattr(
        main_module,
        "parse_cobertura",
        lambda path: (
            parsed_paths.append(path)
            or SimpleNamespace(
                total_coverage=85.0,
                file_coverage={"src/example.py": 85.0},
            )
        ),
    )

    result = main()

    assert result == 0
    assert parsed_paths == [str(tmp_path / "reports" / "coverage.xml")]


def test_action_rejects_coverage_symlink_outside_workspace(
    monkeypatch, tmp_path, capsys
):
    configure_action_environment(monkeypatch, tmp_path)

    outside_file = tmp_path.parent / "outside.xml"
    outside_file.write_text("<coverage line-rate='1.0'></coverage>")

    symlink = tmp_path / "coverage-link.xml"
    symlink.symlink_to(outside_file)

    monkeypatch.setenv("COVERAGE_FILE", "coverage-link.xml")

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "must be located inside GITHUB_WORKSPACE" in captured.out


def test_action_publishes_pr_comment(monkeypatch, tmp_path):
    configure_action_environment(monkeypatch, tmp_path)

    monkeypatch.setenv("PR_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("PR_NUMBER", "42")
    monkeypatch.setenv("GITHUB_API_URL", "https://api.github.com")
    monkeypatch.setenv("ENABLE_PR_COMMENT", "true")

    published_comments = []

    def fake_publish_pr_comment(**kwargs):
        published_comments.append(kwargs)
        return "created"

    monkeypatch.setattr(
        main_module,
        "publish_pr_comment",
        fake_publish_pr_comment,
    )

    result = main()

    assert result == 0
    assert len(published_comments) == 1

    comment = published_comments[0]

    assert comment["token"] == "test-token"
    assert comment["repository"] == "owner/repo"
    assert comment["pull_number"] == "42"
    assert comment["api_url"] == "https://api.github.com"
    assert "Action summary" in comment["summary"]


def test_action_skips_pr_comment_when_disabled(monkeypatch, tmp_path):
    configure_action_environment(monkeypatch, tmp_path)

    monkeypatch.setenv("PR_EVENT_NAME", "pull_request")
    monkeypatch.setenv("ENABLE_PR_COMMENT", "false")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("PR_NUMBER", "42")

    def fail_if_called(**_kwargs):
        raise AssertionError("PR comment should not be published.")

    monkeypatch.setattr(
        main_module,
        "publish_pr_comment",
        fail_if_called,
    )

    result = main()

    assert result == 0


def test_action_continues_when_pr_comment_api_fails(monkeypatch, tmp_path, capsys):
    configure_action_environment(monkeypatch, tmp_path)

    monkeypatch.setenv("PR_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("PR_NUMBER", "42")

    def fail_to_publish(**_kwargs):
        raise OSError("GitHub API unavailable")

    monkeypatch.setattr(
        main_module,
        "publish_pr_comment",
        fail_to_publish,
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 0
    assert "Could not publish PR comment" in captured.out
    assert "GitHub API unavailable" in captured.out
    assert "[Coverage Gate] RESULT: PASSED" in captured.out


def test_action_disables_coverage_trend_by_default(monkeypatch, tmp_path):
    configure_action_environment(monkeypatch, tmp_path)

    def fail_if_called(**_kwargs):
        raise AssertionError("Coverage trend should be disabled.")

    monkeypatch.setattr(
        main_module,
        "get_coverage_trend",
        fail_if_called,
    )

    result = main()

    assert result == 0


def test_action_retrieves_trend_and_writes_history_record(monkeypatch, tmp_path):
    configure_action_environment(monkeypatch, tmp_path)
    history_path = configure_trend_environment(monkeypatch, tmp_path)
    summaries = install_trend_summary_mock(monkeypatch)

    expected_trend = {
        "available": True,
        "direction": "improved",
        "previous_coverage": 80.0,
        "change": 5.0,
        "history": [80.0, 85.0],
        "records_count": 1,
        "message": "Coverage improved by 5.00 percentage points.",
    }

    trend_calls = []

    def fake_get_coverage_trend(**kwargs):
        trend_calls.append(kwargs)
        return expected_trend

    monkeypatch.setattr(
        main_module,
        "get_coverage_trend",
        fake_get_coverage_trend,
    )

    result = main()

    assert result == 0
    assert len(trend_calls) == 1
    assert trend_calls[0]["token"] == "test-history-token"
    assert trend_calls[0]["repository"] == "owner/repo"
    assert trend_calls[0]["branch"] == "feature/test-branch"
    assert trend_calls[0]["current_coverage"] == 85.0
    assert summaries == [expected_trend]

    record = json.loads(history_path.read_text(encoding="utf-8"))

    assert record["coverage"] == 85.0
    assert record["branch"] == "feature/test-branch"
    assert record["commit_sha"] == "current-commit-sha"
    assert record["run_id"] == "12345"
    assert record["run_number"] == 42
    assert record["workflow_path"] == "owner/repo/.github/workflows/ci.yml"


def test_action_writes_history_when_no_previous_trend_exists(monkeypatch, tmp_path):
    configure_action_environment(monkeypatch, tmp_path)
    history_path = configure_trend_environment(monkeypatch, tmp_path)
    summaries = install_trend_summary_mock(monkeypatch)

    no_history = {
        "available": False,
        "direction": "no-history",
        "previous_coverage": None,
        "change": None,
        "history": [85.0],
        "records_count": 0,
        "message": "No previous coverage history is available.",
    }

    monkeypatch.setattr(
        main_module,
        "get_coverage_trend",
        lambda **_kwargs: no_history,
    )

    result = main()

    assert result == 0
    assert summaries == [no_history]
    assert history_path.exists()

    record = json.loads(history_path.read_text(encoding="utf-8"))
    assert record["coverage"] == 85.0
    assert record["run_id"] == "12345"


def test_action_writes_history_even_when_coverage_fails(monkeypatch, tmp_path, capsys):
    configure_action_environment(monkeypatch, tmp_path, threshold="90")
    history_path = configure_trend_environment(monkeypatch, tmp_path)
    install_trend_summary_mock(monkeypatch)

    unavailable_trend = {
        "available": False,
        "direction": "unavailable",
        "previous_coverage": None,
        "change": None,
        "history": [85.0],
        "records_count": 0,
        "message": "Coverage history is currently unavailable.",
    }

    monkeypatch.setattr(
        main_module,
        "get_coverage_trend",
        lambda **_kwargs: unavailable_trend,
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "[Coverage Gate] RESULT: FAILED" in captured.out
    assert history_path.exists()

    record = json.loads(history_path.read_text(encoding="utf-8"))
    assert record["coverage"] == 85.0
    assert record["run_id"] == "12345"


def test_action_skips_history_record_when_run_metadata_is_missing(
    monkeypatch, tmp_path, capsys
):
    configure_action_environment(monkeypatch, tmp_path)
    history_path = configure_trend_environment(monkeypatch, tmp_path)
    install_trend_summary_mock(monkeypatch)
    monkeypatch.delenv("GITHUB_RUN_NUMBER")

    monkeypatch.setattr(
        main_module,
        "get_coverage_trend",
        lambda **_kwargs: {
            "available": False,
            "direction": "unavailable",
            "previous_coverage": None,
            "change": None,
            "history": [85.0],
            "records_count": 0,
            "message": "Coverage history is currently unavailable.",
        },
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 0
    assert "required GitHub run metadata is unavailable" in captured.out
    assert not history_path.exists()


def test_action_fails_when_pr_shas_are_missing_and_threshold_is_positive(
    monkeypatch, tmp_path, capsys
):
    configure_action_environment(monkeypatch, tmp_path)
    monkeypatch.setenv("PR_EVENT_NAME", "pull_request")
    monkeypatch.setenv("CHANGED_LINES_THRESHOLD", "80")
    monkeypatch.delenv("PR_BASE_SHA", raising=False)
    monkeypatch.delenv("PR_HEAD_SHA", raising=False)

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "Base or head commit SHA is unavailable" in captured.out
    assert "Changed-line coverage enforcement failed" in captured.out
    assert "[Coverage Gate] RESULT: FAILED" in captured.out


def test_action_fails_when_git_diff_fails_and_threshold_is_positive(
    monkeypatch, tmp_path, capsys
):
    _, summary_path, output_path, _ = configure_action_environment(
        monkeypatch, tmp_path
    )
    monkeypatch.setenv("PR_EVENT_NAME", "pull_request")
    monkeypatch.setenv("PR_BASE_SHA", "base-sha")
    monkeypatch.setenv("PR_HEAD_SHA", "head-sha")
    monkeypatch.setenv("CHANGED_LINES_THRESHOLD", "80")

    def fail_diff(*_args, **_kwargs):
        raise subprocess.CalledProcessError(1, ["git", "diff"])

    monkeypatch.setattr(main_module.subprocess, "run", fail_diff)

    result = main()

    captured = capsys.readouterr()
    summary = summary_path.read_text(encoding="utf-8")
    output = output_path.read_text(encoding="utf-8")

    assert result == 1
    assert "could not be calculated" in captured.out
    assert "Changed-line coverage enforcement failed" in captured.out
    assert "changed-lines-passed=false" in output
    assert "RESULT: FAILED" in captured.out
    assert "Changed-code coverage not available" in summary


def test_action_skips_enforcement_for_valid_empty_pr_diff(
    monkeypatch, tmp_path, capsys
):
    _, summary_path, output_path, _ = configure_action_environment(
        monkeypatch, tmp_path
    )
    monkeypatch.setenv("PR_EVENT_NAME", "pull_request")
    monkeypatch.setenv("PR_BASE_SHA", "base-sha")
    monkeypatch.setenv("PR_HEAD_SHA", "head-sha")
    monkeypatch.setenv("CHANGED_LINES_THRESHOLD", "80")

    monkeypatch.setattr(
        main_module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(stdout=""),
    )
    monkeypatch.setattr(
        main_module,
        "parse_line_coverage",
        lambda *_args, **_kwargs: {},
    )

    result = main()

    captured = capsys.readouterr()
    summary = summary_path.read_text(encoding="utf-8")
    output = output_path.read_text(encoding="utf-8")

    assert result == 0
    assert "no changed executable lines" in captured.out
    assert "RESULT: PASSED" in captured.out
    assert "no changed executable lines" in summary
    assert "changed-lines-passed=skipped" in output
