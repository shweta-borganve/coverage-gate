from src.logger_config import configure_logger

logger = configure_logger(__name__)


def _format_filename(filename):
    """Safely format filenames for GitHub Markdown tables."""
    escaped_filename = str(filename)
    escaped_filename = escaped_filename.replace("\\", "\\\\")
    escaped_filename = escaped_filename.replace("`", "\\`")
    escaped_filename = escaped_filename.replace("|", "&#124;")
    escaped_filename = escaped_filename.replace("\n", "&#10;")
    escaped_filename = escaped_filename.replace("\r", "&#13;")
    return f"`{escaped_filename}`"


def _append_coverage_trend(summary_lines, trend_data):
    """Add optional historical coverage trend details to the summary."""
    if trend_data is None:
        return

    summary_lines.extend(
        [
            "",
            "### Coverage Trend",
            "",
        ]
    )

    direction = trend_data.get("direction", "unavailable")

    if direction == "unavailable":
        summary_lines.append(
            "**Status:** Unavailable (historical coverage could not be retrieved)"
        )
        summary_lines.append(
            f"**Details:** {trend_data.get('message', 'No details available.')}"
        )
        return

    if direction == "no-history":
        summary_lines.append(
            "**Status:** No previous history available (first recorded run)"
        )
        summary_lines.append(f"**Current coverage:** {trend_data['history'][-1]:.1f}%")
        return

    status_labels = {
        "improved": "Improved",
        "declined": "Declined",
        "unchanged": "Unchanged",
    }
    status = status_labels.get(direction, "Unavailable")

    summary_lines.extend(
        [
            f"- **Status:** {status}",
            f"- **Previous coverage:** {trend_data['previous_coverage']:.1f}%",
            f"- **Current coverage:** {trend_data['history'][-1]:.1f}%",
            f"- **Change:** {trend_data['change']:+.2f} percentage points",
            f"- **Historical records:** {trend_data['records_count']}",
        ]
    )


