import os
import subprocess
import sys
from pathlib import Path

from src.badge import generate_badge
from src.changed_coverage import (
    ChangedCoverageReport,
    generate_changed_coverage_report,
)
from src.changed_lines import parse_changed_lines
from src.enforcer import enforce, enforce_changed_coverage
from src.logger_config import configure_logger
from src.parser import parse_cobertura, parse_line_coverage
from src.summary import generate_summary

logger = configure_logger(__name__)


def get_input(name, default=None):
    """Read a GitHub Docker Action input."""
    env_name = f"INPUT_{name.upper()}"
    value = os.environ.get(env_name, default)

    if value is None:
        raise ValueError(f"Required input '{name}' is missing.")

    return value.strip()


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


def resolve_badge_output_path(workspace, output_path):
    """Resolve the badge output path and prevent workspace escapes."""
    workspace = workspace.resolve()
    badge_path = Path(output_path)

    if not badge_path.is_absolute():
        badge_path = workspace / badge_path

    badge_path = badge_path.resolve()

    try:
        badge_path.relative_to(workspace)
    except ValueError:
        raise ValueError(
            "badge-output-path must point to a file inside GITHUB_WORKSPACE."
        ) from None

    if badge_path == workspace:
        raise ValueError(
            "badge-output-path must point to a file inside GITHUB_WORKSPACE."
        )

    return badge_path


def generate_coverage_badge(workspace, coverage):
    """Generate an optional SVG badge without affecting enforcement."""
    enabled = get_input("enable-coverage-badge", "false").lower()

    if enabled not in {"true", "1", "yes"}:
        logger.info("Coverage badge generation is disabled.")
        return

    configured_path = (
        get_input("badge-output-path", "coverage-badge.svg") or "coverage-badge.svg"
    )

    try:
        badge_path = resolve_badge_output_path(workspace, configured_path)
        generate_badge(coverage, badge_path)
        logger.info("Coverage badge generated: %s", badge_path)
    except (OSError, ValueError, TypeError) as error:
        logger.warning("Could not generate coverage badge: %s", error)


def main():
    logger.info("Starting Coverage Gate Docker Action.")

    workspace = Path(os.environ.get("GITHUB_WORKSPACE", "/github/workspace")).resolve()

    coverage_path = resolve_coverage_path(
        workspace,
        get_input("coverage-file"),
    )

    threshold = float(get_input("threshold", "80"))
    changed_lines_threshold = float(get_input("changed-lines-threshold", "0"))
    warning_margin = float(get_input("warning-margin", "5"))
    baseline_text = get_input("baseline-coverage", "")
    baseline_coverage = float(baseline_text) if baseline_text else None
    max_regression = float(get_input("max-regression", "5"))

    logger.info("Reading coverage report: %s", coverage_path)
    metrics = parse_cobertura(coverage_path)

    generate_coverage_badge(workspace, metrics.total_coverage)

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
                logger.warning(
                    "Changed-code coverage unavailable: %s",
                    error,
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

    changed_result = enforce_changed_coverage(
        changed_coverage,
        changed_lines_threshold,
    )
    logger.info("%s", changed_result.message)

    final_passed = result.passed and changed_result.passed

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        logger.info("Writing GitHub Actions step summary.")

        with open(summary_path, "a", encoding="utf-8") as summary_file:
            summary_file.write(
                generate_summary(
                    result,
                    metrics.file_coverage,
                    changed_coverage,
                    changed_result,
                )
            )

    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        changed_coverage_output = (
            "" if changed_result.coverage is None else str(changed_result.coverage)
        )

        with open(output_path, "a", encoding="utf-8") as output_file:
            output_file.write(f"coverage={result.coverage}\n")
            output_file.write(f"changed-lines-coverage={changed_coverage_output}\n")
            output_file.write(
                f"changed-lines-passed={str(changed_result.passed).lower()}\n"
            )
            output_file.write(f"passed={str(final_passed).lower()}\n")

        logger.info("Coverage outputs written.")

    if not final_passed:
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
