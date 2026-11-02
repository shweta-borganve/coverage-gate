 feature/add-coverage-report-parser
import json
import logging

main
import os
import subprocess
import sys
from pathlib import Path

from src.changed_coverage import (
    ChangedCoverageReport,
    generate_changed_coverage_report,
)
from src.changed_lines import parse_changed_lines
from src.enforcer import enforce
 feature/add-coverage-report-parser
from src.parser import parse_coverage_report, parse_line_coverage
from src.summary import generate_summary

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("coverage-gate")

from src.logger_config import configure_logger
from src.parser import parse_cobertura, parse_line_coverage
from src.summary import generate_summary

logger = configure_logger(__name__)
 main


def get_input(name, default=None):
    """Read a GitHub Docker Action input."""
feature/add-coverage-report-parser
    env_name = f"INPUT_{name.replace('-', '_').upper()}"

    env_name = f"INPUT_{name.upper()}"
main
    value = os.environ.get(env_name, default)

    if value is None:
        raise ValueError(f"Required input '{name}' is missing.")

    return value.strip()


feature/add-coverage-report-parser
def main():
    logger.info("Starting Coverage Gate Docker Action.")

    workspace = Path(os.environ.get("GITHUB_WORKSPACE", "/github/workspace"))
    coverage_path = Path(get_input("coverage-file"))

    if not coverage_path.is_absolute():
        coverage_path = workspace / coverage_path

def resolve_coverage_path(workspace, coverage_file):
    """Resolve the coverage report path and prevent workspace escapes."""
    workspace = workspace.resolve()
    coverage_path = Path(coverage_file)

    if not coverage_path.is_absolute():
        coverage_path = workspace / coverage_path

    coverage_path = coverage_path.resolve()

    try:
        coverage_path.relative_to(workspace)
    except ValueError:
        raise ValueError(
            "coverage-file must point to a file inside GITHUB_WORKSPACE."
        ) from None

    return coverage_path


def main():
    logger.info("Starting Coverage Gate Docker Action.")

    workspace = Path(os.environ.get("GITHUB_WORKSPACE", "/github/workspace")).resolve()

    coverage_path = resolve_coverage_path(
        workspace,
        get_input("coverage-file"),
    )
main

    threshold = float(get_input("threshold", "80"))
    warning_margin = float(get_input("warning-margin", "5"))
    baseline_text = get_input("baseline-coverage", "")
    baseline_coverage = float(baseline_text) if baseline_text else None
    max_regression = float(get_input("max-regression", "5"))

    logger.info("Reading coverage report: %s", coverage_path)
feature/add-coverage-report-parser
    metrics = parse_coverage_report(
        str(coverage_path),
        root_dir=workspace.resolve(),
    )

    metrics = parse_cobertura(coverage_path)
main

    logger.info("Evaluating coverage rules.")
    result = enforce(
        metrics,
        threshold,
        warning_margin,
        baseline_coverage,
        max_regression,
    )
    logger.info("%s", result.message)

    changed_coverage = ChangedCoverageReport(
        available=False,
        files=[],
feature/add-coverage-report-parser
        message="Changed-code coverage not available: pull request diff is unavailable.",

        message=(
            "Changed-code coverage not available: " "pull request diff is unavailable."
        ),
 main
    )

    if os.environ.get("GITHUB_EVENT_NAME") == "pull_request":
        base_sha = os.environ.get("GITHUB_BASE_REF")
        head_sha = os.environ.get("GITHUB_HEAD_REF")

        # Prefer the actual pull request SHAs from the event payload.
        event_path = os.environ.get("GITHUB_EVENT_PATH")
feature/add-coverage-report-parser

        if event_path and Path(event_path).is_file():

        if event_path and Path(event_path).is_file():
            import json

main
            with open(event_path, encoding="utf-8") as event_file:
                event = json.load(event_file)

            pull_request = event.get("pull_request", {})
            base_sha = pull_request.get("base", {}).get("sha", base_sha)
            head_sha = pull_request.get("head", {}).get("sha", head_sha)

        if base_sha and head_sha:
            try:
                logger.info("Calculating changed-code coverage.")
feature/add-coverage-report-parser


 main
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
                    coverage_path,
                    root_dir=workspace,
                )
                changed_coverage = generate_changed_coverage_report(
                    changed_lines,
                    line_coverage,
                )
feature/add-coverage-report-parser
            except (
                OSError,
                ValueError,
                subprocess.SubprocessError,
            ) as error:
                logger.warning("Changed-code coverage unavailable: %s", error)


            except (OSError, ValueError, subprocess.SubprocessError) as error:
                logger.warning(
                    "Changed-code coverage unavailable: %s",
                    error,
                )
 main
                changed_coverage = ChangedCoverageReport(
                    available=False,
                    files=[],
                    message=(
                        "Changed-code coverage not available: "
                        "unable to read the pull request diff "
                        "or line-level coverage data."
                    ),
                )

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
feature/add-coverage-report-parser

    if summary_path:
        logger.info("Writing GitHub Actions step summary.")

    if summary_path:
        logger.info("Writing GitHub Actions step summary.")

main
        with open(summary_path, "a", encoding="utf-8") as summary_file:
            summary_file.write(
                generate_summary(
                    result,
                    metrics.file_coverage,
                    changed_coverage,
                )
            )

    output_path = os.environ.get("GITHUB_OUTPUT")
 feature/add-coverage-report-parser


main
    if output_path:
        with open(output_path, "a", encoding="utf-8") as output_file:
            output_file.write(f"coverage={result.coverage}\n")

        logger.info("Coverage output written.")

    if not result.passed:
        logger.error("Coverage Gate failed.")
        return 1

    logger.info("Coverage Gate passed.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        logger.error("Coverage Gate error: %s", error)
        sys.exit(1)
