import xml.etree.ElementTree as ET
from pathlib import Path


def _load_jacoco_root(file_path: str) -> ET.Element:
    """Load and validate the root of a JaCoCo XML report."""
    try:
        root = ET.parse(file_path).getroot()
    except FileNotFoundError:
        raise FileNotFoundError(f"Coverage file not found: {file_path}")
    except ET.ParseError as error:
        raise ValueError(f"Invalid coverage XML file: {file_path}") from error

    if root.tag != "report":
        raise ValueError(f"Unsupported JaCoCo XML root: {root.tag}")

    return root


def parse_jacoco_xml(
    file_path: str,
) -> tuple[float, dict[str, dict[int, bool]]]:
    """Parse JaCoCo XML and return overall and per-source-file line coverage."""
    root = _load_jacoco_root(file_path)

    line_counters = [
        counter for counter in root.findall("counter") if counter.get("type") == "LINE"
    ]

    if len(line_counters) != 1:
        raise ValueError("JaCoCo report must contain exactly one LINE counter.")

    counter = line_counters[0]
    missed_text = counter.get("missed")
    covered_text = counter.get("covered")

    if missed_text is None or covered_text is None:
        raise ValueError("Missing LINE coverage counts in JaCoCo report.")

    try:
        missed = int(missed_text)
        covered = int(covered_text)
    except ValueError as error:
        raise ValueError("Invalid LINE coverage counts in JaCoCo report.") from error

    if missed < 0 or covered < 0 or missed + covered == 0:
        raise ValueError("Invalid or empty LINE coverage counts in JaCoCo report.")

    total_coverage = covered / (missed + covered) * 100
    file_lines: dict[str, dict[int, bool]] = {}

    for package in root.findall("package"):
        package_name = (package.get("name") or "").strip()

        for source_file in package.findall("sourcefile"):
            source_name = (source_file.get("name") or "").strip()

            if not source_name:
                raise ValueError("Missing source filename in JaCoCo report.")

            filename = f"{package_name}/{source_name}" if package_name else source_name
            lines = file_lines.setdefault(Path(filename).as_posix(), {})

            for line_element in source_file.findall("line"):
                number_text = line_element.get("nr")
                missed_instructions_text = line_element.get("mi")
                covered_instructions_text = line_element.get("ci")

                if (
                    number_text is None
                    or missed_instructions_text is None
                    or covered_instructions_text is None
                ):
                    raise ValueError("Missing line data in JaCoCo report.")

                try:
                    line_number = int(number_text)
                    missed_instructions = int(missed_instructions_text)
                    covered_instructions = int(covered_instructions_text)
                except ValueError as error:
                    raise ValueError("Invalid line data in JaCoCo report.") from error

                if (
                    line_number < 1
                    or missed_instructions < 0
                    or covered_instructions < 0
                ):
                    raise ValueError("Invalid line data in JaCoCo report.")

                lines[line_number] = (
                    lines.get(line_number, False) or covered_instructions > 0
                )

    if not file_lines:
        raise ValueError("Missing source-file line data in JaCoCo report.")

    return total_coverage, file_lines


def parse_jacoco_branch_counts(file_path: str) -> tuple[int, int] | None:
    """Return covered and valid branch counts when JaCoCo provides them."""
    root = _load_jacoco_root(file_path)

    branch_counters = [
        counter
        for counter in root.findall("counter")
        if counter.get("type") == "BRANCH"
    ]

    if not branch_counters:
        return None

    if len(branch_counters) != 1:
        raise ValueError("JaCoCo report must contain exactly one BRANCH counter.")

    counter = branch_counters[0]
    missed_text = counter.get("missed")
    covered_text = counter.get("covered")

    if missed_text is None or covered_text is None:
        raise ValueError("Missing BRANCH coverage counts in JaCoCo report.")

    try:
        missed = int(missed_text)
        covered = int(covered_text)
    except ValueError as error:
        raise ValueError("Invalid BRANCH coverage counts in JaCoCo report.") from error

    if missed < 0 or covered < 0:
        raise ValueError("Invalid BRANCH coverage counts in JaCoCo report.")

    valid = missed + covered

    if valid == 0:
        return None

    return covered, valid
