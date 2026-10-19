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


def _normalize_coverage_filename(
    filename: str,
    source_paths: list[Path],
    working_directory: Path,
) -> str:
    """Normalize a Cobertura filename to a repository-relative path when possible."""
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

    # Preserve the original filename if it cannot be resolved inside the
    # working directory. This avoids guessing paths for external sources.
    return file_path.as_posix()


def parse_line_coverage(
    file_path: str,
    root_dir: str | Path | None = None,
) -> dict[str, dict[int, bool]]:
    """Return line coverage keyed by repository-relative source filenames."""
    logger.info("Reading line coverage report: %s", file_path)

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

    coverage_file = Path(file_path).resolve()
    working_directory = (
        Path(root_dir).resolve() if root_dir is not None else Path.cwd().resolve()
    )

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
