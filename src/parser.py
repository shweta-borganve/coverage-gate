import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field


@dataclass
class CoverageMetrics:
    total_coverage: float
    file_coverage: dict[str, float] = field(default_factory=dict)


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

    file_coverage = {}

    file_lines = {}

    for class_element in root.findall(".//class"):
        filename = class_element.get("filename")

        if filename is None:
            continue

        for line_element in class_element.findall("./lines/line"):
            line_number = line_element.get("number")
            hits = line_element.get("hits")

            if line_number is None or hits is None:
                continue

            try:
                hits = int(hits)
            except ValueError:
                continue

            line_coverage = file_lines.setdefault(filename, {})
            line_coverage[line_number] = (
                line_coverage.get(line_number, False) or hits > 0
            )

    file_coverage = {
        filename: sum(covered_lines.values()) / len(covered_lines) * 100
        for filename, covered_lines in file_lines.items()
        if covered_lines
    }

    return CoverageMetrics(
        total_coverage=total_coverage,
        file_coverage=file_coverage,
    )
