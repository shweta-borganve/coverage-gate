import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from src.logger_config import configure_logger

logger = configure_logger(__name__)


@dataclass
class CoverageMetrics:
    total_coverage: float
    file_coverage: dict[str, float] = field(default_factory=dict)


def parse_cobertura(file_path: str) -> CoverageMetrics:
feature/lcov-only
    """Parse a Cobertura XML report into coverage metrics."""

    logger.info("Reading Cobertura coverage report: %s", file_path)

main
    try:
        tree = ET.parse(file_path)
    except FileNotFoundError:
        logger.error("Coverage file not found: %s", file_path)
        raise FileNotFoundError(f"Coverage file not found: {file_path}")
    except ET.ParseError as error:
        logger.error("Invalid coverage XML file: %s", file_path)
        raise ValueError(f"Invalid coverage XML file: {file_path}") from error

    logger.debug("Coverage XML parsed successfully: %s", file_path)

    root = tree.getroot()

    if root.tag != "coverage":
        logger.error("Unsupported coverage report root: %s", root.tag)
        raise ValueError(f"Unsupported coverage report root: {root.tag}")

    line_rate_text = root.get("line-rate")

    if line_rate_text is None:
        logger.error("Missing 'line-rate' in coverage XML file: %s", file_path)
        raise ValueError(f"Missing 'line-rate' in coverage XML file: {file_path}")

    try:
        line_rate = float(line_rate_text)
    except ValueError as error:
        logger.error("Invalid 'line-rate' value in coverage XML file: %s", file_path)
        raise ValueError(
            f"Invalid 'line-rate' value in coverage XML file: {file_path}"
        ) from error

    if not math.isfinite(line_rate) or not 0 <= line_rate <= 1:
        logger.error("Invalid line-rate range in coverage XML file: %s", file_path)
        raise ValueError(
            f"Invalid 'line-rate' value in coverage XML file: {file_path}. "
            "Expected a value between 0 and 1."
        )

    logger.debug("Validated overall line coverage rate: %s", line_rate)

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

    metrics = CoverageMetrics(
        total_coverage=line_rate * 100,
        file_coverage=file_coverage,
    )

    logger.info(
        "Coverage report processed: %.1f%% total coverage across %d files.",
        metrics.total_coverage,
        len(file_coverage),
    )

    return metrics


def parse_lcov(file_path: str, root_dir: str | Path | None = None) -> CoverageMetrics:
    """Parse an LCOV report into coverage metrics."""
    coverage_file = Path(file_path)

    try:
        content = coverage_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error("Coverage file not found: %s", file_path)
        raise FileNotFoundError(f"Coverage file not found: {file_path}")

    if not content.strip():
        raise ValueError("Empty LCOV coverage report.")

    total_found = 0
    total_hit = 0
    file_coverage: dict[str, float] = {}
    found_source = False
    found_line_data = False

    records = content.split("end_of_record")

    for index, record in enumerate(records):
        if not record.strip():
            continue

        if index == len(records) - 1 and not content.rstrip().endswith("end_of_record"):
            raise ValueError("Missing end_of_record in LCOV report.")

        source_file = None
        lines: dict[int, bool] = {}
        lines_found = None
        lines_hit = None

        for raw_line in record.splitlines():
            line = raw_line.strip()

            if line.startswith("SF:"):
                source_file = line[3:].strip()
                found_source = True

            elif line.startswith("DA:"):
                values = line[3:].split(",")

                if len(values) < 2:
                    raise ValueError("Invalid DA record in LCOV report.")

                try:
                    line_number = int(values[0])
                    hits = int(values[1])
                except ValueError as error:
                    raise ValueError(
                        "Invalid line number or hit count in LCOV report."
                    ) from error

                if line_number < 1 or hits < 0:
                    raise ValueError("Invalid DA record in LCOV report.")

                lines[line_number] = lines.get(line_number, False) or hits > 0

            elif line.startswith("LF:"):
                try:
                    lines_found = int(line[3:])
                except ValueError as error:
                    raise ValueError("Invalid LF value in LCOV report.") from error

            elif line.startswith("LH:"):
                try:
                    lines_hit = int(line[3:])
                except ValueError as error:
                    raise ValueError("Invalid LH value in LCOV report.") from error

        if source_file is None:
            continue

        if lines:
            record_found = len(lines)
            record_hit = sum(lines.values())

            if lines_found is not None and lines_found != record_found:
                raise ValueError(f"Invalid line coverage counts for {source_file}.")

            if lines_hit is not None and lines_hit != record_hit:
                raise ValueError(f"Invalid line coverage counts for {source_file}.")

        elif lines_found is not None and lines_hit is not None:
            record_found = lines_found
            record_hit = lines_hit

        else:
            continue

        if record_found < 0 or record_hit < 0 or record_hit > record_found:
            raise ValueError(f"Invalid line coverage counts for {source_file}.")

        found_line_data = found_line_data or record_found > 0

        total_found += record_found
        total_hit += record_hit

        if record_found:
            file_coverage[source_file] = record_hit / record_found * 100

    if not found_source:
        raise ValueError("Missing line coverage data in LCOV report.")

    if not found_line_data or total_found == 0:
        raise ValueError("Missing line coverage data in LCOV report.")

    total_coverage = total_hit / total_found * 100

    logger.info("LCOV coverage parsed successfully: %.2f%%", total_coverage)

    return CoverageMetrics(
        total_coverage=total_coverage,
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
feature/lcov-only
    """Parse LCOV line records keyed by their reported source filenames."""
    try:
        content = Path(file_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"Coverage file not found: {file_path}")

    if not content.strip():
        raise ValueError(f"Empty LCOV coverage report: {file_path}")

    file_lines: dict[str, dict[int, bool]] = {}
    current_filename: str | None = None
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

        elif line == "end_of_record":
            if current_filename is None:
                raise ValueError(
                    f"Unexpected end_of_record in LCOV report: {file_path}"
                )

            current_filename = None
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

    """Extract line-level coverage data from an LCOV report."""
    coverage_file = Path(file_path)

    try:
        content = coverage_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error("Coverage file not found: %s", file_path)
        raise FileNotFoundError(f"Coverage file not found: {file_path}")

    if not content.strip():
        raise ValueError("Empty LCOV coverage report.")

    file_lines: dict[str, dict[int, bool]] = {}
    records = content.split("end_of_record")

    for index, record in enumerate(records):
        if not record.strip():
            continue

        if index == len(records) - 1 and not content.rstrip().endswith("end_of_record"):
            raise ValueError("Missing end_of_record in LCOV report.")

        source_file = None
        lines: dict[int, bool] = {}

        for raw_line in record.splitlines():
            line = raw_line.strip()

            if line.startswith("SF:"):
                source_file = line[3:].strip()

            elif line.startswith("DA:"):
                values = line[3:].split(",")

                if len(values) < 2:
                    raise ValueError("Invalid DA record in LCOV report.")

                try:
                    line_number = int(values[0])
                    hits = int(values[1])
                except ValueError as error:
                    raise ValueError(
                        "Invalid line number or hit count in LCOV report."
                    ) from error

                if line_number < 1 or hits < 0:
                    raise ValueError("Invalid DA record in LCOV report.")

                lines[line_number] = lines.get(line_number, False) or hits > 0

        if source_file is not None:
            file_lines[source_file] = lines
main

    return file_lines


def _normalize_lcov_line_data(
feature/lcov-only
    file_lines: dict[str, dict[int, bool]],
    working_directory: Path,
) -> dict[str, dict[int, bool]]:
    """Normalize LCOV filenames and merge duplicate resolved source paths."""
    normalized_file_lines: dict[str, dict[int, bool]] = {}

    for filename, lines in file_lines.items():

    raw_file_lines: dict[str, dict[int, bool]],
    working_directory: Path,
) -> dict[str, dict[int, bool]]:
    """Normalize LCOV source filenames."""
    normalized_lines = {}

    for filename, lines in raw_file_lines.items():
