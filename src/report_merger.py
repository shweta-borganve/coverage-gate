"""Utilities for merging line coverage from multiple reports."""

from src.parser import CoverageMetrics, parse_line_coverage


def merge_line_coverage(
    report_paths: list[str],
    root_dir: str,
) -> dict[str, dict[int, bool]]:
    """Merge reports, counting each source file and line only once."""
    merged: dict[str, dict[int, bool]] = {}

    for report_path in report_paths:
        report_lines = parse_line_coverage(
            report_path,
            root_dir=root_dir,
        )

        for filename, lines in report_lines.items():
            merged_lines = merged.setdefault(filename, {})

            for line_number, covered in lines.items():
                merged_lines[line_number] = (
                    merged_lines.get(line_number, False) or covered
                )

    return merged


def calculate_coverage_metrics(
    line_coverage: dict[str, dict[int, bool]],
) -> CoverageMetrics:
    """Calculate overall and per-file coverage from merged line data."""
    file_coverage = {}
    total_lines = 0
    covered_lines = 0

    for filename, lines in line_coverage.items():
        if not lines:
            continue

        file_total = len(lines)
        file_covered = sum(lines.values())

        total_lines += file_total
        covered_lines += file_covered

        file_coverage[filename] = file_covered / file_total * 100

    if total_lines == 0:
        raise ValueError("Coverage reports contain no valid executable lines.")

    return CoverageMetrics(
        total_coverage=covered_lines / total_lines * 100,
        file_coverage=file_coverage,
    )
