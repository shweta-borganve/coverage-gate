from pathlib import Path

import pytest

from src.parser import parse_cobertura, parse_lcov, parse_line_coverage

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_parse():
    metrics = parse_cobertura(FIXTURES_DIR / "sample.xml")
    assert metrics.total_coverage == 85.0


def test_file_not_found():
    with pytest.raises(FileNotFoundError, match="Coverage file not found"):
        parse_cobertura(FIXTURES_DIR / "missing.xml")


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
        parse_cobertura(FIXTURES_DIR / "unsupported.xml")


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

    result = parse_line_coverage(str(coverage_file))

    assert result == {
        "src/parser.py": {
            10: True,
            11: False,
            12: True,
        }
    }


def test_parse_per_file_coverage():
    metrics = parse_cobertura(FIXTURES_DIR / "per_file.xml")

    assert metrics.total_coverage == 80.0
    assert metrics.file_coverage == {
        "src/parser.py": 90.0,
        "src/main.py": 60.0,
    }


def test_invalid_per_file_line_rate(tmp_path):
    coverage_file = tmp_path / "invalid-per-file.xml"
    coverage_file.write_text(
        '<coverage line-rate="0.80">'
        '<class filename="src/parser.py" line-rate="abc"/>'
        "</coverage>"
    )

    metrics = parse_cobertura(str(coverage_file))

    assert metrics.total_coverage == 80.0
    assert metrics.file_coverage == {}


