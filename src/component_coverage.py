"""Component-specific coverage threshold configuration and evaluation."""

import json
import math
from dataclasses import dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True)
class ComponentThreshold:
    """A coverage threshold configured for a file or directory."""

    path: str
    threshold: float
    is_directory: bool


@dataclass
class ComponentCoverageResult:
    """Coverage evaluation result for one configured component."""

    component: str
    coverage: float | None
    threshold: float
    passed: bool
    total_lines: int
    covered_lines: int
    files: list[str]
    message: str


def _normalize_component_path(path: str) -> tuple[str, bool]:
    """Normalize a repository-relative component path."""
    if not isinstance(path, str) or not path.strip():
        raise ValueError("Component paths must be non-empty strings.")

    path = path.strip().replace("\\", "/")
    is_directory = path.endswith("/")

    if path.startswith("/"):
        raise ValueError(f"Component path must be repository-relative: {path}")

    if path.endswith("//"):
        raise ValueError(f"Invalid component path: {path}")

    normalized_input = path[:-1] if is_directory else path
    parts = normalized_input.split("/")

    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(
            f"Invalid component path: {path}. "
            "Empty, '.' and '..' path segments are not allowed."
        )

    return str(PurePosixPath(normalized_input)), is_directory


def parse_component_thresholds(
    configuration: str,
) -> list[ComponentThreshold]:
    """Parse and validate JSON component-threshold configuration."""
    if not configuration or not configuration.strip():
        return []

    try:
        data = json.loads(configuration)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid component-thresholds JSON: {error.msg}.") from error

    if not isinstance(data, dict):
        raise ValueError(  # noqa: TRY004
            "component-thresholds must be a JSON object mapping paths to percentages."
        )

    if not data:
        raise ValueError(
            "component-thresholds must contain at least one component rule."
        )

    thresholds = []
    seen_paths = set()

    for configured_path, configured_threshold in data.items():
        normalized_path, is_directory = _normalize_component_path(configured_path)

        if normalized_path in seen_paths:
            raise ValueError(
                f"Duplicate component path after normalization: {normalized_path}"
            )

        if isinstance(configured_threshold, bool) or not isinstance(
            configured_threshold, (int, float)
        ):
            raise ValueError(  # noqa: TRY004
                f"Threshold for component '{configured_path}' must be a number."
            )

        threshold = float(configured_threshold)

        if not math.isfinite(threshold) or not 0 <= threshold <= 100:
            raise ValueError(
                f"Threshold for component '{configured_path}' "
                "must be between 0 and 100."
            )

        seen_paths.add(normalized_path)
        thresholds.append(
            ComponentThreshold(
                path=normalized_path,
                threshold=threshold,
                is_directory=is_directory,
            )
        )

    return thresholds


def _matching_component(
    filename: str,
    thresholds: list[ComponentThreshold],
) -> ComponentThreshold | None:
    """Find the most specific component rule matching a repository file."""
    normalized_filename = filename.replace("\\", "/")

    while normalized_filename.startswith("./"):
        normalized_filename = normalized_filename[2:]

    matches = []

    for component in thresholds:
        if component.is_directory:
            prefix = component.path + "/"

            if normalized_filename.startswith(prefix):
                matches.append(component)
        elif normalized_filename == component.path:
            matches.append(component)

    if not matches:
        return None

    return max(
        matches,
        key=lambda component: (
            len(component.path),
            not component.is_directory,
        ),
    )


def evaluate_component_coverage(
    line_coverage: dict[str, dict[int, bool]],
    thresholds: list[ComponentThreshold],
) -> list[ComponentCoverageResult]:
    """Evaluate configured components using executable-line coverage."""
    component_lines = {component.path: {} for component in thresholds}

    for filename, lines in line_coverage.items():
        component = _matching_component(filename, thresholds)

        if component is None:
            continue

        component_file_lines = component_lines[component.path]
        component_file_lines[filename] = lines

    results = []

    for component in thresholds:
        matched_files = component_lines[component.path]
        total_lines = sum(len(lines) for lines in matched_files.values())
        covered_lines = sum(sum(lines.values()) for lines in matched_files.values())

        if total_lines == 0:
            results.append(
                ComponentCoverageResult(
                    component=component.path,
                    coverage=None,
                    threshold=component.threshold,
                    passed=False,
                    total_lines=0,
                    covered_lines=0,
                    files=[],
                    message=(
                        f"No executable coverage lines matched component "
                        f"'{component.path}'."
                    ),
                )
            )
            continue

        coverage = covered_lines / total_lines * 100
        passed = coverage >= component.threshold
        status = "PASS" if passed else "FAIL"

        results.append(
            ComponentCoverageResult(
                component=component.path,
                coverage=coverage,
                threshold=component.threshold,
                passed=passed,
                total_lines=total_lines,
                covered_lines=covered_lines,
                files=sorted(matched_files),
                message=(
                    f"Component '{component.path}': "
                    f"{coverage:.1f}% vs threshold "
                    f"{component.threshold:.1f}% — {status}"
                ),
            )
        )

    return results
