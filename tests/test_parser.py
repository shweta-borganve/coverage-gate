import pytest

from src.parser import parse_cobertura


def test_parse():
    metrics = parse_cobertura("tests/fixtures/sample.xml")
    assert metrics.total_coverage == 85.0


def test_file_not_found():
    with pytest.raises(FileNotFoundError, match="Coverage file not found"):
        parse_cobertura("tests/fixtures/missing.xml")


def test_invalid_xml(tmp_path):
    coverage_file = tmp_path / "invalid.xml"
    coverage_file.write_text("<coverage>")

    with pytest.raises(ValueError, match="Invalid coverage XML file"):
        parse_cobertura(str(coverage_file))


def test_missing_line_rate(tmp_path):
    coverage_file = tmp_path / "missing-rate.xml"
    coverage_file.write_text("<coverage></coverage>")

    with pytest.raises(ValueError, match="Missing 'line-rate'"):
        parse_cobertura(str(coverage_file))


def test_invalid_line_rate(tmp_path):
    coverage_file = tmp_path / "invalid-rate.xml"
    coverage_file.write_text('<coverage line-rate="abc"></coverage>')

    with pytest.raises(ValueError, match="Invalid 'line-rate' value"):
        parse_cobertura(str(coverage_file)) 