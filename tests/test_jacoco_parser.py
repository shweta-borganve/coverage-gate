from pathlib import Path

import pytest

from src.jacoco_parser import (
    parse_jacoco_branch_counts,
    parse_jacoco_xml,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_parse_jacoco_xml_returns_overall_coverage_and_file_lines():
    report = FIXTURES_DIR / "sample_jacoco.xml"

    total_coverage, file_lines = parse_jacoco_xml(str(report))

    assert total_coverage == pytest.approx(66.67, abs=0.01)
    assert file_lines == {
        "src/example.py": {
            1: True,
            2: False,
            3: True,
        }
    }


def test_parse_jacoco_xml_rejects_unsupported_root(tmp_path):
    report = tmp_path / "invalid.xml"
    report.write_text("<coverage/>", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported JaCoCo XML root"):
        parse_jacoco_xml(str(report))


def test_parse_jacoco_xml_rejects_missing_line_counter(tmp_path):
    report = tmp_path / "missing-counter.xml"
    report.write_text("<report/>", encoding="utf-8")

    with pytest.raises(ValueError, match="LINE counter"):
        parse_jacoco_xml(str(report))


def test_parse_jacoco_xml_rejects_zero_total_lines(tmp_path):
    report = tmp_path / "zero-lines.xml"
    report.write_text(
        '<report><counter type="LINE" missed="0" covered="0"/>' "</report>",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="empty LINE coverage counts"):
        parse_jacoco_xml(str(report))


def test_parse_jacoco_xml_rejects_invalid_line_number(tmp_path):
    report = tmp_path / "invalid-line.xml"
    report.write_text(
        """
        <report>
            <package name="src">
                <sourcefile name="example.py">
                    <line nr="0" mi="0" ci="1"/>
                </sourcefile>
            </package>
            <counter type="LINE" missed="0" covered="1"/>
        </report>
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid line data"):
        parse_jacoco_xml(str(report))


def test_parse_jacoco_branch_counts_returns_covered_and_valid_counts(tmp_path):
    report = tmp_path / "branches.xml"
    report.write_text(
        """
        <report>
            <counter type="BRANCH" missed="2" covered="8"/>
        </report>
        """,
        encoding="utf-8",
    )

    assert parse_jacoco_branch_counts(str(report)) == (8, 10)


def test_parse_jacoco_branch_counts_returns_none_when_missing(tmp_path):
    report = tmp_path / "no-branches.xml"
    report.write_text("<report/>", encoding="utf-8")

    assert parse_jacoco_branch_counts(str(report)) is None


def test_parse_jacoco_branch_counts_returns_none_for_zero_branches(tmp_path):
    report = tmp_path / "zero-branches.xml"
    report.write_text(
        '<report><counter type="BRANCH" missed="0" covered="0"/></report>',
        encoding="utf-8",
    )

    assert parse_jacoco_branch_counts(str(report)) is None


def test_parse_jacoco_branch_counts_rejects_negative_counts(tmp_path):
    report = tmp_path / "negative-branches.xml"
    report.write_text(
        '<report><counter type="BRANCH" missed="-1" covered="2"/></report>',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid BRANCH coverage counts"):
        parse_jacoco_branch_counts(str(report))
