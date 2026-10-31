from pathlib import Path

import pytest

from src.parser import parse_lcov

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_parse_lcov():
    metrics = parse_lcov(str(FIXTURES_DIR / "sample.info"))

    assert metrics.total_coverage == 75.0
    assert metrics.file_coverage == {
        "src/main.py": 50.0,
        "src/utils.py": 100.0,
    }


def test_lcov_file_not_found():
    with pytest.raises(FileNotFoundError, match="Coverage file not found"):
        parse_lcov(str(FIXTURES_DIR / "missing.info"))


def test_empty_lcov_report(tmp_path):
    coverage_file = tmp_path / "empty.info"
    coverage_file.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="Empty LCOV coverage report"):
        parse_lcov(str(coverage_file))


def test_lcov_missing_end_of_record(tmp_path):
    coverage_file = tmp_path / "incomplete.info"
    coverage_file.write_text(
        "TN:\nSF:src/main.py\nDA:1,1\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Missing end_of_record"):
        parse_lcov(str(coverage_file))


def test_lcov_invalid_line_data(tmp_path):
    coverage_file = tmp_path / "invalid.info"
    coverage_file.write_text(
        "TN:\nSF:src/main.py\nDA:abc,1\nend_of_record\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid line number or hit count"):
        parse_lcov(str(coverage_file))


def test_lcov_rejects_negative_hit_count(tmp_path):
    coverage_file = tmp_path / "negative.info"
    coverage_file.write_text(
        "TN:\nSF:src/main.py\nDA:1,-1\nend_of_record\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid DA record"):
        parse_lcov(str(coverage_file))


def test_lcov_allows_empty_source_record_when_other_record_has_lines(tmp_path):
    coverage_file = tmp_path / "mixed.info"
    coverage_file.write_text(
        "TN:\n"
        "SF:src/empty.py\n"
        "end_of_record\n"
        "TN:\n"
        "SF:src/main.py\n"
        "DA:1,1\n"
        "DA:2,0\n"
        "end_of_record\n",
        encoding="utf-8",
    )

    metrics = parse_lcov(str(coverage_file))

    assert metrics.total_coverage == 50.0
    assert metrics.file_coverage == {"src/main.py": 50.0}


def test_lcov_rejects_only_empty_source_records(tmp_path):
    coverage_file = tmp_path / "no-lines.info"
    coverage_file.write_text(
        "TN:\n" "SF:src/empty.py\n" "end_of_record\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Missing line coverage data"):
        parse_lcov(str(coverage_file))
