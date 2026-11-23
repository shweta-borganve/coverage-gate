from types import SimpleNamespace
from unittest.mock import patch

from src.main import _parse_coverage_report


def test_json_extension_uses_coverage_json_parser():
    expected = SimpleNamespace(total_coverage=70.0)

    with (
        patch("src.main.parse_coverage_json", return_value=expected) as json_parser,
        patch("src.main.parse_lcov") as lcov_parser,
        patch("src.main.parse_cobertura") as cobertura_parser,
    ):
        result = _parse_coverage_report("reports/coverage.json")

    assert result is expected
    json_parser.assert_called_once_with("reports/coverage.json")
    lcov_parser.assert_not_called()
    cobertura_parser.assert_not_called()


def test_info_extension_uses_lcov_parser():
    expected = SimpleNamespace(total_coverage=75.0)

    with (
        patch("src.main.parse_coverage_json") as json_parser,
        patch("src.main.parse_lcov", return_value=expected) as lcov_parser,
        patch("src.main.parse_cobertura") as cobertura_parser,
    ):
        result = _parse_coverage_report("reports/coverage.info")

    assert result is expected
    json_parser.assert_not_called()
    lcov_parser.assert_called_once_with("reports/coverage.info")
    cobertura_parser.assert_not_called()


def test_xml_extension_uses_cobertura_parser():
    expected = SimpleNamespace(total_coverage=85.0)

    with (
        patch("src.main.parse_coverage_json") as json_parser,
        patch("src.main.parse_lcov") as lcov_parser,
        patch("src.main.parse_cobertura", return_value=expected) as cobertura_parser,
    ):
        result = _parse_coverage_report("reports/coverage.xml")

    assert result is expected
    json_parser.assert_not_called()
    lcov_parser.assert_not_called()
    cobertura_parser.assert_called_once_with("reports/coverage.xml")
