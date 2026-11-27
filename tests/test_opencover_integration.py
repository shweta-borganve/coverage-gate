from pathlib import Path

import pytest

from src.opencover_parser import parse_opencover_branch_counts
from src.parser import parse_line_coverage


def _write_opencover_report(
    report_path: Path,
    source_files: list[tuple[str, str]],
    sequence_points: list[tuple[str, int, int]],
) -> None:
    """Create a minimal OpenCover XML report for testing."""
    files_xml = "".join(
        f'<File uid="{file_id}" fullPath="{filename}" />'
        for file_id, filename in source_files
    )

    sequence_points_xml = "".join(
        f'<SequencePoint fileid="{file_id}" sl="{line}" vc="{visits}" />'
        for file_id, line, visits in sequence_points
    )

    report_path.write_text(
        f"""
        <CoverageSession>
            <Modules>
                <Module>
                    <Files>
                        {files_xml}
                    </Files>
                    <Classes>
                        <Class>
                            <Methods>
                                <Method>
                                    <SequencePoints>
                                        {sequence_points_xml}
                                    </SequencePoints>
                                </Method>
                            </Methods>
                        </Class>
                    </Classes>
                </Module>
            </Modules>
        </CoverageSession>
        """,
        encoding="utf-8",
    )


def test_parse_opencover_line_coverage(tmp_path):
    source_file = tmp_path / "src" / "example.cs"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("example source", encoding="utf-8")

    report = tmp_path / "coverage.xml"

    _write_opencover_report(
        report,
        [("1", str(source_file))],
        [
            ("1", 10, 1),
            ("1", 11, 0),
            ("1", 12, 0),
            ("1", 12, 2),
            ("1", 0, 1),
        ],
    )

    result = parse_line_coverage(str(report), root_dir=tmp_path)

    assert result == {
        "src/example.cs": {
            10: True,
            11: False,
            12: True,
        }
    }


def test_parse_opencover_normalizes_repository_relative_paths(tmp_path):
    source_file = tmp_path / "src" / "example.cs"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("example source", encoding="utf-8")

    report = tmp_path / "coverage.xml"

    _write_opencover_report(
        report,
        [("1", str(source_file))],
        [("1", 5, 1)],
    )

    result = parse_line_coverage(str(report), root_dir=tmp_path)

    assert "src/example.cs" in result
    assert result["src/example.cs"] == {5: True}


def test_parse_opencover_rejects_duplicate_normalized_filenames(tmp_path):
    source_file = tmp_path / "src" / "example.cs"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("example source", encoding="utf-8")

    alternative_path = (
        source_file.parent / ".." / source_file.parent.name / source_file.name
    )

    report = tmp_path / "coverage.xml"

    _write_opencover_report(
        report,
        [
            ("1", str(source_file)),
            ("2", str(alternative_path)),
        ],
        [
            ("1", 5, 1),
            ("2", 6, 0),
        ],
    )

    with pytest.raises(ValueError, match="Duplicate normalized filename"):
        parse_line_coverage(str(report), root_dir=tmp_path)


def test_parse_opencover_rejects_unsupported_xml_root(tmp_path):
    report = tmp_path / "invalid.xml"
    report.write_text("<invalid/>", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported coverage report root"):
        parse_line_coverage(str(report), root_dir=tmp_path)


def test_parse_opencover_rejects_missing_sequence_points(tmp_path):
    report = tmp_path / "empty.xml"

    report.write_text(
        """
        <CoverageSession>
            <Modules>
                <Module>
                    <Files>
                        <File uid="1" fullPath="src/example.cs"/>
                    </Files>
                </Module>
            </Modules>
        </CoverageSession>
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Missing sequence point coverage data"):
        parse_line_coverage(str(report), root_dir=tmp_path)


def test_parse_opencover_rejects_unknown_file_id(tmp_path):
    report = tmp_path / "unknown-file.xml"

    _write_opencover_report(
        report,
        [("1", "src/example.cs")],
        [("2", 10, 1)],
    )

    with pytest.raises(ValueError, match="Unknown file ID"):
        parse_line_coverage(str(report), root_dir=tmp_path)


def test_parse_opencover_branch_counts_returns_covered_and_valid_counts(
    tmp_path,
):
    report = tmp_path / "branches.xml"
    report.write_text(
        """
        <CoverageSession>
            <Modules>
                <Module>
                    <Classes>
                        <Class>
                            <Methods>
                                <Method>
                                    <BranchPoints>
                                        <BranchPoint vc="3"/>
                                        <BranchPoint vc="0"/>
                                        <BranchPoint vc="1"/>
                                    </BranchPoints>
                                </Method>
                            </Methods>
                        </Class>
                    </Classes>
                </Module>
            </Modules>
        </CoverageSession>
        """,
        encoding="utf-8",
    )

    assert parse_opencover_branch_counts(str(report)) == (2, 3)


def test_parse_opencover_branch_counts_returns_none_when_missing(tmp_path):
    report = tmp_path / "no-branches.xml"
    report.write_text(
        "<CoverageSession><Modules><Module/></Modules></CoverageSession>",
        encoding="utf-8",
    )

    assert parse_opencover_branch_counts(str(report)) is None


def test_parse_opencover_branch_counts_rejects_missing_visit_count(tmp_path):
    report = tmp_path / "missing-visits.xml"
    report.write_text(
        """
        <CoverageSession>
            <Modules>
                <Module>
                    <BranchPoint/>
                </Module>
            </Modules>
        </CoverageSession>
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Missing branch point data"):
        parse_opencover_branch_counts(str(report))


@pytest.mark.parametrize("visits", ["invalid", "-1"])
def test_parse_opencover_branch_counts_rejects_invalid_visit_count(
    tmp_path,
    visits,
):
    report = tmp_path / "invalid-visits.xml"
    report.write_text(
        f"""
        <CoverageSession>
            <Modules>
                <Module>
                    <BranchPoint vc="{visits}"/>
                </Module>
            </Modules>
        </CoverageSession>
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid branch point data"):
        parse_opencover_branch_counts(str(report))
