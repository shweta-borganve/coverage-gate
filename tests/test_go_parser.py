from pathlib import Path

import pytest

from src.go_parser import GoCoverageReport, parse_go_coverprofile

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_parse_go_coverprofile_returns_statement_coverage_and_line_data():
    report = FIXTURES_DIR / "sample_go.coverprofile"

    result = parse_go_coverprofile(str(report))

    assert isinstance(result, GoCoverageReport)
    assert result.total_coverage == pytest.approx(83.33, abs=0.01)

    assert result.file_coverage == {
        "example.com/project/src/example.go": pytest.approx(66.67, abs=0.01),
        "example.com/project/src/other.go": 100.0,
    }

    assert result.line_coverage == {
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
    }


@pytest.mark.parametrize("mode", ["set", "count", "atomic"])
def test_parse_go_coverprofile_supports_all_modes(tmp_path, mode):
    report = tmp_path / "coverage.out"
    report.write_text(
        f"mode: {mode}\nexample.go:1.1,2.2 2 1\n",
        encoding="utf-8",
    )

    result = parse_go_coverprofile(str(report))

    assert result.total_coverage == 100.0
    assert result.file_coverage == {"example.go": 100.0}


def test_parse_go_coverprofile_rejects_invalid_mode(tmp_path):
    report = tmp_path / "coverage.out"
    report.write_text("mode: invalid\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported Go coverage mode"):
        parse_go_coverprofile(str(report))


def test_parse_go_coverprofile_rejects_missing_mode(tmp_path):
    report = tmp_path / "coverage.out"
    report.write_text("example.go:1.1,2.2 2 1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="valid mode declaration"):
        parse_go_coverprofile(str(report))


def test_parse_go_coverprofile_rejects_duplicate_mode(tmp_path):
    report = tmp_path / "coverage.out"
    report.write_text(
        "mode: set\nmode: count\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate mode"):
        parse_go_coverprofile(str(report))


def test_parse_go_coverprofile_rejects_invalid_record(tmp_path):
    report = tmp_path / "coverage.out"
    report.write_text(
        "mode: set\ninvalid coverage record\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid Go coverage record"):
        parse_go_coverprofile(str(report))


def test_parse_go_coverprofile_rejects_invalid_set_count(tmp_path):
    report = tmp_path / "coverage.out"
    report.write_text(
        "mode: set\nexample.go:1.1,2.2 2 3\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="set mode"):
        parse_go_coverprofile(str(report))


def test_parse_go_coverprofile_rejects_zero_statements(tmp_path):
    report = tmp_path / "coverage.out"
    report.write_text(
        "mode: set\nexample.go:1.1,2.2 0 1\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid Go coverage record"):
        parse_go_coverprofile(str(report))


def test_parse_go_coverprofile_rejects_empty_report(tmp_path):
    report = tmp_path / "coverage.out"
    report.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="Empty Go coverage report"):
        parse_go_coverprofile(str(report))


def test_parse_go_coverprofile_rejects_report_without_records(tmp_path):
    report = tmp_path / "coverage.out"
    report.write_text("mode: set\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Missing coverage records"):
        parse_go_coverprofile(str(report))
