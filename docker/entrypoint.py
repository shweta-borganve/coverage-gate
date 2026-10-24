import logging
import os
import subprocess
import sys
from pathlib import Path

from src.changed_coverage import ChangedCoverageReport, generate_changed_coverage_report
from src.changed_lines import parse_changed_lines
from src.enforcer import enforce
from src.parser import parse_cobertura, parse_line_coverage
from src.summary import generate_summary

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("coverage-gate")


def get_input(name, default=None):
    """Read a GitHub Docker Action input."""
    env_name = f"INPUT_{name.replace('-', '_').upper()}"
    value = os.environ.get(env_name, default)

    if value is None:
        raise ValueError(f"Required input '{name}' is missing.")

    return value.strip()


def main():
    logger.info("Starting Coverage Gate Docker Action.")

    workspace = Path(os.environ.get("GITHUB_WORKSPACE", "/github/workspace"))
    coverage_path = Path(get_input("coverage-file"))
    if not coverage_path.is_absolute():
        coverage_path = workspace / coverage_path

    threshold = float(get_input("threshold", "80"))
    warning_margin = float(get_input("warning-margin", "5"))
    baseline_text = get_input("baseline-coverage", "")
    baseline_coverage = float(baseline_text) if baseline_text else None
    max_regression = float(get_input("max-regression", "5"))

    logger.info("Reading coverage report: %s", coverage_path)
    metrics = parse_cobertura(coverage_path)

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
        message=(
            "Changed-code coverage not available: " "pull request diff is unavailable."
        ),
    )

    if os.environ.get("GITHUB_EVENT_NAME") == "pull_request":
        base_sha = os.environ.get("GITHUB_BASE_REF")
        head_sha = os.environ.get("GITHUB_HEAD_REF")

        # Prefer the actual pull request SHAs from the event payload.
        event_path = os.environ.get("GITHUB_EVENT_PATH")
        if event_path and Path(event_path).is_file():
            import json

            with open(event_path, encoding="utf-8") as event_file:
                event = json.load(event_file)
            pull_request = event.get("pull_request", {})
            base_sha = pull_request.get("base", {}).get("sha", base_sha)
            head_sha = pull_request.get("head", {}).get("sha", head_sha)

        if base_sha and head_sha:
            try:
                logger.info("Calculating changed-code coverage.")
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
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                logger.warning("Changed-code coverage unavailable: %s", error)
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
    if summary_path:
        logger.info("Writing GitHub Actions step summary.")
        with open(summary_path, "a", encoding="utf-8") as summary_file:
            summary_file.write(
                generate_summary(
                    result,
                    metrics.file_coverage,
                    changed_coverage,
                )
            )

    output_path = os.environ.get("GITHUB_OUTPUT")
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
