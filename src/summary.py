feature/per-file-coverage
def generate_summary(result, file_coverage=None):
    status = "PASS" if result.passed else "FAIL"
    warning_status = "Yes" if result.warning else "No"


def generate_summary(result):
    status = "PASS" if result.passed else "FAIL"
    warning_status = "Yes" if result.warning else "No"
main
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

feature/per-file-coverage
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


main
    return "\n".join(summary_lines) + "\n"
