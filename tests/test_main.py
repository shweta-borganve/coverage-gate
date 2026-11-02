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
    monkeypatch.setenv("PR_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_path))
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

    def fake_generate_summary(result, file_coverage, changed_coverage):
        return "Action summary\n" f"{changed_coverage.message}\n"

    monkeypatch.setattr(
        main_module,
        "generate_summary",
        fake_generate_summary,
    )

    return workspace, summary_path, output_path, metrics


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
    configure_action_environment(monkeypatch, tmp_path)

    result = main()

    captured = capsys.readouterr()

    assert result == 0
    assert "Not a pull request event" in captured.out


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
