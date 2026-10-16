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


def test_unsupported_root_element():
    with pytest.raises(ValueError, match="Unsupported coverage report root"):
        parse_cobertura("tests/fixtures/unsupported.xml")


@pytest.mark.parametrize("line_rate", ["-0.2", "1.5", "NaN", "inf", "-inf"])
def test_out_of_range_line_rate(tmp_path, line_rate):
    coverage_file = tmp_path / "out-of-range.xml"
    coverage_file.write_text(f'<coverage line-rate="{line_rate}"></coverage>')

    with pytest.raises(ValueError):
        parse_cobertura(str(coverage_file))


def test_empty_xml_report(tmp_path):
    coverage_file = tmp_path / "empty.xml"
    coverage_file.write_text("")

    with pytest.raises(ValueError):
        parse_cobertura(str(coverage_file))
feature/per-file-coverage


def test_parse_per_file_coverage():
    metrics = parse_cobertura("tests/fixtures/per_file.xml")

    assert metrics.total_coverage == 80.0
    assert metrics.file_coverage == {
        "src/billing.py": 90.0,
        "src/database.py": 60.0,
    }


def test_invalid_per_file_line_rate(tmp_path):
    coverage_file = tmp_path / "invalid-per-file.xml"
    coverage_file.write_text(
        '<coverage line-rate="0.80">'
        '<class filename="src/billing.py" line-rate="abc"/>'
        "</coverage>"
    )

    metrics = parse_cobertura(str(coverage_file))

    assert metrics.total_coverage == 80.0
    assert metrics.file_coverage == {}


def test_parse_duplicate_filenames():
    metrics = parse_cobertura("tests/fixtures/duplicate_filenames.xml")

    assert metrics.file_coverage == {
        "src/billing.py": 60.0,
    }

main
