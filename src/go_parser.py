import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GoCoverageReport:
    """Store parsed Go coverage metrics and line-level coverage data."""

    total_coverage: float
    file_coverage: dict[str, float]
    line_coverage: dict[str, dict[int, bool]]


def parse_go_coverprofile(file_path: str) -> GoCoverageReport:
    """Parse a Go coverprofile and return statement-based coverage metrics."""
    coverage_file = Path(file_path)

    try:
        content = coverage_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"Coverage file not found: {file_path}")

    if not content.strip():
        raise ValueError("Empty Go coverage report.")

    records = content.splitlines()
    mode = None

    total_statements = 0
    covered_statements = 0

    file_totals: dict[str, int] = {}
    file_covered: dict[str, int] = {}
    line_coverage: dict[str, dict[int, bool]] = {}

    record_pattern = re.compile(r"^(.+):(\d+)\.(\d+),(\d+)\.(\d+)\s+(\d+)\s+(\d+)$")

    for line_number, raw_line in enumerate(records, start=1):
        line = raw_line.strip()

        if not line:
            continue

        if mode is None:
            if not line.startswith("mode:"):
                raise ValueError(
                    "Go coverage report must begin with a valid mode declaration."
                )

            mode = line.partition(":")[2].strip()

            if mode not in {"set", "count", "atomic"}:
                raise ValueError(f"Unsupported Go coverage mode: {mode}")

            continue

        if line.startswith("mode:"):
            raise ValueError("Duplicate mode declaration in Go coverage report.")

        match = record_pattern.fullmatch(line)

        if match is None:
            raise ValueError(f"Invalid Go coverage record at line {line_number}.")

        (
            filename,
            start_line_text,
            start_column_text,
            end_line_text,
            end_column_text,
            statements_text,
            count_text,
        ) = match.groups()

        try:
            start_line = int(start_line_text)
            start_column = int(start_column_text)
            end_line = int(end_line_text)
            end_column = int(end_column_text)
            statements = int(statements_text)
            count = int(count_text)
        except ValueError as error:
            raise ValueError(
                f"Invalid numeric value in Go coverage record at line {line_number}."
            ) from error

        if (
            not filename.strip()
            or start_line < 1
            or start_column < 1
            or end_line < start_line
            or end_column < 1
            or statements < 1
            or count < 0
        ):
            raise ValueError(f"Invalid Go coverage record at line {line_number}.")

        if mode == "set" and count not in {0, 1}:
            raise ValueError(
                f"Invalid execution count for Go set mode at line {line_number}."
            )

        is_covered = count > 0

        total_statements += statements
        file_totals[filename] = file_totals.get(filename, 0) + statements

        if is_covered:
            covered_statements += statements
            file_covered[filename] = file_covered.get(filename, 0) + statements

        lines = line_coverage.setdefault(filename, {})

        for source_line in range(start_line, end_line + 1):
            lines[source_line] = lines.get(source_line, False) or is_covered

    if mode is None:
        raise ValueError("Missing Go coverage mode declaration.")

    if total_statements == 0:
        raise ValueError("Missing coverage records in Go coverage report.")

    total_coverage = covered_statements / total_statements * 100

    file_coverage = {
        filename: file_covered.get(filename, 0) / statements * 100
        for filename, statements in file_totals.items()
    }

    return GoCoverageReport(
        total_coverage=total_coverage,
        file_coverage=file_coverage,
        line_coverage=line_coverage,
    )
