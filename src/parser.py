import json
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.go_parser import parse_go_coverprofile
from src.istanbul_parser import parse_istanbul_json
from src.jacoco_parser import parse_jacoco_xml
from src.logger_config import configure_logger
from src.opencover_parser import parse_opencover_xml

logger = configure_logger(__name__)


@dataclass
class CoverageMetrics:
    total_coverage: float
    file_coverage: dict[str, float] = field(default_factory=dict)
    covered_branches: int | None = None
    valid_branches: int | None = None

    @property
    def branch_coverage(self) -> float | None:
        if self.covered_branches is None or self.valid_branches is None:
            return None

        if self.valid_branches == 0:
            return None

        return self.covered_branches / self.valid_branches * 100


def parse_cobertura(file_path: str) -> CoverageMetrics:
    logger.info("Reading Cobertura coverage report: %s", file_path)

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

    file_lines: dict[str, dict[int, bool]] = {}
    fallback_counts: dict[str, tuple[int, int]] = {}
    detailed_sources: set[str] = set()
    summary_only_sources: set[str] = set()
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
            if source_file in summary_only_sources:
                raise ValueError(
                    f"Ambiguous LCOV records for {source_file}: "
                    "detailed and summary-only records cannot be combined."
                )

            detailed_sources.add(source_file)
            record_found = len(lines)
            record_hit = sum(lines.values())

            if lines_found is not None and lines_found != record_found:
                raise ValueError(f"Invalid line coverage counts for {source_file}.")

            if lines_hit is not None and lines_hit != record_hit:
                raise ValueError(f"Invalid line coverage counts for {source_file}.")

        elif lines_found is not None and lines_hit is not None:
            if source_file in detailed_sources or source_file in summary_only_sources:
                raise ValueError(
                    f"Ambiguous LCOV records for {source_file}: "
                    "repeated summary-only records cannot be merged."
                )

            summary_only_sources.add(source_file)
            record_found = lines_found
            record_hit = lines_hit

        else:
            continue

        if record_found < 0 or record_hit < 0 or record_hit > record_found:
            raise ValueError(f"Invalid line coverage counts for {source_file}.")

        found_line_data = found_line_data or record_found > 0

        if lines:
            merged_lines = file_lines.setdefault(source_file, {})

            for line_number, covered in lines.items():
                merged_lines[line_number] = (
                    merged_lines.get(line_number, False) or covered
                )
        else:
            fallback_counts[source_file] = (record_found, record_hit)

    if not found_source:
        raise ValueError("Missing line coverage data in LCOV report.")

    if not found_line_data:
        raise ValueError("Missing line coverage data in LCOV report.")

    file_coverage: dict[str, float] = {}
    total_found = 0
    total_hit = 0

    for source_file in set(file_lines) | set(fallback_counts):
        merged_lines = file_lines.get(source_file, {})
        fallback_found, fallback_hit = fallback_counts.get(
            source_file,
            (0, 0),
        )

        record_found = len(merged_lines) + fallback_found
        record_hit = sum(merged_lines.values()) + fallback_hit

        if record_found == 0:
            continue

        total_found += record_found
        total_hit += record_hit
        file_coverage[source_file] = record_hit / record_found * 100

    if total_found == 0:
        raise ValueError("Missing line coverage data in LCOV report.")

    total_coverage = total_hit / total_found * 100

    logger.info("LCOV coverage parsed successfully: %.2f%%", total_coverage)

    return CoverageMetrics(
        total_coverage=total_coverage,
        file_coverage=file_coverage,
    )


