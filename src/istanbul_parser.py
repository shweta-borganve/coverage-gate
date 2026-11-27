import json
from pathlib import Path


def _load_istanbul_report(file_path: str) -> dict:
    """Load and validate an Istanbul/NYC JSON report."""
    coverage_file = Path(file_path)

    try:
        content = coverage_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"Coverage file not found: {file_path}")

    if not content.strip():
        raise ValueError("Empty Istanbul/NYC coverage JSON report.")

    try:
        report = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid Istanbul/NYC coverage JSON report: {file_path}"
        ) from error

    if not isinstance(report, dict) or not report:
        raise ValueError(
            "Invalid Istanbul/NYC coverage JSON report: "
            "expected a non-empty JSON object."
        )

    return report


def parse_istanbul_json(
    file_path: str,
) -> tuple[float, dict[str, dict[int, bool]]]:
    """Parse Istanbul/NYC JSON into overall and per-file line coverage."""
    report = _load_istanbul_report(file_path)
    file_lines: dict[str, dict[int, bool]] = {}

    for filename, file_data in report.items():
        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("Invalid filename in Istanbul/NYC coverage report.")

        if not isinstance(file_data, dict):
            raise TypeError(f"Invalid Istanbul/NYC coverage data for {filename}.")

        statement_map = file_data.get("statementMap")
        statement_counts = file_data.get("s")

        if not isinstance(statement_map, dict):
            raise TypeError(f"Missing or invalid statementMap for {filename}.")

        if not isinstance(statement_counts, dict):
            raise TypeError(f"Missing or invalid statement counts for {filename}.")

        if not statement_map:
            raise ValueError(f"Missing statement coverage data for {filename}.")

        if set(statement_map) != set(statement_counts):
            raise ValueError(
                f"Inconsistent statement IDs in Istanbul/NYC report for {filename}."
            )

        lines: dict[int, bool] = {}

        for statement_id, location in statement_map.items():
            if not isinstance(location, dict):
                raise TypeError(f"Invalid statement location for {filename}.")

            start = location.get("start")

            if not isinstance(start, dict):
                raise TypeError(f"Missing statement start location for {filename}.")

            line_number = start.get("line")

            if (
                isinstance(line_number, bool)
                or not isinstance(line_number, int)
                or line_number < 1
            ):
                raise ValueError(f"Invalid statement line number for {filename}.")

            count = statement_counts[statement_id]

            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                raise ValueError(f"Invalid statement execution count for {filename}.")

            covered = count > 0
            lines[line_number] = lines.get(line_number, False) or covered

        file_lines[filename] = lines

    all_lines = [covered for lines in file_lines.values() for covered in lines.values()]

    if not all_lines:
        raise ValueError("Missing statement coverage data in Istanbul/NYC report.")

    total_coverage = sum(all_lines) / len(all_lines) * 100

    return total_coverage, file_lines


def parse_istanbul_branch_counts(file_path: str) -> tuple[int, int] | None:
    """Return covered and valid branch-path counts from Istanbul/NYC JSON."""
    report = _load_istanbul_report(file_path)

    covered_branches = 0
    valid_branches = 0
    found_branch_data = False

    for filename, file_data in report.items():
        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("Invalid filename in Istanbul/NYC coverage report.")

        if not isinstance(file_data, dict):
            raise TypeError(f"Invalid Istanbul/NYC coverage data for {filename}.")

        branch_map = file_data.get("branchMap")
        branch_counts = file_data.get("b")

        if branch_map is None and branch_counts is None:
            continue

        if not isinstance(branch_map, dict) or not isinstance(branch_counts, dict):
            raise TypeError(f"Missing or invalid branch coverage data for {filename}.")

        if set(branch_map) != set(branch_counts):
            raise ValueError(
                f"Inconsistent branch IDs in Istanbul/NYC report for {filename}."
            )

        if branch_map:
            found_branch_data = True

        for branch_id, branch_info in branch_map.items():
            if not isinstance(branch_info, dict):
                raise TypeError(f"Invalid branch metadata for {filename}.")

            locations = branch_info.get("locations")

            if not isinstance(locations, list):
                raise TypeError(f"Missing branch locations for {filename}.")

            counts = branch_counts[branch_id]

            if not isinstance(counts, list):
                raise TypeError(f"Invalid branch execution counts for {filename}.")

            if len(counts) != len(locations):
                raise ValueError(f"Inconsistent branch path counts for {filename}.")

            for count in counts:
                if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                    raise ValueError(f"Invalid branch execution count for {filename}.")

                valid_branches += 1
                covered_branches += count > 0

    if not found_branch_data or valid_branches == 0:
        return None

    return covered_branches, valid_branches
