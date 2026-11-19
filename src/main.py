import os
import subprocess
import sys
from pathlib import Path

from src.changed_coverage import (
    ChangedCoverageReport,
    generate_changed_coverage_report,
)
from src.changed_lines import parse_changed_lines
from src.enforcer import enforce, enforce_changed_coverage
from src.logger_config import configure_logger
from src.parser import parse_cobertura, parse_lcov, parse_line_coverage
from src.pr_comment import publish_pr_comment
from src.summary import generate_summary

logger = configure_logger(__name__)


def _parse_coverage_report(file_path: str):
    """Parse a supported coverage report based on its file extension."""
    extension = Path(file_path).suffix.lower()

    if extension == ".info":
        logger.debug("[Coverage Gate] Detected LCOV coverage report.")
        return parse_lcov(file_path)

    logger.debug("[Coverage Gate] Detected Cobertura XML coverage report.")
    return parse_cobertura(file_path)


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
    coverage_file = _resolve_coverage_file(
        workspace,
        os.environ["COVERAGE_FILE"],
    )

    threshold = float(os.environ["COVERAGE_THRESHOLD"])
    warning_margin = float(os.environ["WARNING_MARGIN"])
    changed_lines_threshold = float(os.environ.get("CHANGED_LINES_THRESHOLD", "0"))

    baseline_text = os.environ.get("BASELINE_COVERAGE", "")
    baseline_coverage = float(baseline_text) if baseline_text else None
    max_regression = float(os.environ["MAX_REGRESSION"])

    logger.debug("[Coverage Gate] Starting coverage check...")
    logger.debug("[Coverage Gate] Coverage report: %s", coverage_file)
    logger.debug("[Coverage Gate] Required threshold: %.2f%%", threshold)
    logger.debug("[Coverage Gate] Warning margin: %.2f%%", warning_margin)
    logger.debug(
        "[Coverage Gate] Changed-lines threshold: %.2f%%",
        changed_lines_threshold,
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

    metrics = _parse_coverage_report(coverage_file)

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

    changed_result = enforce_changed_coverage(
        changed_coverage,
        changed_lines_threshold,
    )

    logger.info(
        "[Coverage Gate] %s",
        changed_result.message,
    )

    final_passed = result.passed and changed_result.passed

    summary = generate_summary(
        result,
        metrics.file_coverage,
        changed_coverage,
        changed_result,
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

            output.write(f"changed-lines-coverage={changed_coverage_value}\n")
            output.write(
                "changed-lines-passed=" f"{str(changed_result.passed).lower()}\n"
            )

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
