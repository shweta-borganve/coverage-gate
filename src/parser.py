import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass


@dataclass
class CoverageMetrics:
    total_coverage: float


def parse_cobertura(file_path: str) -> CoverageMetrics:
    try:
        tree = ET.parse(file_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Coverage file not found: {file_path}")
    except ET.ParseError:
        raise ValueError(f"Invalid coverage XML file: {file_path}")

    root = tree.getroot()

    if root.tag != "coverage":
        raise ValueError(f"Unsupported coverage report root: {root.tag}")

    line_rate = root.get("line-rate")

    if line_rate is None:
        raise ValueError(f"Missing 'line-rate' in coverage XML file: {file_path}")

    try:
        line_rate = float(line_rate)
    except ValueError:
        raise ValueError(f"Invalid 'line-rate' value in coverage XML file: {file_path}")

    if not math.isfinite(line_rate) or not 0 <= line_rate <= 1:
        raise ValueError(
            f"Invalid 'line-rate' value in coverage XML file: {file_path}. "
            "Expected a value between 0 and 1."
        )

    total_coverage = line_rate * 100

    return CoverageMetrics(total_coverage=total_coverage)


def parse_line_coverage(file_path: str) -> dict[str, dict[int, bool]]:
    """Return line coverage for each source file in a Cobertura XML report."""
    try:
        tree = ET.parse(file_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Coverage file not found: {file_path}")
    except ET.ParseError:
        raise ValueError(f"Invalid coverage XML file: {file_path}")

    root = tree.getroot()

    if root.tag != "coverage":
        raise ValueError(f"Unsupported coverage report root: {root.tag}")

    file_lines: dict[str, dict[int, bool]] = {}

    for class_element in root.iter("class"):
        filename = class_element.get("filename")

        if not filename:
            continue

        for line_element in class_element.findall("./lines/line"):
            number_text = line_element.get("number")
            hits_text = line_element.get("hits")

            if number_text is None or hits_text is None:
                raise ValueError(
                    f"Missing line number or hits in coverage XML file: {file_path}"
                )

            try:
                line_number = int(number_text)
                hits = int(hits_text)
            except ValueError as error:
                raise ValueError(
                    f"Invalid line number or hits in coverage XML file: {file_path}"
                ) from error

            if line_number < 1 or hits < 0:
                raise ValueError(
                    f"Invalid line number or hits in coverage XML file: {file_path}"
                )

            lines = file_lines.setdefault(filename, {})
            lines[line_number] = lines.get(line_number, False) or hits > 0

    return file_lines
