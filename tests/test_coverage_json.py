import json
from pathlib import Path

import pytest

from src.parser import parse_coverage_json, parse_line_coverage

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_parse_coverage_json():
    metrics = parse_coverage_json(FIXTURES_DIR / "sample.json")

    assert metrics.total_coverage == 70.0
    assert metrics.file_coverage == {
        "src/example.py": 80.0,
        "src/utils.py": 60.0,
    }


def test_parse_coverage_json_accepts_string_path():
    metrics = parse_coverage_json(str(FIXTURES_DIR / "sample.json"))

    assert metrics.total_coverage == 70.0


def test_parse_json_line_coverage():
    coverage_file = FIXTURES_DIR / "sample.json"

    result = parse_line_coverage(str(coverage_file))

    assert result == {
        "src/example.py": {
            1: True,
            2: True,
            3: True,
            4: False,
            5: True,
        },
        "src/utils.py": {
            1: True,
            2: True,
            3: True,
            4: False,
            5: False,
        },
    }


def test_json_file_not_found():
    with pytest.raises(FileNotFoundError, match="Coverage file not found"):
        parse_coverage_json(FIXTURES_DIR / "missing.json")


def test_empty_json_report(tmp_path):
    coverage_file = tmp_path / "empty.json"
    coverage_file.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="Empty coverage JSON report"):
        parse_coverage_json(coverage_file)


def test_invalid_json_report(tmp_path):
    coverage_file = tmp_path / "invalid.json"
    coverage_file.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid coverage JSON report"):
        parse_coverage_json(coverage_file)


@pytest.mark.parametrize(
    "content",
    [
        "[]",
        '"coverage"',
        "null",
        "123",
    ],
)
def test_json_report_requires_object_root(tmp_path, content):
    coverage_file = tmp_path / "invalid-root.json"
    coverage_file.write_text(content, encoding="utf-8")

    with pytest.raises(TypeError, match="expected a JSON object"):
        parse_coverage_json(coverage_file)


def test_json_report_requires_totals_object(tmp_path):
    coverage_file = tmp_path / "missing-totals.json"
    coverage_file.write_text(
        json.dumps({"files": {"src/example.py": {}}}),
        encoding="utf-8",
    )

    with pytest.raises(TypeError, match="missing totals object"):
        parse_coverage_json(coverage_file)


