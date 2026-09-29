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

    line_rate = root.get("line-rate")

    if line_rate is None:
        raise ValueError(
            f"Missing 'line-rate' in coverage XML file: {file_path}"
        )

    try:
        line_rate = float(line_rate)
    except ValueError:
        raise ValueError(
            f"Invalid 'line-rate' value in coverage XML file: {file_path}"
        )

    total_coverage = line_rate * 100

    return CoverageMetrics(total_coverage=total_coverage) 