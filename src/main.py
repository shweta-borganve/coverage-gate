import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from src.badge import generate_badge
from src.changed_coverage import (
    ChangedCoverageReport,
    generate_changed_coverage_report,
)
from src.changed_lines import parse_changed_lines
from src.component_coverage import (
    evaluate_component_coverage,
    parse_component_thresholds,
)
from src.coverage_trend import (
    create_history_record,
    get_coverage_trend,
    write_history_record,
)
from src.enforcer import (
    ChangedCoverageEnforcementResult,
    enforce,
    enforce_changed_coverage,
)
from src.go_parser import parse_go_coverprofile
from src.istanbul_adapter import parse_istanbul
from src.jacoco_adapter import parse_jacoco
from src.logger_config import configure_logger
from src.opencover_adapter import parse_opencover
from src.parser import (
    CoverageMetrics,
    parse_cobertura,
    parse_coverage_json,
    parse_lcov,
    parse_line_coverage,
)
from src.pr_comment import publish_pr_comment
from src.report_merger import (
    calculate_coverage_metrics,
    merge_line_coverage,
)
from src.summary import generate_summary

logger = configure_logger(__name__)


def _parse_coverage_report(file_path: str):
    """Parse a supported coverage report based on its format."""
    extension = Path(file_path).suffix.lower()

    if extension == ".json":
        try:
            with open(file_path, encoding="utf-8") as coverage_file:
                json_report = json.load(coverage_file)
        except (OSError, json.JSONDecodeError):
            json_report = None

        is_istanbul = isinstance(json_report, dict) and any(
            isinstance(file_data, dict)
            and ("statementMap" in file_data or "s" in file_data)
            for file_data in json_report.values()
        )

        if is_istanbul:
            logger.debug("[Coverage Gate] Detected Istanbul/NYC JSON report.")
            return parse_istanbul(file_path)

        logger.debug("[Coverage Gate] Detected coverage.py JSON report.")
        return parse_coverage_json(file_path)

    if extension == ".info":
        logger.debug("[Coverage Gate] Detected LCOV coverage report.")
        return parse_lcov(file_path)

    if extension in {".out", ".coverprofile"}:
        logger.debug("[Coverage Gate] Detected Go coverprofile report.")
        go_report = parse_go_coverprofile(file_path)

        return CoverageMetrics(
            total_coverage=go_report.total_coverage,
            file_coverage=go_report.file_coverage,
        )

    try:
        root = ET.parse(file_path).getroot()
    except ET.ParseError as error:
        raise ValueError(f"Invalid coverage XML file: {file_path}") from error

    root_name = root.tag.rsplit("}", 1)[-1]

    if root_name == "coverage":
        logger.debug("[Coverage Gate] Detected Cobertura XML coverage report.")
        return parse_cobertura(file_path)

    if root_name == "report":
        logger.debug("[Coverage Gate] Detected JaCoCo XML coverage report.")
        return parse_jacoco(file_path)

    if root_name == "CoverageSession":
        logger.debug("[Coverage Gate] Detected OpenCover XML coverage report.")
        return parse_opencover(file_path)

    raise ValueError(f"Unsupported coverage XML root element: {root_name}")


def _resolve_coverage_file(workspace: str, configured_path: str) -> str:
    """Resolve a coverage report path and ensure it stays inside the workspace."""
    workspace_path = Path(workspace).resolve()
    coverage_path = (workspace_path / configured_path).resolve()

    try:
        coverage_path.relative_to(workspace_path)
    except ValueError as error:
        raise ValueError(
            "Coverage report must be located inside GITHUB_WORKSPACE."
        ) from error

    return str(coverage_path)


def _split_coverage_files(configured_paths: str) -> list[str]:
    """Split comma-separated coverage report paths and validate the list."""
    paths = [item.strip() for item in configured_paths.split(",")]

    if not paths or any(not item for item in paths):
        raise ValueError(
            "COVERAGE_FILE must contain one or more non-empty report paths."
        )

    return paths


def _resolve_coverage_files(
    workspace: str,
    configured_paths: str,
) -> list[str]:
    """Resolve every report path inside the GitHub workspace."""
    return [
        _resolve_coverage_file(workspace, configured_path)
        for configured_path in _split_coverage_files(configured_paths)
    ]


