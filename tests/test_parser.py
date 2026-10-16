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


def test_parse_line_coverage(tmp_path):
    coverage_file = tmp_path / "line-coverage.xml"
    coverage_file.write_text(
        """<?xml version="1.0"?>
        <coverage line-rate="0.67">
            <packages>
                <package name="src">
                    <classes>
                        <class filename="src/parser.py">
                            <lines>
                                <line number="10" hits="1"/>
                                <line number="11" hits="0"/>
                                <line number="12" hits="2"/>
                            </lines>
                        </class>
                    </classes>
                </package>
            </packages>
        </coverage>
        """,
        encoding="utf-8",
    )

    from src.parser import parse_line_coverage

    result = parse_line_coverage(str(coverage_file))

    assert result == {
        "src/parser.py": {
            10: True,
            11: False,
            12: True,
        }
    }


@pytest.mark.parametrize(
    ("number", "hits"),
    [
        ("0", "1"),
        ("-1", "1"),
        ("10", "-1"),
        ("abc", "1"),
        ("10", "abc"),
    ],
)
def test_parse_line_coverage_rejects_invalid_line_data(tmp_path, number, hits):
    coverage_file = tmp_path / "invalid-line-data.xml"
    coverage_file.write_text(
        f"""<coverage line-rate="0.5">
            <packages>
                <package name="src">
                    <classes>
                        <class filename="src/parser.py">
                            <lines>
                                <line number="{number}" hits="{hits}"/>
                            </lines>
                        </class>
                    </classes>
                </package>
            </packages>
        </coverage>
        """,
        encoding="utf-8",
    )

    from src.parser import parse_line_coverage

    with pytest.raises(ValueError):
        parse_line_coverage(str(coverage_file))
