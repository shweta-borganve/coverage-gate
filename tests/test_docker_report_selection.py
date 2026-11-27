import xml.etree.ElementTree as ET
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from docker.entrypoint import parse_coverage_report


def test_json_extension_uses_coverage_json_parser():
    expected = SimpleNamespace(total_coverage=70.0)

    with (
        patch(
            "docker.entrypoint.parse_coverage_json",
            return_value=expected,
        ) as json_parser,
        patch("docker.entrypoint.parse_lcov") as lcov_parser,
        patch("docker.entrypoint.parse_cobertura") as cobertura_parser,
    ):
        result = parse_coverage_report("reports/coverage.json")

    assert result is expected
    json_parser.assert_called_once_with("reports/coverage.json")
    lcov_parser.assert_not_called()
    cobertura_parser.assert_not_called()


def test_info_extension_uses_lcov_parser():
    expected = SimpleNamespace(total_coverage=75.0)

    with (
        patch("docker.entrypoint.parse_coverage_json") as json_parser,
        patch(
            "docker.entrypoint.parse_lcov",
            return_value=expected,
        ) as lcov_parser,
        patch("docker.entrypoint.parse_cobertura") as cobertura_parser,
    ):
        result = parse_coverage_report("reports/coverage.info")

    assert result is expected
    json_parser.assert_not_called()
    lcov_parser.assert_called_once_with("reports/coverage.info")
    cobertura_parser.assert_not_called()


def test_xml_extension_uses_cobertura_parser():
    expected = SimpleNamespace(total_coverage=85.0)

    with (
        patch("docker.entrypoint.ET.parse") as xml_parser,
        patch(
            "docker.entrypoint.parse_cobertura",
            return_value=expected,
        ) as cobertura_parser,
        patch("docker.entrypoint.parse_jacoco") as jacoco_parser,
    ):
        xml_parser.return_value.getroot.return_value.tag = "coverage"

        result = parse_coverage_report("reports/coverage.xml")

    assert result is expected
    xml_parser.assert_called_once_with("reports/coverage.xml")
    cobertura_parser.assert_called_once_with("reports/coverage.xml")
    jacoco_parser.assert_not_called()


def test_xml_extension_uses_jacoco_parser():
    expected = SimpleNamespace(total_coverage=90.0)

    with (
        patch("docker.entrypoint.ET.parse") as xml_parser,
        patch("docker.entrypoint.parse_cobertura") as cobertura_parser,
        patch(
            "docker.entrypoint.parse_jacoco",
            return_value=expected,
        ) as jacoco_parser,
    ):
        xml_parser.return_value.getroot.return_value.tag = "report"

        result = parse_coverage_report("reports/jacoco.xml")

    assert result is expected
    xml_parser.assert_called_once_with("reports/jacoco.xml")
    jacoco_parser.assert_called_once_with("reports/jacoco.xml")
    cobertura_parser.assert_not_called()


@pytest.mark.parametrize(
    "filename",
    [
        "reports/coverage.out",
        "reports/coverage.coverprofile",
    ],
)
def test_go_extension_uses_go_parser(filename):
    expected = SimpleNamespace(total_coverage=80.0)

    with patch(
        "docker.entrypoint.parse_go_coverprofile",
        return_value=expected,
    ) as go_parser:
        result = parse_coverage_report(filename)

    assert result is expected
    go_parser.assert_called_once_with(filename)


def test_invalid_xml_raises_value_error():
    with (
        patch(
            "docker.entrypoint.ET.parse",
            side_effect=ET.ParseError("Invalid XML"),
        ),
        pytest.raises(ValueError, match="Invalid coverage XML"),
    ):
        parse_coverage_report("reports/invalid.xml")
