import json

import pytest

from src.main import _parse_coverage_report
from src.parser import CoverageMetrics, parse_line_coverage


def test_main_detects_istanbul_json_report():
    result = _parse_coverage_report("tests/fixtures/sample_istanbul.json")

    assert isinstance(result, CoverageMetrics)
    assert result.total_coverage == pytest.approx(60.0)
    assert result.file_coverage == {
        "/project/src/app.js": pytest.approx(200 / 3),
        "/project/src/utils.js": pytest.approx(50.0),
    }


def test_parse_line_coverage_supports_istanbul_json(tmp_path):
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    source_file = source_dir / "app.js"
    source_file.write_text(
        "const first = 1;\nconst second = 2;\n",
        encoding="utf-8",
    )

    report = {
        str(source_file): {
            "statementMap": {
                "0": {"start": {"line": 1, "column": 0}},
                "1": {"start": {"line": 2, "column": 0}},
            },
            "s": {"0": 3, "1": 0},
        }
    }

    coverage_file = tmp_path / "coverage-final.json"
    coverage_file.write_text(json.dumps(report), encoding="utf-8")

    result = parse_line_coverage(
        str(coverage_file),
        root_dir=tmp_path,
    )

    assert result == {
        "src/app.js": {
            1: True,
            2: False,
        }
    }
