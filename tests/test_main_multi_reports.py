import pytest

from src.main import (
    _resolve_coverage_files,
    _split_coverage_files,
)


def test_split_coverage_files_accepts_multiple_paths():
    result = _split_coverage_files(
        "reports/python.xml, reports/javascript.json, reports/go.out"
    )

    assert result == [
        "reports/python.xml",
        "reports/javascript.json",
        "reports/go.out",
    ]


def test_split_coverage_files_accepts_single_path():
    assert _split_coverage_files("coverage.xml") == ["coverage.xml"]


@pytest.mark.parametrize(
    "configured_paths",
    [
        "",
        ",coverage.xml",
        "coverage.xml,",
        "coverage.xml,,other.xml",
        "coverage.xml,   ,other.xml",
    ],
)
def test_split_coverage_files_rejects_empty_paths(configured_paths):
    with pytest.raises(ValueError, match="non-empty report paths"):
        _split_coverage_files(configured_paths)


def test_resolve_coverage_files_accepts_multiple_workspace_paths(tmp_path):
    result = _resolve_coverage_files(
        str(tmp_path),
        "coverage.xml, reports/coverage.json",
    )

    assert result == [
        str(tmp_path / "coverage.xml"),
        str(tmp_path / "reports" / "coverage.json"),
    ]


def test_resolve_coverage_files_rejects_path_outside_workspace(tmp_path):
    with pytest.raises(
        ValueError,
        match="must be located inside GITHUB_WORKSPACE",
    ):
        _resolve_coverage_files(
            str(tmp_path),
            "coverage.xml, ../outside.xml",
        )


def test_resolve_coverage_files_rejects_absolute_path_outside_workspace(
    tmp_path,
):
    outside_path = tmp_path.parent / "outside.xml"

    with pytest.raises(
        ValueError,
        match="must be located inside GITHUB_WORKSPACE",
    ):
        _resolve_coverage_files(
            str(tmp_path),
            f"coverage.xml, {outside_path}",
        )
