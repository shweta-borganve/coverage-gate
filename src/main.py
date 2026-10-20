import os
import subprocess
import sys

from src.changed_coverage import ChangedCoverageReport, generate_changed_coverage_report
from src.changed_lines import parse_changed_lines
from src.enforcer import enforce
from src.logger_config import configure_logger
from src.parser import parse_cobertura, parse_line_coverage
from src.summary import generate_summary

logger = configure_logger(__name__)


def run_action():
    """Run Coverage Gate inside GitHub Actions."""
    workspace = os.environ["GITHUB_WORKSPACE"]
    coverage_file = os.path.join(
        workspace,
        os.environ["COVERAGE_FILE"],
    )
    threshold = float(os.environ["COVERAGE_THRESHOLD"])
    warning_margin = float(os.environ["WARNING_MARGIN"])

    baseline_text = os.environ.get("BASELINE_COVERAGE", "")
    baseline_coverage = float(baseline_text) if baseline_text else None
    max_regression = float(os.environ["MAX_REGRESSION"])

    logger.debug("[Coverage Gate] Starting coverage check...")
    logger.debug("[Coverage Gate] Coverage report: %s", coverage_file)
    logger.debug("[Coverage Gate] Required threshold: %.2f%%", threshold)
    logger.debug("[Coverage Gate] Warning margin: %.2f%%", warning_margin)

    if baseline_coverage is not None:
        logger.info("[Coverage Gate] Baseline coverage: %.2f%%", baseline_coverage)
        logger.debug(
            "[Coverage Gate] Maximum allowed regression: %.2f percentage points",
            max_regression,
        )
    else:
        logger.info("[Coverage Gate] Baseline regression check is not configured.")

    logger.debug("[Coverage Gate] Reading Cobertura XML report...")
    metrics = parse_cobertura(coverage_file)
    logger.debug("[Coverage Gate] Coverage report parsed successfully.")

    logger.debug("[Coverage Gate] Evaluating coverage rules...")
    result = enforce(
        metrics,
        threshold,
        warning_margin,
        baseline_coverage,
        max_regression,
    )

    logger.info("[Coverage Gate] Measured line coverage: %.2f%%", result.coverage)
    logger.info("[Coverage Gate] %s", result.message)

    changed_coverage = ChangedCoverageReport(
        available=False,
        files=[],
        message=(
            "Changed-code coverage not available: " "pull request diff is unavailable."
        ),
    )

    if os.environ.get("PR_EVENT_NAME") == "pull_request":
        logger.debug("[Coverage Gate] Checking changed-code coverage...")

        base_sha = os.environ.get("PR_BASE_SHA")
        head_sha = os.environ.get("PR_HEAD_SHA")

        if base_sha and head_sha:
            try:
                logger.debug(
                    "[Coverage Gate] Comparing pull request changes with the base revision..."
                )

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
                logger.debug("[Coverage Gate] Changed lines identified.")

                logger.debug("[Coverage Gate] Reading line-level coverage data...")
                line_coverage = parse_line_coverage(
                    coverage_file,
                    root_dir=workspace,
                )

                changed_coverage = generate_changed_coverage_report(
                    changed_lines,
                    line_coverage,
                )

                logger.debug(
                    "[Coverage Gate] Changed-code coverage analysis completed."
                )
                logger.info("[Coverage Gate] %s", changed_coverage.message)

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
                "[Coverage Gate] WARNING: Base or head commit SHA is "
                "unavailable; skipping changed-code coverage."
            )
    else:
        logger.info(
            "[Coverage Gate] Not a pull request event; "
            "skipping changed-code coverage."
        )

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")

    if summary_path:
        logger.debug("[Coverage Gate] Writing GitHub Actions step summary...")
        with open(summary_path, "a", encoding="utf-8") as summary_file:
            summary_file.write(
                generate_summary(
                    result,
                    metrics.file_coverage,
                    changed_coverage,
                )
            )
        logger.debug("[Coverage Gate] Step summary written successfully.")
    else:
        logger.info("[Coverage Gate] GitHub Actions summary path is unavailable.")

    output_path = os.environ.get("GITHUB_OUTPUT")

    if output_path:
        logger.debug("[Coverage Gate] Publishing coverage output...")
        with open(output_path, "a", encoding="utf-8") as output:
            output.write(f"coverage={result.coverage}\n")
    else:
        logger.info("[Coverage Gate] GitHub Actions output path is unavailable.")

    if not result.passed:
        logger.error("[Coverage Gate] RESULT: FAILED")
        return 1

    logger.info("[Coverage Gate] RESULT: PASSED")
    return 0


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

    logger.info("Reading coverage report.")

    try:
        metrics = parse_cobertura(file_path)
        logger.info("Coverage report parsed successfully.")

        logger.info("Evaluating coverage rules.")
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
