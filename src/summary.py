from src.logger_config import configure_logger

logger = configure_logger(__name__)


def generate_summary(
    result,
    file_coverage=None,
    changed_coverage=None,
):
    logger.info("Generating Coverage Gate summary.")

    status = "PASS" if result.passed else "FAIL"
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
            summary_lines.append(f"| `{filename}` | {coverage:.1f}% |")

        summary_lines.extend(
            [
                "",
                "</details>",
            ]
        )
    else:
        logger.debug("No per-file coverage details provided.")

    if changed_coverage is not None:
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
                    f"| `{item.filename}` | {item.changed_lines} | "
                    f"{item.covered_lines} | {item.uncovered_lines} | "
                    f"{line_numbers} |"
                )

    summary = "\n".join(summary_lines) + "\n"

    logger.info(
        "Coverage Gate summary generated successfully (%d lines).",
        len(summary_lines),
    )
    logger.debug("Generated summary contains %d characters.", len(summary))

    return summary