def _coverage_badge_enabled() -> bool:
    """Return whether optional SVG coverage badge generation is enabled."""
    value = os.environ.get("ENABLE_COVERAGE_BADGE", "false").strip().lower()
    return value in {"true", "1", "yes"}


def _resolve_badge_output_path(workspace: str, configured_path: str) -> Path:
    """Resolve a badge output path and ensure it stays inside the workspace."""
    workspace_path = Path(workspace).resolve()
    badge_path = (workspace_path / configured_path).resolve()

    try:
        badge_path.relative_to(workspace_path)
    except ValueError as error:
        raise ValueError(
            "Coverage badge output must be located inside GITHUB_WORKSPACE."
        ) from error

    if badge_path == workspace_path:
        raise ValueError(
            "Coverage badge output must be a file inside GITHUB_WORKSPACE."
        )

    return badge_path


def _coverage_trend_enabled() -> bool:
    """Return whether optional coverage trend tracking is enabled."""
    value = os.environ.get("ENABLE_COVERAGE_TREND", "false").strip().lower()
    return value in {"true", "1", "yes"}


def _process_coverage_trend(current_coverage: float):
    """Retrieve previous coverage and write the current history record.

    Trend tracking is optional. Errors in this feature must never affect
    the coverage enforcement result.
    """
    branch = (
        os.environ.get("COVERAGE_HISTORY_BRANCH")
        or os.environ.get("GITHUB_HEAD_REF")
        or os.environ.get("GITHUB_REF_NAME", "")
    )
    commit_sha = (
        os.environ.get("COVERAGE_HISTORY_COMMIT_SHA")
        or os.environ.get("GITHUB_HEAD_SHA")
        or os.environ.get("GITHUB_SHA", "")
    )
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_number_text = os.environ.get("GITHUB_RUN_NUMBER", "")
    workflow_ref = os.environ.get("GITHUB_WORKFLOW_REF", "")
    token = os.environ.get("HISTORY_TOKEN", "")
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")

    trend_data = get_coverage_trend(
        token=token,
        repository=repository,
        branch=branch,
        commit_sha=commit_sha,
        current_run_id=run_id,
        workflow_ref=workflow_ref,
        current_coverage=current_coverage,
        api_url=api_url,
    )

    output_path = os.environ.get("HISTORY_OUTPUT_PATH", "")

    if not output_path:
        logger.warning(
            "[Coverage Gate] Coverage history record not written: "
            "history output path is unavailable."
        )
        return trend_data

    try:
        if not all(
            (
                branch,
                commit_sha,
                run_id,
                run_number_text,
                workflow_ref,
            )
        ):
            logger.warning(
                "[Coverage Gate] Coverage history record not written: "
                "required GitHub run metadata is unavailable."
            )
            return trend_data

        record = create_history_record(
            coverage=current_coverage,
            branch=branch,
            commit_sha=commit_sha,
            run_id=run_id,
            run_number=int(run_number_text),
            workflow_ref=workflow_ref,
        )

        write_history_record(record, output_path)

    except (OSError, ValueError, TypeError, KeyError) as error:
        logger.warning(
            "[Coverage Gate] WARNING: Could not write coverage history: %s",
            error,
        )

    return trend_data


