import pytest

from docker import entrypoint
from src import report_merger


def test_docker_action_merges_multiple_reports(monkeypatch, tmp_path):
    workspace = tmp_path
    first_report = workspace / "python.xml"
    second_report = workspace / "javascript.json"

    first_report.write_text("<coverage></coverage>", encoding="utf-8")
    second_report.write_text("{}", encoding="utf-8")

    output_path = workspace / "github-output.txt"
    summary_path = workspace / "summary.md"

    monkeypatch.setenv("GITHUB_WORKSPACE", str(workspace))
    monkeypatch.setenv(
        "INPUT_COVERAGE-FILE",
        "python.xml, javascript.json",
    )
    monkeypatch.setenv("INPUT_THRESHOLD", "60")
    monkeypatch.setenv("INPUT_CHANGED-LINES-THRESHOLD", "0")
    monkeypatch.setenv("INPUT_WARNING-MARGIN", "5")
    monkeypatch.setenv("INPUT_BASELINE-COVERAGE", "")
    monkeypatch.setenv("INPUT_MAX-REGRESSION", "5")
    monkeypatch.setenv("INPUT_ENABLE-COVERAGE-BADGE", "false")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_path))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))

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
        report_merger,
        "merge_line_coverage",
        fake_merge_line_coverage,
    )

    monkeypatch.setattr(
        entrypoint,
        "generate_summary",
        lambda *args, **kwargs: "Multiple-report Docker summary",
    )

    result = entrypoint.main()

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
    assert "passed=true" in output

    summary = summary_path.read_text(encoding="utf-8")
    assert "Multiple-report Docker summary" in summary


def test_resolve_coverage_paths_accepts_multiple_reports(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    first_report = workspace / "python.xml"
    second_report = workspace / "javascript.json"

    first_report.touch()
    second_report.touch()

    result = entrypoint.resolve_coverage_paths(
        workspace,
        "python.xml, javascript.json",
    )

    assert result == [first_report, second_report]


def test_resolve_coverage_paths_accepts_single_report(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    report = workspace / "coverage.xml"
    report.touch()

    result = entrypoint.resolve_coverage_paths(
        workspace,
        "coverage.xml",
    )

    assert result == [report]


@pytest.mark.parametrize(
    "configured_paths",
    [
        "",
        ",",
        "coverage.xml,",
        ",coverage.xml",
        "coverage.xml,,other.xml",
        "coverage.xml,   ,other.xml",
    ],
)
def test_resolve_coverage_paths_rejects_empty_entries(
    tmp_path,
    configured_paths,
):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(
        ValueError,
        match="one or more non-empty report paths",
    ):
        entrypoint.resolve_coverage_paths(
            workspace,
            configured_paths,
        )


def test_resolve_coverage_paths_rejects_parent_directory(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(
        ValueError,
        match="inside GITHUB_WORKSPACE",
    ):
        entrypoint.resolve_coverage_paths(
            workspace,
            "coverage.xml, ../outside.xml",
        )


def test_resolve_coverage_paths_rejects_external_absolute_path(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    outside_report = tmp_path / "outside.xml"

    with pytest.raises(
        ValueError,
        match="inside GITHUB_WORKSPACE",
    ):
        entrypoint.resolve_coverage_paths(
            workspace,
            f"coverage.xml, {outside_report}",
        )


def test_resolve_coverage_paths_rejects_symlink_outside_workspace(
    tmp_path,
):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    outside_report = tmp_path / "outside.xml"
    outside_report.write_text("<coverage />", encoding="utf-8")

    symlink = workspace / "coverage-link.xml"
    symlink.symlink_to(outside_report)

    with pytest.raises(
        ValueError,
        match="inside GITHUB_WORKSPACE",
    ):
        entrypoint.resolve_coverage_paths(
            workspace,
            "coverage.xml, coverage-link.xml",
        )
