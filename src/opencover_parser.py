import xml.etree.ElementTree as ET
from pathlib import Path


def _local_name(tag: str) -> str:
    """Return an XML tag name without its namespace."""
    return tag.rsplit("}", 1)[-1]


def _load_opencover_root(file_path: str) -> ET.Element:
    """Load and validate the root of an OpenCover XML report."""
    try:
        root = ET.parse(file_path).getroot()
    except FileNotFoundError:
        raise FileNotFoundError(f"Coverage file not found: {file_path}")
    except ET.ParseError as error:
        raise ValueError(f"Invalid coverage XML file: {file_path}") from error

    if _local_name(root.tag) != "CoverageSession":
        raise ValueError(f"Unsupported OpenCover XML root: {_local_name(root.tag)}")

    return root


def parse_opencover_xml(
    file_path: str,
) -> tuple[float, dict[str, dict[int, bool]]]:
    """Parse OpenCover XML and return overall and per-source-file line coverage."""
    root = _load_opencover_root(file_path)

    total_points = 0
    covered_points = 0
    file_lines: dict[str, dict[int, bool]] = {}
    found_modules = False

    for module in root.iter():
        if _local_name(module.tag) != "Module":
            continue

        found_modules = True
        files: dict[str, str] = {}

        for element in module.iter():
            if _local_name(element.tag) != "File":
                continue

            file_id = element.get("uid")
            full_path = element.get("fullPath")

            if file_id is None or not full_path:
                raise ValueError("Invalid file entry in OpenCover report.")

            if file_id in files and files[file_id] != full_path:
                raise ValueError(
                    f"Conflicting file paths for OpenCover file ID {file_id}."
                )

            files[file_id] = Path(full_path).as_posix()

        for element in module.iter():
            if _local_name(element.tag) != "SequencePoint":
                continue

            file_id = element.get("fileid")
            line_text = element.get("sl")
            visits_text = element.get("vc")

            if file_id is None or line_text is None or visits_text is None:
                raise ValueError("Missing sequence point data in OpenCover report.")

            if file_id not in files:
                raise ValueError(
                    f"Unknown file ID in OpenCover sequence point: {file_id}."
                )

            try:
                line_number = int(line_text)
                visits = int(visits_text)
            except ValueError as error:
                raise ValueError(
                    "Invalid sequence point data in OpenCover report."
                ) from error

            if line_number < 0 or visits < 0:
                raise ValueError("Invalid sequence point data in OpenCover report.")

            # OpenCover uses line zero for sequence points without source lines.
            if line_number == 0:
                continue

            filename = files[file_id]
            lines = file_lines.setdefault(filename, {})

            total_points += 1
            covered_points += visits > 0

            lines[line_number] = lines.get(line_number, False) or visits > 0

    if not found_modules:
        raise ValueError("Missing modules in OpenCover report.")

    total_lines = sum(len(lines) for lines in file_lines.values())
    covered_lines = sum(sum(lines.values()) for lines in file_lines.values())

    if total_lines == 0:
        raise ValueError("Missing sequence point coverage data in OpenCover report.")

    total_coverage = covered_lines / total_lines * 100

    return total_coverage, file_lines


def parse_opencover_branch_counts(file_path: str) -> tuple[int, int] | None:
    """Return covered and valid branch counts from OpenCover branch points."""
    root = _load_opencover_root(file_path)

    covered_branches = 0
    valid_branches = 0

    for module in root.iter():
        if _local_name(module.tag) != "Module":
            continue

        for element in module.iter():
            if _local_name(element.tag) != "BranchPoint":
                continue

            visits_text = element.get("vc")

            if visits_text is None:
                raise ValueError("Missing branch point data in OpenCover report.")

            try:
                visits = int(visits_text)
            except ValueError as error:
                raise ValueError(
                    "Invalid branch point data in OpenCover report."
                ) from error

            if visits < 0:
                raise ValueError("Invalid branch point data in OpenCover report.")

            valid_branches += 1
            covered_branches += visits > 0

    if valid_branches == 0:
        return None

    return covered_branches, valid_branches