def _publish_pr_comment(summary: str) -> None:
    """Publish or update a PR comment without affecting the coverage result."""
    if os.environ.get("PR_EVENT_NAME") != "pull_request":
        logger.debug("[Coverage Gate] Skipping PR comment: not a pull request event.")
        return

    enabled = os.environ.get("ENABLE_PR_COMMENT", "true").strip().lower()

    if enabled not in {"true", "1", "yes"}:
        logger.info("[Coverage Gate] PR comments are disabled.")
        return

    token = os.environ.get("GITHUB_TOKEN", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    pull_number = os.environ.get("PR_NUMBER", "")
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")

    if not token:
        logger.warning(
            "[Coverage Gate] PR comment skipped: GitHub token is unavailable."
        )
        return

    try:
        result = publish_pr_comment(
            summary=summary,
            token=token,
            repository=repository,
            pull_number=pull_number,
            api_url=api_url,
        )
        logger.info(
            "[Coverage Gate] PR comment %s successfully.",
            result,
        )
    except (
        OSError,
        ValueError,
        TypeError,
        TimeoutError,
        subprocess.SubprocessError,
    ) as error:
        logger.warning(
            "[Coverage Gate] WARNING: Could not publish PR comment: %s",
            error,
        )


def run_action():
    """Run Coverage Gate inside GitHub Actions."""
    workspace = os.environ["GITHUB_WORKSPACE"]
    coverage_files = _resolve_coverage_files(
        workspace,
        os.environ["COVERAGE_FILE"],
    )
    coverage_file = coverage_files[0]

    threshold = float(os.environ["COVERAGE_THRESHOLD"])
    warning_margin = float(os.environ["WARNING_MARGIN"])
    changed_lines_threshold = float(os.environ.get("CHANGED_LINES_THRESHOLD", "0"))

    component_thresholds = parse_component_thresholds(
        os.environ.get("COMPONENT_THRESHOLDS", "")
    )

    baseline_text = os.environ.get("BASELINE_COVERAGE", "")
    baseline_coverage = float(baseline_text) if baseline_text else None
    max_regression = float(os.environ["MAX_REGRESSION"])

    logger.debug("[Coverage Gate] Starting coverage check...")
    logger.debug(
        "[Coverage Gate] Coverage report(s): %s",
        ", ".join(coverage_files),
    )
    logger.debug("[Coverage Gate] Required threshold: %.2f%%", threshold)
    logger.debug("[Coverage Gate] Warning margin: %.2f%%", warning_margin)
    logger.debug(
        "[Coverage Gate] Changed-lines threshold: %.2f%%",
        changed_lines_threshold,
    )

    if component_thresholds:
        logger.info(
            "[Coverage Gate] Configured %d component coverage threshold(s).",
            len(component_thresholds),
        )

    if baseline_coverage is not None:
        logger.info(
            "[Coverage Gate] Baseline coverage: %.2f%%",
            baseline_coverage,
        )
        logger.debug(
            "[Coverage Gate] Maximum allowed regression: %.2f percentage points",
            max_regression,
        )

    line_coverage = None

    if len(coverage_files) == 1:
        metrics = _parse_coverage_report(coverage_file)
        extension = Path(coverage_file).suffix.lower()
        use_unique_line_metrics = extension in {".out", ".coverprofile"}

        if extension not in {".out", ".coverprofile", ".json", ".info"}:
            try:
                report_root = ET.parse(coverage_file).getroot()
                report_name = report_root.tag.rsplit("}", 1)[-1]
                use_unique_line_metrics = report_name in {
                    "report",
                    "CoverageSession",
                }
            except ET.ParseError:
                use_unique_line_metrics = False

        if use_unique_line_metrics:
            line_coverage = parse_line_coverage(
                coverage_file,
                root_dir=workspace,
            )
            canonical_metrics = calculate_coverage_metrics(line_coverage)
            canonical_metrics.covered_branches = getattr(
                metrics, "covered_branches", None
            )
            canonical_metrics.valid_branches = getattr(metrics, "valid_branches", None)
            metrics = canonical_metrics
    else:
        logger.info(
            "[Coverage Gate] Merging %d coverage reports.",
            len(coverage_files),
        )
        line_coverage = merge_line_coverage(
            coverage_files,
            workspace,
        )
        metrics = calculate_coverage_metrics(line_coverage)

    if _coverage_badge_enabled():
        configured_badge_path = (
            os.environ.get(
                "BADGE_OUTPUT_PATH",
                "coverage-badge.svg",
            ).strip()
            or "coverage-badge.svg"
        )

        try:
            badge_path = _resolve_badge_output_path(
                workspace,
                configured_badge_path,
            )
            generate_badge(metrics.total_coverage, badge_path)
            logger.info(
                "[Coverage Gate] Coverage badge generated: %s",
                badge_path,
            )
        except (OSError, ValueError, TypeError) as error:
            logger.warning(
                "[Coverage Gate] WARNING: Could not generate coverage badge: %s",
                error,
            )

    result = enforce(
        metrics,
        threshold,
        warning_margin,
        baseline_coverage,
        max_regression,
    )

    changed_coverage = ChangedCoverageReport(
        available=False,
        files=[],
        message=(
            "Changed-code coverage not available: " "pull request diff is unavailable."
        ),
    )

    if os.environ.get("PR_EVENT_NAME") == "pull_request":
        base_sha = os.environ.get("PR_BASE_SHA")
        head_sha = os.environ.get("PR_HEAD_SHA")

        if base_sha and head_sha:
            try:
                diff_result = subprocess.run(
                    [
                        "git",
                        "diff",
                        "--unified=0",
                        f"{base_sha}...{head_sha}",
                        "--",
                    ],
                    cwd=workspace,
                    check=True,
                    capture_output=True,
                    text=True,
                )

                changed_lines = parse_changed_lines(diff_result.stdout)

                if line_coverage is None:
                    line_coverage = parse_line_coverage(
                        coverage_file,
                        root_dir=workspace,
                    )

                changed_coverage = generate_changed_coverage_report(
                    changed_lines,
                    line_coverage,
                )

                logger.info(
                    "[Coverage Gate] %s",
                    changed_coverage.message,
                )

            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                logger.warning(
                    "[Coverage Gate] WARNING: Changed-code coverage "
                    "could not be calculated: %s",
                    exc,
                )

                changed_coverage = ChangedCoverageReport(
                    available=False,
                    files=[],
                    message=(
                        "Changed-code coverage not available: "
                        "unable to read the pull request diff "
                        "or line-level coverage data."
                    ),
                )
        else:
            logger.warning(
                "[Coverage Gate] Base or head commit SHA is unavailable; "
                "skipping changed-code coverage."
            )
    else:
        logger.info(
            "[Coverage Gate] Not a pull request event; "
            "skipping changed-code coverage."
        )

    if os.environ.get("PR_EVENT_NAME") == "pull_request":
        changed_result = enforce_changed_coverage(
            changed_coverage,
            changed_lines_threshold,
        )
    else:
        changed_result = ChangedCoverageEnforcementResult(
            passed=True,
            coverage=None,
            threshold=changed_lines_threshold,
            available=False,
            message=(
                "Changed-line coverage enforcement skipped: "
                "not a pull request event."
            ),
        )

    logger.info(
        "[Coverage Gate] %s",
        changed_result.message,
    )

    component_results = []

    if component_thresholds:
        if line_coverage is None:
            line_coverage = parse_line_coverage(
                coverage_file,
                root_dir=workspace,
            )

        component_results = evaluate_component_coverage(
            line_coverage,
            component_thresholds,
        )

        for component_result in component_results:
            logger.info(
                "[Coverage Gate] %s",
                component_result.message,
            )

    final_passed = result.passed and changed_result.passed
    final_passed = final_passed and all(
        component.passed for component in component_results
    )

    trend_enabled = _coverage_trend_enabled()
    trend_data = None

    branch_coverage_kwargs = {}
    if (
        getattr(metrics, "covered_branches", None) is not None
        and getattr(metrics, "valid_branches", None) is not None
    ):
        branch_coverage_kwargs = {
            "covered_branches": getattr(metrics, "covered_branches", None),
            "valid_branches": getattr(metrics, "valid_branches", None),
        }

    if trend_enabled:
        trend_data = _process_coverage_trend(result.coverage)

    if component_results:
        if trend_enabled:
            summary = generate_summary(
                result,
                metrics.file_coverage,
                changed_coverage,
                changed_result,
                trend_data=trend_data,
                component_results=component_results,
                **branch_coverage_kwargs,
            )
        else:
            summary = generate_summary(
                result,
                metrics.file_coverage,
                changed_coverage,
                changed_result,
                component_results=component_results,
                **branch_coverage_kwargs,
            )
    elif trend_enabled:
        summary = generate_summary(
            result,
            metrics.file_coverage,
            changed_coverage,
            changed_result,
            trend_data=trend_data,
            **branch_coverage_kwargs,
        )
    else:
        summary = generate_summary(
            result,
            metrics.file_coverage,
            changed_coverage,
            changed_result,
            **branch_coverage_kwargs,
        )

    if len(coverage_files) > 1:
        summary += (
            "\n\n### Branch Coverage\n"
            "- **Status:** Unavailable for merged reports because branch "
            "identities cannot be safely deduplicated across reports.\n"
        )

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")

    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary_file:
            summary_file.write(summary)

        logger.debug("[Coverage Gate] GitHub Actions summary written.")
    else:
        logger.info(
            "[Coverage Gate] GitHub Actions summary path is unavailable; "
            "skipping summary."
        )

    _publish_pr_comment(summary)

    output_path = os.environ.get("GITHUB_OUTPUT")

    if output_path:
        with open(output_path, "a", encoding="utf-8") as output:
            output.write(f"coverage={result.coverage}\n")
            output.write(f"threshold={result.threshold}\n")
            output.write(f"passed={str(final_passed).lower()}\n")

            changed_coverage_value = (
                changed_result.coverage if changed_result.coverage is not None else ""
            )

            changed_lines_status = (
                str(changed_result.passed).lower()
                if changed_result.coverage is not None or not changed_result.passed
                else "skipped"
            )

            output.write(f"changed-lines-coverage={changed_coverage_value}\n")
            output.write(f"changed-lines-passed={changed_lines_status}\n")

        logger.debug("[Coverage Gate] GitHub Actions outputs published.")
    else:
        logger.info(
            "[Coverage Gate] GitHub Actions output path is unavailable; "
            "skipping outputs."
        )

    logger.info("")
    logger.info("========== Coverage Gate Result ==========")
    logger.info("Coverage:  %.1f%%", result.coverage)
    logger.info("Threshold: %.1f%%", result.threshold)
    logger.info("Details:   %s", result.message)
    logger.info(
        "Changed-line coverage: %s",
        (
            f"{changed_result.coverage:.1f}%"
            if changed_result.coverage is not None
            else "not available"
        ),
    )
    logger.info(
        "Changed-line threshold: %.1f%%",
        changed_result.threshold,
    )
    logger.info(
        "Changed-line enforcement: %s",
        "PASSED" if changed_result.passed else "FAILED",
    )

    if component_results:
        logger.info("Component coverage results:")

        for component_result in component_results:
            logger.info(
                "  %s",
                component_result.message,
            )

    logger.info(
        "[Coverage Gate] RESULT: %s",
        "PASSED" if final_passed else "FAILED",
    )

    if result.warning:
        logger.warning("Warning: Coverage is close to the required threshold.")

    if result.regression:
        logger.error(
            "REGRESSION: Coverage dropped by %.1f percentage points.",
            result.regression_amount,
        )

    logger.info("===========================================")

    return 0 if final_passed else 1


def main():
    """Run Coverage Gate from the command line or GitHub Actions."""
    if len(sys.argv) > 1 and sys.argv[1] == "--github-action":
        try:
            return run_action()
        except (KeyError, OSError, ValueError, subprocess.SubprocessError) as error:
            logger.error("[Coverage Gate] ERROR: %s", error)
            return 1

    logger.info("Coverage Gate started.")

    if len(sys.argv) < 3:
        logger.error(
            "Usage: python -m src.main <file> <threshold> "
            "[warning_margin] [baseline_coverage] [max_regression]"
        )
        return 1

    file_path = sys.argv[1]
    threshold_text = sys.argv[2]
    warning_margin_text = sys.argv[3] if len(sys.argv) >= 4 else "5.0"
    baseline_coverage_text = sys.argv[4] if len(sys.argv) >= 5 else None
    max_regression_text = sys.argv[5] if len(sys.argv) >= 6 else "5.0"

    logger.debug("Coverage report path: %s", file_path)
    logger.debug("Coverage threshold: %s%%", threshold_text)

    try:
        threshold = float(threshold_text)
    except ValueError:
        logger.error("Invalid threshold: %s", threshold_text)
        return 1

    try:
        warning_margin = float(warning_margin_text)
    except ValueError:
        logger.error("Invalid warning margin: %s", warning_margin_text)
        return 1

    baseline_coverage = None

    if baseline_coverage_text is not None:
        try:
            baseline_coverage = float(baseline_coverage_text)
        except ValueError:
            logger.error(
                "Invalid baseline coverage: %s",
                baseline_coverage_text,
            )
            return 1

    try:
        max_regression = float(max_regression_text)
    except ValueError:
        logger.error("Invalid max regression: %s", max_regression_text)
        return 1

    try:
        metrics = _parse_coverage_report(file_path)

        result = enforce(
            metrics,
            threshold,
            warning_margin,
            baseline_coverage,
            max_regression,
        )
    except (FileNotFoundError, ValueError) as error:
        logger.error("Coverage Gate failed: %s", error)
        return 1

    if result.passed:
        logger.info("Coverage Gate passed: %s", result.message)
    else:
        logger.error("Coverage Gate failed: %s", result.message)

    logger.info("Coverage Gate finished.")

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
