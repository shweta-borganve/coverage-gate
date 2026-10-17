def generate_summary(
    result,
    file_coverage=None,
    changed_coverage=None,
):
    status = "PASS" if result.passed else "FAIL"
    warning_status = "Yes" if result.warning else "No"

    summary_lines = [
        "## Coverage Gate Summary",
        "",
        f"- **Coverage:** {result.coverage:.1f}%",
        f"- **Required threshold:** {result.threshold:.1f}%",
        f"- **Status:** {status}",
        f"- **Warning:** {warning_status}",
    ]

    if result.baseline_coverage is None:
        summary_lines.append("- **Regression:** Not checked (no baseline configured)")
    elif result.regression:
        summary_lines.append(
            f"- **Regression:** Yes — dropped "
            f"{result.regression_amount:.1f} percentage points "
            f"from baseline {result.baseline_coverage:.1f}%"
        )
    else:
        summary_lines.append("- **Regression:** No — within the allowed limit")

    if file_coverage:
        summary_lines.extend(
            [
                "",
                "### Per-file Coverage",
                "",
                "| File | Coverage |",
                "|---|---:|",
            ]
        )

        for filename, coverage in sorted(file_coverage.items()):
            summary_lines.append(f"| `{filename}` | {coverage:.1f}% |")

    if changed_coverage is not None:
        summary_lines.extend(
            [
                "",
                "### Changed-Code Coverage",
                "",
            ]
        )

        if not changed_coverage.available:
            summary_lines.append(f"**Not available:** {changed_coverage.message}")
        else:
            summary_lines.extend(
                [
                    "| File | Changed lines | Covered | Uncovered | Uncovered line numbers |",
                    "|---|---:|---:|---:|---|",
                ]
            )

            if not changed_coverage.files:
                summary_lines.append("| No changed lines | 0 | 0 | 0 | None |")

            for item in changed_coverage.files:
                line_numbers = (
                    ", ".join(str(number) for number in item.uncovered_line_numbers)
                    or "None"
                )
                summary_lines.append(
                    f"| `{item.filename}` | {item.changed_lines} | "
                    f"{item.covered_lines} | {item.uncovered_lines} | "
                    f"{line_numbers} |"
                )

    return "\n".join(summary_lines) + "\n"
