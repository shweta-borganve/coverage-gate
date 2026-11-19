from dataclasses import dataclass

from src.logger_config import configure_logger

logger = configure_logger(__name__)


@dataclass
class ChangedFileCoverage:
    filename: str
    changed_lines: int
    covered_lines: int
    uncovered_lines: int
    uncovered_line_numbers: list[int]


@dataclass
class ChangedCoverageReport:
    available: bool
    files: list[ChangedFileCoverage]
    message: str
    total_changed_lines: int = 0
    covered_changed_lines: int = 0
    coverage_percentage: float | None = None


def generate_changed_coverage_report(
    changed_lines: dict[str, set[int]],
    line_coverage: dict[str, dict[int, bool]] | None,
) -> ChangedCoverageReport:
    """Report aggregate and per-file coverage for changed lines."""
    logger.info("Generating changed-code coverage report.")
    logger.debug(
        "Received changed-line data for %d files.",
        len(changed_lines),
    )

    if line_coverage is None:
        logger.warning(
            "Changed-code coverage is unavailable because line data is missing."
        )
        return ChangedCoverageReport(
            available=False,
            files=[],
            message="Changed-code coverage not available: line data is missing.",
        )

    results = []

    for filename, lines in changed_lines.items():
        logger.debug(
            "Processing %d changed lines for %s.",
            len(lines),
            filename,
        )

        if filename not in line_coverage:
            logger.warning(
                "Changed-code coverage is unavailable: no line coverage data for %s.",
                filename,
            )
            return ChangedCoverageReport(
                available=False,
                files=[],
                message=(
                    "Changed-code coverage not available: "
                    f"line data is missing for {filename}."
                ),
            )

        coverage_for_file = line_coverage[filename]

        missing_lines = lines - coverage_for_file.keys()
        if missing_lines:
            logger.warning(
                "Changed-code coverage is unavailable for %s: "
                "coverage data is missing for lines %s.",
                filename,
                sorted(missing_lines),
            )
            return ChangedCoverageReport(
                available=False,
                files=[],
                message=(
                    "Changed-code coverage not available: coverage data is "
                    f"missing for lines in {filename}: "
                    f"{sorted(missing_lines)}."
                ),
            )

        covered_line_numbers = sorted(
            line_number for line_number in lines if coverage_for_file[line_number]
        )
        uncovered_line_numbers = sorted(
            line_number for line_number in lines if not coverage_for_file[line_number]
        )

        file_result = ChangedFileCoverage(
            filename=filename,
            changed_lines=len(lines),
            covered_lines=len(covered_line_numbers),
            uncovered_lines=len(uncovered_line_numbers),
            uncovered_line_numbers=uncovered_line_numbers,
        )
        results.append(file_result)

        logger.info(
            "Changed-code coverage for %s: %d/%d lines covered; %d uncovered.",
            filename,
            file_result.covered_lines,
            file_result.changed_lines,
            file_result.uncovered_lines,
        )

        if uncovered_line_numbers:
            logger.debug(
                "Uncovered changed lines in %s: %s.",
                filename,
                uncovered_line_numbers,
            )

    results.sort(key=lambda item: (-item.uncovered_lines, item.filename))

    total_changed_lines = sum(item.changed_lines for item in results)
    covered_changed_lines = sum(item.covered_lines for item in results)

    coverage_percentage = (
        covered_changed_lines / total_changed_lines * 100
        if total_changed_lines
        else None
    )

    logger.info(
        "Aggregate changed-code coverage: %s (%d/%d lines).",
        (
            f"{coverage_percentage:.2f}%"
            if coverage_percentage is not None
            else "not applicable"
        ),
        covered_changed_lines,
        total_changed_lines,
    )

    return ChangedCoverageReport(
        available=True,
        files=results,
        message="Changed-code coverage report generated.",
        total_changed_lines=total_changed_lines,
        covered_changed_lines=covered_changed_lines,
        coverage_percentage=coverage_percentage,
    )
