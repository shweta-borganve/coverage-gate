import sys

from src.enforcer import enforce
from src.parser import parse_cobertura


def main():
    if len(sys.argv) < 3:
        print(
            "Usage: python -m src.main <file> <threshold> "
            "[warning_margin] [baseline_coverage] [max_regression]"
        )
        return 1

    file_path = sys.argv[1]
    threshold_text = sys.argv[2]
    warning_margin_text = sys.argv[3] if len(sys.argv) >= 4 else "5.0"
    baseline_coverage_text = sys.argv[4] if len(sys.argv) >= 5 else None
    max_regression_text = sys.argv[5] if len(sys.argv) >= 6 else "5.0"

    try:
        threshold = float(threshold_text)
    except ValueError:
        print(f"Coverage Gate Error: Invalid threshold: {threshold_text}")
        return 1

    try:
        warning_margin = float(warning_margin_text)
    except ValueError:
        print("Coverage Gate Error: " f"Invalid warning margin: {warning_margin_text}")
        return 1

    baseline_coverage = None

    if baseline_coverage_text is not None:
        try:
            baseline_coverage = float(baseline_coverage_text)
        except ValueError:
            print(
                "Coverage Gate Error: "
                f"Invalid baseline coverage: {baseline_coverage_text}"
            )
            return 1

    try:
        max_regression = float(max_regression_text)
    except ValueError:
        print("Coverage Gate Error: " f"Invalid max regression: {max_regression_text}")
        return 1

    try:
        metrics = parse_cobertura(file_path)
        result = enforce(
            metrics,
            threshold,
            warning_margin,
            baseline_coverage,
            max_regression,
        )
    except (FileNotFoundError, ValueError) as error:
        print(f"Coverage Gate Error: {error}")
        return 1

    print(result.message)
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
