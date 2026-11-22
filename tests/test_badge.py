"""Tests for SVG coverage badge generation."""

import math
import xml.etree.ElementTree as ET

import pytest

from src.badge import generate_badge


@pytest.mark.parametrize(
    ("coverage", "expected_color"),
    [
        (0, "#e05d44"),
        (59.9, "#e05d44"),
        (60, "#dfb317"),
        (79.9, "#dfb317"),
        (80, "#4c1"),
        (100, "#4c1"),
    ],
)
def test_generate_badge_uses_correct_color(
    tmp_path,
    coverage,
    expected_color,
):
    output = tmp_path / "coverage.svg"

    generate_badge(coverage, output)

    content = output.read_text(encoding="utf-8")
    assert f'fill="{expected_color}"' in content


def test_generate_badge_creates_valid_svg(tmp_path):
    output = tmp_path / "coverage.svg"

    generate_badge(85.5, output)

    root = ET.parse(output).getroot()

    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert root.attrib["role"] == "img"


def test_generate_badge_displays_percentage(tmp_path):
    output = tmp_path / "coverage.svg"

    generate_badge(85.567, output)

    content = output.read_text(encoding="utf-8")
    assert "85.6%" in content


def test_generate_badge_creates_parent_directories(tmp_path):
    output = tmp_path / "reports" / "badges" / "coverage.svg"

    result = generate_badge(90, output)

    assert result == output
    assert output.is_file()


def test_generate_badge_accepts_numeric_string(tmp_path):
    output = tmp_path / "coverage.svg"

    generate_badge("75.5", output)

    assert "75.5%" in output.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "coverage",
    [
        -1,
        101,
        float("nan"),
        float("inf"),
        float("-inf"),
        "invalid",
        None,
    ],
)
def test_generate_badge_rejects_invalid_coverage(
    tmp_path,
    coverage,
):
    output = tmp_path / "coverage.svg"

    with pytest.raises(ValueError):
        generate_badge(coverage, output)

    assert not output.exists()


def test_generate_badge_rejects_non_finite_values(tmp_path):
    output = tmp_path / "coverage.svg"

    for value in (math.nan, math.inf, -math.inf):
        with pytest.raises(ValueError):
            generate_badge(value, output)

    assert not output.exists()