def generate_summary(
    result,
    file_coverage=None,
    changed_coverage=None,
    changed_enforcement=None,
    trend_data=None,
):
    logger.info("Generating Coverage Gate summary.")

    final_passed = result.passed and (
        changed_enforcement is None or changed_enforcement.passed
    )

    status = "PASS" if final_passed else "FAIL"
    warning_status = "Yes" if result.warning else "No"

    logger.debug(
        "Summary details: status=%s, coverage=%.1f%%, threshold=%.1f%%, "
        "warning=%s, regression=%s",
        status,
        result.coverage,
        result.threshold,
        warning_status,
        result.regression,
    )

    summary_lines = [
        "## Coverage Gate Summary",
        "",
        f"- **Coverage:** {result.coverage:.1f}%",
        f"- **Required threshold:** {result.threshold:.1f}%",
        f"- **Status:** {status}",
        f"- **Warning:** {warning_status}",
    ]

    if result.baseline_coverage is None:
        logger.debug("Regression checking skipped because no baseline was configured.")
        summary_lines.append("- **Regression:** Not checked (no baseline configured)")
    elif result.regression:
        logger.warning(
            "Including coverage regression details in summary: "
            "coverage dropped %.1f percentage points.",
            result.regression_amount,
        )
        summary_lines.append(
            f"- **Regression:** Yes — dropped "
            f"{result.regression_amount:.1f} percentage points "
            f"from baseline {result.baseline_coverage:.1f}%"
        )
    else:
        logger.debug("No coverage regression detected for the summary.")
        summary_lines.append("- **Regression:** No — within the allowed limit")

    if changed_enforcement is not None:
        summary_lines.extend(
            [
                "",
                "### Changed-Line Coverage Enforcement",
                "",
                f"- **Required threshold:** {changed_enforcement.threshold:.1f}%",
            ]
        )

        if not changed_enforcement.passed:
            summary_lines.append("- **Status:** FAIL")
            if changed_enforcement.coverage is not None:
                summary_lines.append(
                    f"- **Coverage:** {changed_enforcement.coverage:.1f}%"
                )
            summary_lines.append(f"- **Details:** {changed_enforcement.message}")
        elif not changed_enforcement.available:
            summary_lines.append("- **Status:** Skipped")
            summary_lines.append(f"- **Details:** {changed_enforcement.message}")
        elif changed_enforcement.coverage is None:
            summary_lines.append("- **Coverage:** Not applicable (no changed lines)")
            summary_lines.append("- **Status:** Skipped")
        else:
            summary_lines.extend(
                [
                    f"- **Coverage:** {changed_enforcement.coverage:.1f}%",
                    "- **Status:** PASS",
                ]
            )

    _append_coverage_trend(summary_lines, trend_data)

    if file_coverage:
        logger.info(
            "Adding per-file coverage details for %d files.",
            len(file_coverage),
        )

        summary_lines.extend(
            [
                "",
                "### Per-file Coverage",
                "",
                "<details>",
                "<summary>Show per-file coverage</summary>",
                "",
                "| File | Coverage |",
                "|---|---:|",
            ]
        )

        for filename, coverage in sorted(file_coverage.items()):
            logger.debug(
                "Adding per-file coverage: %s = %.1f%%.",
                filename,
                coverage,
            )
            summary_lines.append(f"| {_format_filename(filename)} | {coverage:.1f}% |")

        summary_lines.extend(
            [
                "",
                "</details>",
            ]
        )
    else:
        logger.debug("No per-file coverage details provided.")

    show_changed_coverage = changed_coverage is not None and not (
        changed_enforcement is not None
        and not changed_enforcement.available
        and not changed_coverage.available
    )

    if show_changed_coverage:
        logger.info("Adding changed-code coverage details to summary.")

        summary_lines.extend(
            [
                "",
                "### Changed-Code Coverage",
                "",
            ]
        )

        if not changed_coverage.available:
            logger.warning(
                "Changed-code coverage is unavailable: %s",
                changed_coverage.message,
            )
            summary_lines.append(f"**Not available:** {changed_coverage.message}")
        else:
            logger.debug(
                "Changed-code coverage is available for %d files.",
                len(changed_coverage.files),
            )

            if changed_coverage.coverage_percentage is not None:
                summary_lines.append(
                    f"**Aggregate changed-line coverage:** "
                    f"{changed_coverage.coverage_percentage:.1f}% "
                    f"({changed_coverage.covered_changed_lines}/"
                    f"{changed_coverage.total_changed_lines} lines)"
                )
                summary_lines.append("")

            summary_lines.extend(
                [
                    "| File | Changed lines | Covered | Uncovered | Uncovered line numbers |",
                    "|---|---:|---:|---:|---|",
                ]
            )

            if not changed_coverage.files:
                logger.info("No changed lines were found for coverage reporting.")
                summary_lines.append("| No changed lines | 0 | 0 | 0 | None |")

            for item in changed_coverage.files:
                line_numbers = (
                    ", ".join(str(number) for number in item.uncovered_line_numbers)
                    or "None"
                )

                logger.debug(
                    "Adding changed-code coverage for %s: "
                    "%d changed, %d covered, %d uncovered lines.",
                    item.filename,
                    item.changed_lines,
                    item.covered_lines,
                    item.uncovered_lines,
                )

                summary_lines.append(
                    f"| {_format_filename(item.filename)} | "
                    f"{item.changed_lines} | "
                    f"{item.covered_lines} | "
                    f"{item.uncovered_lines} | "
                    f"{line_numbers} |"
                )

    summary = "\n".join(summary_lines) + "\n"

    logger.info(
        "Coverage Gate summary generated successfully (%d lines).",
        len(summary_lines),
    )
    logger.debug("Generated summary contains %d characters.", len(summary))

    return summary
