import sys

import pytest

import src.main as main_module
from src.main import main


def test_action_merges_multiple_reports_and_writes_combined_coverage(
    monkeypatch, tmp_path
):
    workspace = tmp_path
    summary_path = workspace / "summary.md"
    output_path = workspace / "github-output.txt"

    first_report = workspace / "python.xml"
    second_report = workspace / "javascript.json"

    first_report.write_text("<coverage></coverage>", encoding="utf-8")
    second_report.write_text("{}", encoding="utf-8")

    monkeypatch.setenv("GITHUB_WORKSPACE", str(workspace))
    monkeypatch.setenv(
        "COVERAGE_FILE",
        "python.xml, javascript.json",
    )
    monkeypatch.setenv("COVERAGE_THRESHOLD", "60")
    monkeypatch.setenv("WARNING_MARGIN", "5")
    monkeypatch.setenv("BASELINE_COVERAGE", "")
    monkeypatch.setenv("MAX_REGRESSION", "5")
    monkeypatch.setenv("CHANGED_LINES_THRESHOLD", "0")
    monkeypatch.setenv("PR_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_path))
    monkeypatch.setenv("ENABLE_COVERAGE_TREND", "false")

    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "--github-action"],
    )

    merged_lines = {
        "src/example.py": {
            1: True,
            2: True,
            3: False,
        }
    }

    merge_calls = []

    def fake_merge_line_coverage(report_paths, root_dir):
        merge_calls.append((report_paths, root_dir))
        return merged_lines

    monkeypatch.setattr(
        main_module,
        "merge_line_coverage",
        fake_merge_line_coverage,
    )

    def fail_if_single_report_parser_is_used(_path):
        pytest.fail("The single-report parser should not be used.")

    monkeypatch.setattr(
        main_module,
        "_parse_coverage_report",
        fail_if_single_report_parser_is_used,
    )

    monkeypatch.setattr(
        main_module,
        "generate_summary",
        lambda *args, **kwargs: "Multiple-report integration summary",
    )

    result = main()

    assert result == 0

    assert merge_calls == [
        (
            [
                str(first_report),
                str(second_report),
            ],
            str(workspace),
        )
    ]

    output = output_path.read_text(encoding="utf-8")
    assert "coverage=66.66666666666666" in output

    summary = summary_path.read_text(encoding="utf-8")
    assert "Multiple-report integration summary" in summary
    assert "### Branch Coverage" in summary
    assert "Unavailable for merged reports" in summary
    assert "branch identities cannot be safely deduplicated" in summary
