from pathlib import Path

import pytest

from src.report_merger import (
    calculate_coverage_metrics,
    merge_line_coverage,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_merge_line_coverage_combines_reports_and_counts_duplicate_lines_once(
    monkeypatch,
):
    reports = {
        "report-one.xml": {
            "src/app.py": {1: True, 2: False},
            "src/other.py": {1: False},
        },
        "report-two.xml": {
            "src/app.py": {2: True, 3: False},
            "src/other.py": {1: True},
        },
    }

    def mock_parse_line_coverage(report_path, root_dir):
        return reports[report_path]

    monkeypatch.setattr(
        "src.report_merger.parse_line_coverage",
        mock_parse_line_coverage,
    )

    result = merge_line_coverage(
        ["report-one.xml", "report-two.xml"],
        "/workspace",
    )

    assert result == {
        "src/app.py": {1: True, 2: True, 3: False},
        "src/other.py": {1: True},
    }


def test_merge_line_coverage_combines_real_go_and_jacoco_reports(tmp_path):
    workspace = tmp_path

    go_source = workspace / "example.com/project/src/example.go"
    go_source.parent.mkdir(parents=True)
    go_source.write_text(
        "package src\nfunc Example() {}\nfunc Other() {}\n",
        encoding="utf-8",
    )

    other_go_source = workspace / "example.com/project/src/other.go"
    other_go_source.write_text(
        "package src\nfunc Other() {}\n",
        encoding="utf-8",
    )

    jacoco_source = workspace / "src/example.py"
    jacoco_source.parent.mkdir(parents=True)
    jacoco_source.write_text(
        "first()\nsecond()\nthird()\n",
        encoding="utf-8",
    )

    go_report = FIXTURES_DIR / "sample_go.coverprofile"
    jacoco_report = FIXTURES_DIR / "sample_jacoco.xml"

    result = merge_line_coverage(
        [str(go_report), str(jacoco_report)],
        str(workspace),
    )

    assert result == {
        "example.com/project/src/example.go": {
            1: True,
            2: True,
            3: True,
            4: False,
            5: False,
        },
        "example.com/project/src/other.go": {
            1: True,
            2: True,
        },
        "src/example.py": {
            1: True,
            2: False,
            3: True,
        },
    }

    metrics = calculate_coverage_metrics(result)

    assert metrics.total_coverage == 70.0
    assert metrics.file_coverage["example.com/project/src/example.go"] == 60.0
    assert metrics.file_coverage["example.com/project/src/other.go"] == 100.0
    assert metrics.file_coverage["src/example.py"] == pytest.approx(66.6666667)


def test_calculate_coverage_metrics_uses_unique_lines():
    line_coverage = {
        "src/app.py": {1: True, 2: True, 3: False},
        "src/other.py": {1: True},
    }

    result = calculate_coverage_metrics(line_coverage)

    assert result.total_coverage == 75.0
    assert result.file_coverage["src/app.py"] == pytest.approx(66.6666667)
    assert result.file_coverage["src/other.py"] == 100.0


def test_calculate_coverage_metrics_rejects_empty_line_data():
    with pytest.raises(
        ValueError,
        match="Coverage reports contain no valid executable lines",
    ):
        calculate_coverage_metrics({})
