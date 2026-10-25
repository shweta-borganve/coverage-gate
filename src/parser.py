import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CoverageMetrics:
    total_coverage: float
    file_coverage: dict[str, float] = field(default_factory=dict)


def parse_cobertura(file_path: str) -> CoverageMetrics:
    """Parse a Cobertura XML report into coverage metrics."""
    try:
        tree = ET.parse(file_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Coverage file not found: {file_path}")
    except ET.ParseError as error:
        raise ValueError(f"Invalid coverage XML file: {file_path}") from error

    root = tree.getroot()

    if root.tag != "coverage":
        raise ValueError(f"Unsupported coverage report root: {root.tag}")

    line_rate_text = root.get("line-rate")

    if line_rate_text is None:
        raise ValueError(f"Missing 'line-rate' in coverage XML file: {file_path}")

    try:
        line_rate = float(line_rate_text)
    except ValueError as error:
        raise ValueError(
            f"Invalid 'line-rate' value in coverage XML file: {file_path}"
        ) from error

    if not math.isfinite(line_rate) or not 0 <= line_rate <= 1:
        raise ValueError(
            f"Invalid 'line-rate' value in coverage XML file: {file_path}. "
            "Expected a value between 0 and 1."
        )

    file_lines: dict[str, dict[int, bool]] = {}

    for class_element in root.iter("class"):
        filename = class_element.get("filename")

        if not filename:
            continue

        for line_element in class_element.findall("./lines/line"):
            number_text = line_element.get("number")
            hits_text = line_element.get("hits")

            if number_text is None or hits_text is None:
                continue

            try:
                line_number = int(number_text)
                hits = int(hits_text)
            except ValueError:
                continue

            if line_number < 1 or hits < 0:
                continue

            lines = file_lines.setdefault(filename, {})
            lines[line_number] = lines.get(line_number, False) or hits > 0

    file_coverage = {
        filename: sum(lines.values()) / len(lines) * 100
        for filename, lines in file_lines.items()
        if lines
    }

    return CoverageMetrics(
        total_coverage=line_rate * 100,
        file_coverage=file_coverage,
    )


def _normalize_coverage_filename(
    filename: str,
    source_paths: list[Path],
    working_directory: Path,
) -> str:
    """Normalize a coverage filename to a repository-relative path when possible."""
    file_path = Path(filename)

    if file_path.is_absolute():
        candidates = [file_path]
    else:
        candidates = [working_directory / file_path]
        candidates.extend(source / file_path for source in source_paths)

    for candidate in candidates:
        resolved = candidate.resolve()

        try:
            relative_path = resolved.relative_to(working_directory)
        except ValueError:
            continue

        if relative_path.is_file():
            return relative_path.as_posix()

    # Preserve unresolved paths instead of guessing their location.
    return file_path.as_posix()


def _parse_lcov_line_data(file_path: str) -> dict[str, dict[int, bool]]:
    """Parse LCOV line records keyed by their reported source filenames."""
    try:
        content = Path(file_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"Coverage file not found: {file_path}")

    if not content.strip():
        raise ValueError(f"Empty LCOV coverage report: {file_path}")

    file_lines: dict[str, dict[int, bool]] = {}
    current_filename: str | None = None
    current_record_has_lines = False
    completed_record = False

    for raw_line in content.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("SF:"):
            if current_filename is not None:
                raise ValueError(
                    f"Missing end_of_record before next source file: {file_path}"
                )

            current_filename = line[3:].strip()

            if not current_filename:
                raise ValueError(f"Missing source filename in LCOV report: {file_path}")

            file_lines.setdefault(current_filename, {})
            current_record_has_lines = False

        elif line.startswith("DA:"):
            if current_filename is None:
                raise ValueError(
                    "Line data found before source filename in LCOV report: "
                    f"{file_path}"
                )

            values = line[3:].split(",")

            if len(values) < 2:
                raise ValueError(f"Invalid DA record in LCOV report: {line}")

            try:
                line_number = int(values[0])
                hits = int(values[1])
            except ValueError as error:
                raise ValueError(
                    f"Invalid line number or hit count in LCOV report: {line}"
                ) from error

            if line_number < 1 or hits < 0:
                raise ValueError(f"Invalid DA record in LCOV report: {line}")

            lines = file_lines[current_filename]
            lines[line_number] = lines.get(line_number, False) or hits > 0
            current_record_has_lines = True

        elif line == "end_of_record":
            if current_filename is None or not current_record_has_lines:
                raise ValueError(
                    "Missing source filename or line data in LCOV report: "
                    f"{file_path}"
                )

            current_filename = None
            current_record_has_lines = False
            completed_record = True

        elif line.startswith(
            (
                "TN:",
                "FN:",
                "FNDA:",
                "FNF:",
                "FNH:",
                "BRDA:",
                "BRF:",
                "BRH:",
                "LF:",
                "LH:",
                "VER:",
            )
        ):
            # These LCOV records are not needed for line coverage.
            continue

        else:
            raise ValueError(f"Invalid LCOV record in report: {line}")

    if current_filename is not None:
        raise ValueError(f"Missing end_of_record in LCOV report: {file_path}")

    if not completed_record or not any(file_lines.values()):
        raise ValueError(f"Missing line coverage data in LCOV report: {file_path}")

    return file_lines


def _normalize_lcov_line_data(
    file_lines: dict[str, dict[int, bool]],
    working_directory: Path,
) -> dict[str, dict[int, bool]]:
    """Normalize LCOV filenames and merge duplicate resolved source paths."""
    normalized_file_lines: dict[str, dict[int, bool]] = {}

    for filename, lines in file_lines.items():
        normalized_filename = _normalize_coverage_filename(
            filename,
            [],
            working_directory,
        )
        normalized_lines = normalized_file_lines.setdefault(
            normalized_filename,
            {},
        )

        for line_number, covered in lines.items():
            normalized_lines[line_number] = (
                normalized_lines.get(line_number, False) or covered
            )

    return normalized_file_lines


def parse_lcov(
    file_path: str,
    root_dir: str | Path | None = None,
) -> CoverageMetrics:
    """Parse an LCOV report, resolving source paths against the repository root."""
    working_directory = (
        Path(root_dir).resolve() if root_dir is not None else Path.cwd().resolve()
    )
    raw_file_lines = _parse_lcov_line_data(file_path)
    normalized_file_lines = _normalize_lcov_line_data(
        raw_file_lines,
        working_directory,
    )

    total_lines = sum(len(lines) for lines in normalized_file_lines.values())
    covered_lines = sum(sum(lines.values()) for lines in normalized_file_lines.values())

    if total_lines == 0:
        raise ValueError(f"Missing line coverage data in LCOV report: {file_path}")

    file_coverage = {
        filename: sum(lines.values()) / len(lines) * 100
        for filename, lines in normalized_file_lines.items()
        if lines
    }

    return CoverageMetrics(
        total_coverage=covered_lines / total_lines * 100,
        file_coverage=file_coverage,
    )


def parse_coverage_report(
    file_path: str,
    root_dir: str | Path | None = None,
) -> CoverageMetrics:
    """Select a coverage parser based on the report extension."""
    file_extension = Path(file_path).suffix.lower()

    if file_extension == ".xml":
        return parse_cobertura(file_path)

    if file_extension == ".info":
        return parse_lcov(file_path, root_dir=root_dir)

    raise ValueError(
        f"Unsupported coverage report format: "
        f"{file_extension or 'no extension'}. "
        "Supported formats: .xml (Cobertura), .info (LCOV)."
    )


def parse_line_coverage(
    file_path: str,
    root_dir: str | Path | None = None,
) -> dict[str, dict[int, bool]]:
    """Return line coverage keyed by normalized source filenames."""
    coverage_file = Path(file_path).resolve()
    working_directory = (
        Path(root_dir).resolve() if root_dir is not None else Path.cwd().resolve()
    )

    if coverage_file.suffix.lower() == ".info":
        raw_file_lines = _parse_lcov_line_data(str(coverage_file))
        return _normalize_lcov_line_data(raw_file_lines, working_directory)

    try:
        tree = ET.parse(file_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Coverage file not found: {file_path}")
    except ET.ParseError as error:
        raise ValueError(f"Invalid coverage XML file: {file_path}") from error

    root = tree.getroot()

    if root.tag != "coverage":
        raise ValueError(f"Unsupported coverage report root: {root.tag}")

    source_paths = []
    sources_element = root.find("sources")

    if sources_element is not None:
        for source_element in sources_element.findall("source"):
            source_text = (source_element.text or "").strip()

            if not source_text:
                continue

            source_path = Path(source_text)

            if not source_path.is_absolute():
                source_path = coverage_file.parent / source_path

            source_paths.append(source_path.resolve())

    file_lines: dict[str, dict[int, bool]] = {}

    for class_element in root.iter("class"):
        filename = class_element.get("filename")

        if not filename:
            continue

        normalized_filename = _normalize_coverage_filename(
            filename,
            source_paths,
            working_directory,
        )

        for line_element in class_element.findall("./lines/line"):
            number_text = line_element.get("number")
            hits_text = line_element.get("hits")

            if number_text is None or hits_text is None:
                raise ValueError(
                    f"Missing line number or hits in coverage XML file: {file_path}"
                )

            try:
                line_number = int(number_text)
                hits = int(hits_text)
            except ValueError as error:
                raise ValueError(
                    f"Invalid line number or hits in coverage XML file: {file_path}"
                ) from error

            if line_number < 1 or hits < 0:
                raise ValueError(
                    f"Invalid line number or hits in coverage XML file: {file_path}"
                )

            lines = file_lines.setdefault(normalized_filename, {})
            lines[line_number] = lines.get(line_number, False) or hits > 0

    return file_lines