@pytest.mark.parametrize("files", [None, [], {}, "invalid"])
def test_json_report_requires_nonempty_files_object(tmp_path, files):
    coverage_file = tmp_path / "missing-files.json"
    coverage_file.write_text(
        json.dumps({"totals": {}, "files": files}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing files object"):
        parse_coverage_json(coverage_file)


@pytest.mark.parametrize(
    ("covered", "statements"),
    [
        (-1, 10),
        (True, 10),
        (1.5, 10),
        ("7", 10),
        (11, 10),
        (0, 0),
    ],
)
def test_json_report_rejects_invalid_total_counts(
    tmp_path,
    covered,
    statements,
):
    report = {
        "files": {
            "src/example.py": {
                "executed_lines": [1],
                "missing_lines": [2],
                "summary": {
                    "covered_lines": 1,
                    "num_statements": 2,
                },
            }
        },
        "totals": {
            "covered_lines": covered,
            "num_statements": statements,
        },
    }

    coverage_file = tmp_path / "invalid-totals.json"
    coverage_file.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(ValueError):
        parse_coverage_json(coverage_file)


@pytest.mark.parametrize(
    ("executed", "missing"),
    [
        ([1, 1], [2]),
        ([1], [1]),
        ([0], [2]),
        ([-1], [2]),
        ([True], [2]),
        (["1"], [2]),
    ],
)
def test_json_report_rejects_invalid_line_data(
    tmp_path,
    executed,
    missing,
):
    report = {
        "files": {
            "src/example.py": {
                "executed_lines": executed,
                "missing_lines": missing,
                "summary": {
                    "covered_lines": 1,
                    "num_statements": 2,
                },
            }
        },
        "totals": {
            "covered_lines": 1,
            "num_statements": 2,
        },
    }

    coverage_file = tmp_path / "invalid-lines.json"
    coverage_file.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(ValueError):
        parse_coverage_json(coverage_file)


def test_json_report_rejects_missing_file_summary(tmp_path):
    report = {
        "files": {
            "src/example.py": {
                "executed_lines": [1],
                "missing_lines": [2],
            }
        },
        "totals": {
            "covered_lines": 1,
            "num_statements": 2,
        },
    }

    coverage_file = tmp_path / "missing-summary.json"
    coverage_file.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(TypeError, match="missing summary"):
        parse_coverage_json(coverage_file)


def test_json_report_rejects_inconsistent_file_summary(tmp_path):
    report = {
        "files": {
            "src/example.py": {
                "executed_lines": [1],
                "missing_lines": [2],
                "summary": {
                    "covered_lines": 2,
                    "num_statements": 2,
                },
            }
        },
        "totals": {
            "covered_lines": 1,
            "num_statements": 2,
        },
    }

    coverage_file = tmp_path / "inconsistent-summary.json"
    coverage_file.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(ValueError, match="Inconsistent line coverage data"):
        parse_coverage_json(coverage_file)


def test_json_report_rejects_invalid_filename(tmp_path):
    report = {
        "files": {
            " ": {
                "executed_lines": [1],
                "missing_lines": [2],
                "summary": {
                    "covered_lines": 1,
                    "num_statements": 2,
                },
            }
        },
        "totals": {
            "covered_lines": 1,
            "num_statements": 2,
        },
    }

    coverage_file = tmp_path / "invalid-filename.json"
    coverage_file.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(ValueError, match="invalid filename"):
        parse_coverage_json(coverage_file)


def test_json_report_rejects_missing_line_data(tmp_path):
    report = {
        "files": {
            "src/example.py": {
                "executed_lines": [],
                "missing_lines": [],
                "summary": {
                    "covered_lines": 0,
                    "num_statements": 0,
                },
            }
        },
        "totals": {
            "covered_lines": 0,
            "num_statements": 0,
        },
    }

    coverage_file = tmp_path / "no-line-data.json"
    coverage_file.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(ValueError):
        parse_coverage_json(coverage_file)


@pytest.mark.parametrize(
    ("total_covered", "total_statements"),
    [
        (0, 2),
        (1, 3),
        (2, 2),
    ],
)
def test_json_report_rejects_inconsistent_aggregate_totals(
    tmp_path,
    total_covered,
    total_statements,
):
    report = {
        "files": {
            "src/example.py": {
                "executed_lines": [1],
                "missing_lines": [2],
                "summary": {
                    "covered_lines": 1,
                    "num_statements": 2,
                },
            }
        },
        "totals": {
            "covered_lines": total_covered,
            "num_statements": total_statements,
        },
    }

    coverage_file = tmp_path / "inconsistent-totals.json"
    coverage_file.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="Inconsistent total coverage counts",
    ):
        parse_coverage_json(coverage_file)


def test_json_line_coverage_rejects_duplicate_normalized_filenames(tmp_path):
    source_file = tmp_path / "src" / "example.py"
    source_file.parent.mkdir()
    source_file.write_text("print('hello')\n", encoding="utf-8")

    report = {
        "files": {
            "src/example.py": {
                "executed_lines": [1],
                "missing_lines": [],
                "summary": {
                    "covered_lines": 1,
                    "num_statements": 1,
                },
            },
            str(source_file): {
                "executed_lines": [1],
                "missing_lines": [],
                "summary": {
                    "covered_lines": 1,
                    "num_statements": 1,
                },
            },
        },
        "totals": {
            "covered_lines": 2,
            "num_statements": 2,
        },
    }

    coverage_file = tmp_path / "duplicate-paths.json"
    coverage_file.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="Duplicate normalized filename",
    ):
        parse_line_coverage(coverage_file, root_dir=tmp_path)
