from types import SimpleNamespace

import pytest

from docker import entrypoint


@pytest.mark.parametrize(
    ("threshold", "expected_result", "expected_output"),
    [
        ("80", 1, "passed=false"),
        ("50", 0, "passed=true"),
    ],
)
def test_docker_action_enforces_component_threshold(
    monkeypatch,
    tmp_path,
    threshold,
    expected_result,
    expected_output,
):
    workspace = tmp_path
    report = workspace / "coverage.xml"
    report.write_text("<coverage />", encoding="utf-8")

    source_file = workspace / "src" / "api" / "service.py"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("example source", encoding="utf-8")

    output_path = workspace / "github-output.txt"
    summary_path = workspace / "summary.md"

    monkeypatch.setenv("GITHUB_WORKSPACE", str(workspace))
    monkeypatch.setenv("INPUT_COVERAGE-FILE", "coverage.xml")
    monkeypatch.setenv("INPUT_THRESHOLD", "0")
    monkeypatch.setenv("INPUT_CHANGED-LINES-THRESHOLD", "0")
    monkeypatch.setenv("INPUT_COMPONENT-THRESHOLDS", f'{{"src/api/": {threshold}}}')
    monkeypatch.setenv("INPUT_WARNING-MARGIN", "5")
    monkeypatch.setenv("INPUT_BASELINE-COVERAGE", "")
    monkeypatch.setenv("INPUT_MAX-REGRESSION", "5")
    monkeypatch.setenv("INPUT_ENABLE-COVERAGE-BADGE", "false")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_path))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))

    metrics = SimpleNamespace(
        total_coverage=90.0,
        file_coverage={},
    )

    line_coverage = {
        "src/api/service.py": {
            1: True,
            2: False,
        }
    }

    monkeypatch.setattr(
        entrypoint,
        "parse_coverage_report",
        lambda file_path: metrics,
    )
    monkeypatch.setattr(
        entrypoint,
        "parse_line_coverage",
        lambda file_path, root_dir: line_coverage,
    )
    monkeypatch.setattr(
        entrypoint,
        "enforce",
        lambda *args: SimpleNamespace(
            passed=True,
            message="Overall coverage passed.",
            coverage=90.0,
        ),
    )
    monkeypatch.setattr(
        entrypoint,
        "enforce_changed_coverage",
        lambda *args: SimpleNamespace(
            passed=True,
            message="Changed-line coverage passed.",
            coverage=None,
        ),
    )

    summary_calls = []

    def fake_generate_summary(*args, **kwargs):
        summary_calls.append((args, kwargs))
        return "Docker component coverage summary"

    monkeypatch.setattr(
        entrypoint,
        "generate_summary",
        fake_generate_summary,
    )

    result = entrypoint.main()

    assert result == expected_result

    output = output_path.read_text(encoding="utf-8")
    assert expected_output in output

    assert len(summary_calls) == 1
    component_results = summary_calls[0][1]["component_results"]

    assert len(component_results) == 1
    assert component_results[0].component == "src/api"
    assert component_results[0].coverage == 50.0
    assert component_results[0].threshold == float(threshold)
    assert component_results[0].passed is (expected_result == 0)

    summary = summary_path.read_text(encoding="utf-8")
    assert "Docker component coverage summary" in summary
