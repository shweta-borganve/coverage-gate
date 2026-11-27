import json

import pytest

from src.istanbul_parser import (
    parse_istanbul_branch_counts,
    parse_istanbul_json,
)

FIXTURE = "tests/fixtures/sample_istanbul.json"


def test_parse_istanbul_json_returns_expected_coverage():
    total, files = parse_istanbul_json(FIXTURE)

    assert total == pytest.approx(60.0)
    assert files == {
        "/project/src/app.js": {
            1: True,
            2: True,
            3: False,
        },
        "/project/src/utils.js": {
            1: True,
            2: False,
        },
    }


def test_parse_istanbul_json_handles_multiple_statements_on_one_line(tmp_path):
    report = {
        "/project/app.js": {
            "statementMap": {
                "0": {"start": {"line": 1, "column": 0}},
                "1": {"start": {"line": 1, "column": 10}},
            },
            "s": {"0": 0, "1": 1},
        }
    }
    path = tmp_path / "coverage.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    total, files = parse_istanbul_json(str(path))

    assert total == pytest.approx(100.0)
    assert files["/project/app.js"] == {1: True}


def test_parse_istanbul_json_rejects_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        parse_istanbul_json(str(tmp_path / "missing.json"))


def test_parse_istanbul_json_rejects_empty_file(tmp_path):
    path = tmp_path / "empty.json"
    path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="Empty"):
        parse_istanbul_json(str(path))


def test_parse_istanbul_json_rejects_invalid_json(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text("{invalid", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid Istanbul"):
        parse_istanbul_json(str(path))


def test_parse_istanbul_json_rejects_non_object_root(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="non-empty JSON object"):
        parse_istanbul_json(str(path))


def test_parse_istanbul_json_rejects_missing_statement_map(tmp_path):
    report = {"/project/app.js": {"s": {"0": 1}}}
    path = tmp_path / "coverage.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(TypeError, match="statementMap"):
        parse_istanbul_json(str(path))


def test_parse_istanbul_json_rejects_mismatched_statement_ids(tmp_path):
    report = {
        "/project/app.js": {
            "statementMap": {"0": {"start": {"line": 1, "column": 0}}},
            "s": {"1": 1},
        }
    }
    path = tmp_path / "coverage.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(ValueError, match="Inconsistent statement IDs"):
        parse_istanbul_json(str(path))


def test_parse_istanbul_json_rejects_invalid_line_number(tmp_path):
    report = {
        "/project/app.js": {
            "statementMap": {"0": {"start": {"line": 0, "column": 0}}},
            "s": {"0": 1},
        }
    }
    path = tmp_path / "coverage.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(ValueError, match="line number"):
        parse_istanbul_json(str(path))


def test_parse_istanbul_json_rejects_invalid_execution_count(tmp_path):
    report = {
        "/project/app.js": {
            "statementMap": {"0": {"start": {"line": 1, "column": 0}}},
            "s": {"0": -1},
        }
    }
    path = tmp_path / "coverage.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(ValueError, match="execution count"):
        parse_istanbul_json(str(path))


def test_parse_istanbul_branch_counts_returns_covered_and_valid_counts(
    tmp_path,
):
    report = {
        "/project/app.js": {
            "branchMap": {
                "0": {
                    "type": "if",
                    "locations": [{}, {}],
                },
                "1": {
                    "type": "switch",
                    "locations": [{}, {}, {}],
                },
            },
            "b": {
                "0": [3, 0],
                "1": [1, 0, 2],
            },
        }
    }
    path = tmp_path / "branches.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    assert parse_istanbul_branch_counts(str(path)) == (3, 5)


def test_parse_istanbul_branch_counts_returns_none_when_missing(tmp_path):
    report = {
        "/project/app.js": {
            "statementMap": {"0": {"start": {"line": 1}}},
            "s": {"0": 1},
        }
    }
    path = tmp_path / "no-branches.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    assert parse_istanbul_branch_counts(str(path)) is None


def test_parse_istanbul_branch_counts_rejects_mismatched_branch_ids(tmp_path):
    report = {
        "/project/app.js": {
            "branchMap": {"0": {"locations": [{}]}},
            "b": {"1": [1]},
        }
    }
    path = tmp_path / "mismatched-branches.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(ValueError, match="Inconsistent branch IDs"):
        parse_istanbul_branch_counts(str(path))


def test_parse_istanbul_branch_counts_rejects_missing_branch_data(tmp_path):
    report = {
        "/project/app.js": {
            "branchMap": {"0": {"locations": [{}]}},
        }
    }
    path = tmp_path / "missing-branches.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(TypeError, match="branch coverage data"):
        parse_istanbul_branch_counts(str(path))


def test_parse_istanbul_branch_counts_rejects_mismatched_path_counts(
    tmp_path,
):
    report = {
        "/project/app.js": {
            "branchMap": {"0": {"locations": [{}, {}]}},
            "b": {"0": [1]},
        }
    }
    path = tmp_path / "mismatched-paths.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(ValueError, match="Inconsistent branch path counts"):
        parse_istanbul_branch_counts(str(path))


@pytest.mark.parametrize("count", [-1, True, "1"])
def test_parse_istanbul_branch_counts_rejects_invalid_execution_counts(
    tmp_path,
    count,
):
    report = {
        "/project/app.js": {
            "branchMap": {"0": {"locations": [{}]}},
            "b": {"0": [count]},
        }
    }
    path = tmp_path / "invalid-counts.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid branch execution count"):
        parse_istanbul_branch_counts(str(path))


def test_parse_istanbul_branch_counts_returns_none_for_empty_branches(
    tmp_path,
):
    report = {
        "/project/app.js": {
            "branchMap": {},
            "b": {},
        }
    }
    path = tmp_path / "empty-branches.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    assert parse_istanbul_branch_counts(str(path)) is None