def _load_coverage_json(file_path: str) -> dict[str, Any]:
    """Load and validate the top-level structure of a coverage.py JSON report."""
    try:
        content = Path(file_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error("Coverage file not found: %s", file_path)
        raise FileNotFoundError(f"Coverage file not found: {file_path}")

    if not content.strip():
        raise ValueError("Empty coverage JSON report.")

    try:
        report = json.loads(content)
    except json.JSONDecodeError as error:
        logger.error("Invalid coverage JSON report: %s", file_path)
        raise ValueError(f"Invalid coverage JSON report: {file_path}") from error

    if not isinstance(report, dict):
        raise TypeError("Invalid coverage JSON report: expected a JSON object.")

    totals = report.get("totals")
    files = report.get("files")

    if not isinstance(totals, dict):
        raise TypeError("Invalid coverage JSON report: missing totals object.")

    if not isinstance(files, dict) or not files:
        raise ValueError("Invalid coverage JSON report: missing files object.")

    return report


def _validate_json_count(value: Any, field_name: str) -> int:
    """Validate a non-negative integer count in a coverage JSON report."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(
            f"Invalid coverage JSON report: '{field_name}' must be "
            "a non-negative integer."
        )

    return value


def _parse_json_line_data(
    report: dict[str, Any],
) -> dict[str, dict[int, bool]]:
    """Extract executed and missing lines from coverage.py JSON data."""
    files = report["files"]
    file_lines: dict[str, dict[int, bool]] = {}

    for filename, file_data in files.items():
        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("Invalid coverage JSON report: invalid filename.")

        if not isinstance(file_data, dict):
            raise TypeError(
                f"Invalid coverage JSON report: invalid file data for {filename}."
            )

        executed_lines = file_data.get("executed_lines")
        missing_lines = file_data.get("missing_lines")

        if not isinstance(executed_lines, list) or not isinstance(missing_lines, list):
            raise TypeError(
                f"Invalid coverage JSON report: missing line data for {filename}."
            )

        lines: dict[int, bool] = {}

        for line_number in executed_lines:
            if (
                isinstance(line_number, bool)
                or not isinstance(line_number, int)
                or line_number < 1
                or line_number in lines
            ):
                raise ValueError(f"Invalid executed line data for {filename}.")

            lines[line_number] = True

        for line_number in missing_lines:
            if (
                isinstance(line_number, bool)
                or not isinstance(line_number, int)
                or line_number < 1
                or line_number in lines
            ):
                raise ValueError(f"Invalid missing line data for {filename}.")

            lines[line_number] = False

        summary = file_data.get("summary")

        if not isinstance(summary, dict):
            raise TypeError(
                f"Invalid coverage JSON report: missing summary for {filename}."
            )

        covered = _validate_json_count(
            summary.get("covered_lines"),
            f"{filename}.summary.covered_lines",
        )
        statements = _validate_json_count(
            summary.get("num_statements"),
            f"{filename}.summary.num_statements",
        )

        if covered > statements:
            raise ValueError(f"Invalid line coverage counts for {filename}.")

        if len(lines) != statements or sum(lines.values()) != covered:
            raise ValueError(f"Inconsistent line coverage data for {filename}.")

        file_lines[filename] = lines

    if not any(file_lines.values()):
        raise ValueError("Missing line coverage data in JSON report.")

    return file_lines


def parse_coverage_json(file_path: str) -> CoverageMetrics:
    """Parse a coverage.py JSON report into line coverage metrics."""
    logger.info("Reading coverage.py JSON report: %s", file_path)

    report = _load_coverage_json(file_path)
    totals = report["totals"]

    covered_lines = _validate_json_count(
        totals.get("covered_lines"),
        "totals.covered_lines",
    )
    num_statements = _validate_json_count(
        totals.get("num_statements"),
        "totals.num_statements",
    )

    if num_statements == 0 or covered_lines > num_statements:
        raise ValueError("Invalid total line coverage counts in JSON report.")

    raw_file_lines = _parse_json_line_data(report)

    file_covered_lines = sum(sum(lines.values()) for lines in raw_file_lines.values())
    file_num_statements = sum(len(lines) for lines in raw_file_lines.values())

    if file_covered_lines != covered_lines or file_num_statements != num_statements:
        raise ValueError("Inconsistent total coverage counts in JSON report.")

    file_coverage = {}

    for filename, lines in raw_file_lines.items():
        if lines:
            file_coverage[filename] = sum(lines.values()) / len(lines) * 100

    total_coverage = covered_lines / num_statements * 100

    logger.info(
        "Coverage JSON processed: %.1f%% total coverage across %d files.",
        total_coverage,
        len(file_coverage),
    )

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
    normalized_name = filename.replace("\\", "/")
    file_path = Path(normalized_name)

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

        if resolved.is_file():
            return relative_path.as_posix()

    if not file_path.is_absolute():
        reported_parts = file_path.parts
        ignored = {".git", ".venv", "venv", "node_modules", "__pycache__"}
        matches = []

        for candidate in working_directory.rglob(file_path.name):
            if not candidate.is_file():
                continue

            relative_parts = candidate.relative_to(working_directory).parts

            if ignored.intersection(relative_parts):
                continue

            if (
                len(relative_parts) >= len(reported_parts)
                and relative_parts[-len(reported_parts) :] == reported_parts
            ) or (
                len(reported_parts) >= len(relative_parts)
                and reported_parts[-len(relative_parts) :] == relative_parts
            ):
                matches.append(candidate)

        if len(matches) == 1:
            return matches[0].relative_to(working_directory).as_posix()

        if len(matches) > 1:
            logger.warning(
                "Ambiguous coverage source path '%s'; preserving the reported path.",
                filename,
            )

    return file_path.as_posix()


def _parse_lcov_line_data(file_path: str) -> dict[str, dict[int, bool]]:
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
            merged_lines = file_lines.setdefault(source_file, {})

            for line_number, covered in lines.items():
                merged_lines[line_number] = (
                    merged_lines.get(line_number, False) or covered
                )

    return file_lines


def _normalize_lcov_line_data(
    raw_file_lines: dict[str, dict[int, bool]],
    working_directory: Path,
) -> dict[str, dict[int, bool]]:
    """Normalize LCOV filenames and reject duplicate normalized paths."""
    normalized_lines = {}

    for filename, lines in raw_file_lines.items():
        normalized_filename = _normalize_coverage_filename(
            filename,
            [],
            working_directory,
        )

        if normalized_filename in normalized_lines:
            raise ValueError(
                "Duplicate normalized filename in LCOV report: "
                f"{normalized_filename}"
            )

        normalized_lines[normalized_filename] = lines

    return normalized_lines


def _normalize_json_line_data(
    raw_file_lines: dict[str, dict[int, bool]],
    working_directory: Path,
) -> dict[str, dict[int, bool]]:
    """Normalize JSON filenames and reject paths that collide after normalization."""
    normalized_lines = {}

    for filename, lines in raw_file_lines.items():
        normalized_filename = _normalize_coverage_filename(
            filename,
            [],
            working_directory,
        )

        if normalized_filename in normalized_lines:
            raise ValueError(
                "Duplicate normalized filename in coverage JSON report: "
                f"{normalized_filename}"
            )

        normalized_lines[normalized_filename] = lines

    return normalized_lines


def _normalize_go_line_data(
    raw_file_lines: dict[str, dict[int, bool]],
    working_directory: Path,
) -> dict[str, dict[int, bool]]:
    """Normalize Go source filenames and reject paths that collide."""
    normalized_lines = {}

    for filename, lines in raw_file_lines.items():
        normalized_filename = _normalize_coverage_filename(
            filename,
            [],
            working_directory,
        )

        if normalized_filename in normalized_lines:
            raise ValueError(
                "Duplicate normalized filename in Go coverage report: "
                f"{normalized_filename}"
            )

        normalized_lines[normalized_filename] = lines

    return normalized_lines


def _normalize_opencover_line_data(
    raw_file_lines: dict[str, dict[int, bool]],
    working_directory: Path,
) -> dict[str, dict[int, bool]]:
    """Normalize OpenCover filenames and reject paths that collide."""
    normalized_lines = {}

    for filename, lines in raw_file_lines.items():
        normalized_filename = _normalize_coverage_filename(
            filename,
            [],
            working_directory,
        )

        if normalized_filename in normalized_lines:
            raise ValueError(
                "Duplicate normalized filename in OpenCover report: "
                f"{normalized_filename}"
            )

        normalized_lines[normalized_filename] = lines

    return normalized_lines


def parse_line_coverage(
    file_path: str,
    root_dir: str | Path | None = None,
) -> dict[str, dict[int, bool]]:
    """Return line coverage keyed by repository-relative source filenames."""
    coverage_file = Path(file_path).resolve()
    working_directory = (
        Path(root_dir).resolve() if root_dir is not None else Path.cwd().resolve()
    )

    if coverage_file.suffix.lower() in {".out", ".coverprofile"}:
        go_report = parse_go_coverprofile(str(coverage_file))

        return _normalize_go_line_data(
            go_report.line_coverage,
            working_directory,
        )

    if coverage_file.suffix.lower() == ".info":
        raw_file_lines = _parse_lcov_line_data(str(coverage_file))
        return _normalize_lcov_line_data(raw_file_lines, working_directory)

    if coverage_file.suffix.lower() == ".json":
        try:
            json_report = json.loads(coverage_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            json_report = None

        is_istanbul = isinstance(json_report, dict) and any(
            isinstance(file_data, dict)
            and ("statementMap" in file_data or "s" in file_data)
            for file_data in json_report.values()
        )

        if is_istanbul:
            logger.debug("Detected Istanbul/NYC JSON for changed-line coverage.")
            _, raw_file_lines = parse_istanbul_json(str(coverage_file))

            return _normalize_json_line_data(
                raw_file_lines,
                working_directory,
            )

        report = _load_coverage_json(str(coverage_file))
        raw_file_lines = _parse_json_line_data(report)

        return _normalize_json_line_data(raw_file_lines, working_directory)

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

    if root.tag == "CoverageSession":
        logger.debug("Detected OpenCover XML for changed-line coverage.")

        _, opencover_file_lines = parse_opencover_xml(str(coverage_file))

        normalized_lines = _normalize_opencover_line_data(
            opencover_file_lines,
            working_directory,
        )

        logger.info(
            "OpenCover line coverage processed: %d source files found.",
            len(normalized_lines),
        )

        return normalized_lines

    if root.tag == "report":
        logger.debug("Detected JaCoCo XML for changed-line coverage.")

        _, jacoco_file_lines = parse_jacoco_xml(str(coverage_file))

        normalized_lines = {}

        for filename, lines in jacoco_file_lines.items():
            normalized_filename = _normalize_coverage_filename(
                filename,
                [],
                working_directory,
            )

            if normalized_filename in normalized_lines:
                raise ValueError(
                    "Duplicate normalized filename in JaCoCo report: "
                    f"{normalized_filename}"
                )

            normalized_lines[normalized_filename] = lines

        logger.info(
            "JaCoCo line coverage processed: %d source files found.",
            len(normalized_lines),
        )

        return normalized_lines

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
