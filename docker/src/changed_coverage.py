from dataclasses import dataclass


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


def generate_changed_coverage_report(
    changed_lines: dict[str, set[int]],
    line_coverage: dict[str, dict[int, bool]] | None,
) -> ChangedCoverageReport:
    """Report coverage for changed lines without enforcing a threshold."""
    if line_coverage is None:
        return ChangedCoverageReport(
            available=False,
            files=[],
            message="Changed-code coverage not available: line data is missing.",
        )

    results = []

    for filename, lines in changed_lines.items():
        if filename not in line_coverage:
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

        results.append(
            ChangedFileCoverage(
                filename=filename,
                changed_lines=len(lines),
                covered_lines=len(covered_line_numbers),
                uncovered_lines=len(uncovered_line_numbers),
                uncovered_line_numbers=uncovered_line_numbers,
            )
        )

    results.sort(key=lambda item: (-item.uncovered_lines, item.filename))

    return ChangedCoverageReport(
        available=True,
        files=results,
        message="Changed-code coverage report generated.",
    )