def test_parse_duplicate_filenames():
    metrics = parse_cobertura(FIXTURES_DIR / "duplicate_filenames.xml")

    assert metrics.file_coverage == {
        "src/parser.py": 60.0,
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

    with pytest.raises(ValueError):
        parse_line_coverage(str(coverage_file))


@pytest.mark.parametrize(
    "line_entries",
    [
        ('<line number="1" hits="0"/>', '<line number="1" hits="1"/>'),
        ('<line number="1" hits="1"/>', '<line number="1" hits="0"/>'),
    ],
)
def test_duplicate_line_coverage_is_independent_of_xml_order(tmp_path, line_entries):
    coverage_file = tmp_path / "duplicate-lines.xml"
    coverage_file.write_text(
        '<coverage line-rate="1.0">'
        '<class filename="src/parser.py"><lines>'
        f"{line_entries[0]}{line_entries[1]}"
        "</lines></class></coverage>"
    )

    metrics = parse_cobertura(str(coverage_file))

    assert metrics.file_coverage == {"src/parser.py": 100.0}


def test_parse_line_coverage_normalizes_source_path(tmp_path):
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    (source_dir / "parser.py").write_text(
        "print('hello')\n",
        encoding="utf-8",
    )

    coverage_file = tmp_path / "coverage.xml"
    coverage_file.write_text(
        f"""<coverage line-rate="1.0">
            <sources>
                <source>{source_dir}</source>
            </sources>
            <packages>
                <package name="src">
                    <classes>
                        <class filename="parser.py">
                            <lines>
                                <line number="1" hits="1"/>
                            </lines>
                        </class>
                    </classes>
                </package>
            </packages>
        </coverage>
        """,
        encoding="utf-8",
    )

    result = parse_line_coverage(
        str(coverage_file),
        root_dir=tmp_path,
    )

    assert result == {"src/parser.py": {1: True}}


def test_parse_line_coverage_merges_classes_with_normalized_same_path(
    tmp_path,
):
    source_dir = tmp_path / "src"
    source_dir.mkdir()

    source_file = source_dir / "parser.py"
    source_file.write_text(
        "print('hello')\nprint('world')\n",
        encoding="utf-8",
    )

    coverage_file = tmp_path / "coverage.xml"
    coverage_file.write_text(
        f"""<coverage line-rate="0.5">
            <sources>
                <source>{tmp_path}</source>
            </sources>
            <packages>
                <package name="src">
                    <classes>
                        <class filename="src/parser.py">
                            <lines>
                                <line number="1" hits="1"/>
                            </lines>
                        </class>
                        <class filename="{source_file}">
                            <lines>
                                <line number="2" hits="0"/>
                            </lines>
                        </class>
                    </classes>
                </package>
            </packages>
        </coverage>
        """,
        encoding="utf-8",
    )

    result = parse_line_coverage(
        str(coverage_file),
        root_dir=tmp_path,
    )

    assert result == {
        "src/parser.py": {
            1: True,
            2: False,
        }
    }


def test_parse_lcov_report(tmp_path):
    coverage_file = tmp_path / "coverage.info"
    coverage_file.write_text(
        """TN:
SF:src/main.py
DA:1,1
DA:2,0
LF:2
LH:1
end_of_record
TN:
SF:src/utils.py
DA:1,2
DA:2,5
LF:2
LH:2
end_of_record
""",
        encoding="utf-8",
    )

    metrics = parse_lcov(coverage_file)

    assert metrics.total_coverage == 75.0
    assert metrics.file_coverage == {
        "src/main.py": 50.0,
        "src/utils.py": 100.0,
    }


def test_parse_lcov_line_coverage(tmp_path):
    coverage_file = tmp_path / "coverage.info"
    coverage_file.write_text(
        """TN:
SF:src/main.py
DA:1,1
DA:2,0
LF:2
LH:1
end_of_record
""",
        encoding="utf-8",
    )

    result = parse_line_coverage(str(coverage_file))

    assert result == {
        "src/main.py": {
            1: True,
            2: False,
        }
    }


def test_lcov_file_not_found():
    with pytest.raises(FileNotFoundError):
        parse_lcov(FIXTURES_DIR / "missing.info")


def test_parse_jacoco_line_coverage():
    coverage_file = FIXTURES_DIR / "sample_jacoco.xml"

    result = parse_line_coverage(str(coverage_file))

    assert result == {
        "src/example.py": {
            1: True,
            2: False,
            3: True,
        }
    }


def test_parse_jacoco_line_coverage_normalizes_source_path(tmp_path):
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    (source_dir / "example.py").write_text(
        "print('hello')\n",
        encoding="utf-8",
    )

    coverage_file = tmp_path / "coverage.xml"
    coverage_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
        <report name="Coverage Gate">
            <package name="src">
                <sourcefile name="example.py">
                    <line nr="1" mi="0" ci="2" mb="0" cb="0"/>
                </sourcefile>
            </package>
            <counter type="LINE" missed="0" covered="1"/>
        </report>
        """,
        encoding="utf-8",
    )

    result = parse_line_coverage(
        str(coverage_file),
        root_dir=tmp_path,
    )

    assert result == {"src/example.py": {1: True}}


def test_parse_go_line_coverage():
    coverage_file = FIXTURES_DIR / "sample_go.coverprofile"

    result = parse_line_coverage(str(coverage_file))

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
    }


def test_parse_go_line_coverage_normalizes_source_path(tmp_path):
    source_dir = tmp_path / "src"
    source_dir.mkdir()

    source_file = source_dir / "example.go"
    source_file.write_text(
        "package src\n",
        encoding="utf-8",
    )

    coverage_file = tmp_path / "coverage.out"
    coverage_file.write_text(
        f"mode: set\n{source_file}:1.1,2.2 2 1\n",
        encoding="utf-8",
    )

    result = parse_line_coverage(
        str(coverage_file),
        root_dir=tmp_path,
    )

    assert result == {"src/example.go": {1: True, 2: True}}


def test_parse_go_line_coverage_rejects_duplicate_normalized_filenames(tmp_path):
    source_dir = tmp_path / "src"
    source_dir.mkdir()

    source_file = source_dir / "example.go"
    source_file.write_text(
        "package src\n",
        encoding="utf-8",
    )

    coverage_file = tmp_path / "coverage.out"
    coverage_file.write_text(
        f"""mode: set
{source_file}:1.1,1.2 1 1
src/example.go:2.1,2.2 1 0
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate normalized filename"):
        parse_line_coverage(
            str(coverage_file),
            root_dir=tmp_path,
        )


def test_parse_lcov_line_coverage_rejects_duplicate_normalized_filenames(
    tmp_path,
):
    source_dir = tmp_path / "src"
    source_dir.mkdir()

    source_file = source_dir / "example.py"
    source_file.write_text(
        "print('hello')\n",
        encoding="utf-8",
    )

    coverage_file = tmp_path / "coverage.info"
    coverage_file.write_text(
        f"""SF:{source_file}
DA:1,1
LF:1
LH:1
end_of_record
SF:src/example.py
DA:2,0
LF:1
LH:0
end_of_record
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate normalized filename"):
        parse_line_coverage(
            str(coverage_file),
            root_dir=tmp_path,
        )


def test_parse_go_line_coverage_resolves_module_relative_path(tmp_path):
    source_file = tmp_path / "internal" / "api" / "handler.go"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("package api\n", encoding="utf-8")

    coverage_file = tmp_path / "coverage.out"
    coverage_file.write_text(
        "mode: set\n"
        "github.com/example/project/internal/api/handler.go:1.1,2.2 2 1\n",
        encoding="utf-8",
    )

    result = parse_line_coverage(str(coverage_file), root_dir=tmp_path)

    assert result == {"internal/api/handler.go": {1: True, 2: True}}


def test_parse_jacoco_line_coverage_resolves_maven_source_path(tmp_path):
    source_file = (
        tmp_path / "module-a" / "src" / "main" / "java" / "com" / "example" / "Foo.java"
    )
    source_file.parent.mkdir(parents=True)
    source_file.write_text("class Foo {}\n", encoding="utf-8")

    coverage_file = tmp_path / "coverage.xml"
    coverage_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
        <report name="Coverage">
            <package name="com/example">
                <sourcefile name="Foo.java">
                    <line nr="1" mi="0" ci="1" mb="0" cb="0"/>
                </sourcefile>
            </package>
            <counter type="LINE" missed="0" covered="1"/>
        </report>
        """,
        encoding="utf-8",
    )

    result = parse_line_coverage(str(coverage_file), root_dir=tmp_path)

    assert result == {"module-a/src/main/java/com/example/Foo.java": {1: True}}


def test_parse_jacoco_line_coverage_does_not_guess_ambiguous_source_path(
    tmp_path, caplog
):
    for module in ("module-a", "module-b"):
        source_file = (
            tmp_path / module / "src" / "main" / "java" / "com" / "example" / "Foo.java"
        )
        source_file.parent.mkdir(parents=True)
        source_file.write_text("class Foo {}\n", encoding="utf-8")

    coverage_file = tmp_path / "coverage.xml"
    coverage_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
        <report name="Coverage">
            <package name="com/example">
                <sourcefile name="Foo.java">
                    <line nr="1" mi="0" ci="1" mb="0" cb="0"/>
                </sourcefile>
            </package>
            <counter type="LINE" missed="0" covered="1"/>
        </report>
        """,
        encoding="utf-8",
    )

    result = parse_line_coverage(str(coverage_file), root_dir=tmp_path)

    assert result == {"com/example/Foo.java": {1: True}}
    assert "Ambiguous coverage source path" in caplog.text
