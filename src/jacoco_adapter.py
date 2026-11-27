from src.jacoco_parser import (
    parse_jacoco_branch_counts,
    parse_jacoco_xml,
)
from src.parser import CoverageMetrics


def parse_jacoco(file_path: str) -> CoverageMetrics:
    """Convert JaCoCo XML data into Coverage Gate coverage metrics."""
    total_coverage, file_lines = parse_jacoco_xml(file_path)
    branch_counts = parse_jacoco_branch_counts(file_path)

    file_coverage = {
        filename: sum(lines.values()) / len(lines) * 100
        for filename, lines in file_lines.items()
        if lines
    }

    covered_branches = None
    valid_branches = None

    if branch_counts is not None:
        covered_branches, valid_branches = branch_counts

    return CoverageMetrics(
        total_coverage=total_coverage,
        file_coverage=file_coverage,
        covered_branches=covered_branches,
        valid_branches=valid_branches,
    )