main
        normalized_filename = _normalize_coverage_filename(
            filename,
            [],
            working_directory,
        )
 feature/lcov-only
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


        normalized_lines[normalized_filename] = lines

    return normalized_lines main


def parse_line_coverage(
    file_path: str,
    root_dir: str | Path | None = None,
) -> dict[str, dict[int, bool]]:
feature/lcov-only
    """Return line coverage keyed by normalized source filenames."""
    coverage_file = Path(file_path).resolve()
    working_directory = (
        Path(root_dir).resolve() if root_dir is not None else Path.cwd().resolve()
    )

    if coverage_file.suffix.lower() == ".info":
        raw_file_lines = _parse_lcov_line_data(str(coverage_file))
        return _normalize_lcov_line_data(raw_file_lines, working_directory)

    """Return line coverage keyed by repository-relative source filenames."""
feature/lcov-only
 main
    coverage_file = Path(file_path).resolve()
    working_directory = (
        Path(root_dir).resolve() if root_dir is not None else Path.cwd().resolve()
    )

    if coverage_file.suffix.lower() == ".info":
        raw_file_lines = _parse_lcov_line_data(str(coverage_file))
        return _normalize_lcov_line_data(raw_file_lines, working_directorymain

    try:
        tree = ET.parse(file_path)
    except FileNotFoundError:
        logger.error("Coverage file not found: %s", file_path)
        raise FileNotFoundError(f"Coverage file not found: {file_path}")
    except ET.ParseError as error:
        logger.error("Invalid coverage XML file: %s", file_path)
        raise ValueError(f"Invalid coverage XML file: {file_path}") from error

    logger.debug("Line coverage XML parsed successfully: %s", file_path)

    root = tree.getroot()

    if root.tag != "coverage":
        logger.error("Unsupported coverage report root: %s", root.tag)
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

    logger.debug("Found %d source paths in coverage report.", len(source_paths))

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
                logger.error(
                    "Missing line number or hits in coverage XML file: %s",
                    file_path,
                )
                raise ValueError(
                    f"Missing line number or hits in coverage XML file: {file_path}"
                )

            try:
                line_number = int(number_text)
                hits = int(hits_text)
            except ValueError as error:
                logger.error(
                    "Invalid line number or hits in coverage XML file: %s",
                    file_path,
                )
                raise ValueError(
                    f"Invalid line number or hits in coverage XML file: {file_path}"
                ) from error

            if line_number < 1 or hits < 0:
                logger.error(
                    "Invalid line number or hits in coverage XML file: %s",
                    file_path,
                )
                raise ValueError(
                    f"Invalid line number or hits in coverage XML file: {file_path}"
                )

            lines = file_lines.setdefault(normalized_filename, {})
            lines[line_number] = lines.get(line_number, False) or hits > 0

    logger.info(
        "Line coverage processed: %d source files found.",
        len(file_lines),
    )

    return file_lines
