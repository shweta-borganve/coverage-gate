from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.main import _parse_coverage_report
from src.parser import CoverageMetrics


def test_json_extension_uses_coverage_json_parser():
    expected = SimpleNamespace(total_coverage=70.0)

    with (
        patch("src.main.parse_coverage_json", return_value=expected) as json_parser,
        patch("src.main.parse_lcov") as lcov_parser,
        patch("src.main.parse_cobertura") as cobertura_parser,
        patch("src.main.parse_jacoco") as jacoco_parser,
        patch("src.main.parse_go_coverprofile") as go_parser,
    ):
        result = _parse_coverage_report("reports/coverage.json")

    assert result is expected
    json_parser.assert_called_once_with("reports/coverage.json")
    lcov_parser.assert_not_called()
    cobertura_parser.assert_not_called()
    jacoco_parser.assert_not_called()
    go_parser.assert_not_called()


def test_info_extension_uses_lcov_parser():
    expected = SimpleNamespace(total_coverage=75.0)

    with (
        patch("src.main.parse_coverage_json") as json_parser,
        patch("src.main.parse_lcov", return_value=expected) as lcov_parser,
        patch("src.main.parse_cobertura") as cobertura_parser,
        patch("src.main.parse_jacoco") as jacoco_parser,
        patch("src.main.parse_go_coverprofile") as go_parser,
    ):
        result = _parse_coverage_report("reports/coverage.info")

    assert result is expected
    json_parser.assert_not_called()
    lcov_parser.assert_called_once_with("reports/coverage.info")
    cobertura_parser.assert_not_called()
    jacoco_parser.assert_not_called()
    go_parser.assert_not_called()


def test_xml_root_coverage_uses_cobertura_parser(tmp_path):
    report = tmp_path / "coverage.xml"
    report.write_text("<coverage/>", encoding="utf-8")
    expected = SimpleNamespace(total_coverage=85.0)

    with (
        patch("src.main.parse_coverage_json") as json_parser,
        patch("src.main.parse_lcov") as lcov_parser,
        patch("src.main.parse_cobertura", return_value=expected) as cobertura_parser,
        patch("src.main.parse_jacoco") as jacoco_parser,
        patch("src.main.parse_go_coverprofile") as go_parser,
    ):
        result = _parse_coverage_report(str(report))

    assert result is expected
    json_parser.assert_not_called()
    lcov_parser.assert_not_called()
    cobertura_parser.assert_called_once_with(str(report))
    jacoco_parser.assert_not_called()
    go_parser.assert_not_called()


def test_xml_root_report_uses_jacoco_parser(tmp_path):
    report = tmp_path / "coverage.xml"
    report.write_text("<report/>", encoding="utf-8")
    expected = SimpleNamespace(total_coverage=90.0)

    with (
        patch("src.main.parse_coverage_json") as json_parser,
        patch("src.main.parse_lcov") as lcov_parser,
        patch("src.main.parse_cobertura") as cobertura_parser,
        patch("src.main.parse_jacoco", return_value=expected) as jacoco_parser,
        patch("src.main.parse_go_coverprofile") as go_parser,
    ):
        result = _parse_coverage_report(str(report))

    assert result is expected
    json_parser.assert_not_called()
    lcov_parser.assert_not_called()
    cobertura_parser.assert_not_called()
    jacoco_parser.assert_called_once_with(str(report))
    go_parser.assert_not_called()


@pytest.mark.parametrize(
    "extension",
    [".out", ".coverprofile"],
)
def test_go_extension_uses_go_coverprofile_parser(tmp_path, extension):
    report = tmp_path / f"coverage{extension}"
    report.write_text(
        "mode: set\nexample.go:1.1,2.2 2 1\n",
        encoding="utf-8",
    )

    go_report = SimpleNamespace(
        total_coverage=100.0,
        file_coverage={"example.go": 100.0},
        line_coverage={"example.go": {1: True, 2: True}},
    )

    with (
        patch("src.main.parse_coverage_json") as json_parser,
        patch("src.main.parse_lcov") as lcov_parser,
        patch("src.main.parse_cobertura") as cobertura_parser,
        patch("src.main.parse_jacoco") as jacoco_parser,
        patch(
            "src.main.parse_go_coverprofile",
            return_value=go_report,
        ) as go_parser,
    ):
        result = _parse_coverage_report(str(report))

    assert result == CoverageMetrics(
        total_coverage=100.0,
        file_coverage={"example.go": 100.0},
    )
    go_parser.assert_called_once_with(str(report))
    json_parser.assert_not_called()
    lcov_parser.assert_not_called()
    cobertura_parser.assert_not_called()
    jacoco_parser.assert_not_called()
