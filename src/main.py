import sys

from src.enforcer import enforce
from src.parser import parse_cobertura


def main():
    if len(sys.argv) < 3:
        print("Usage: python -m src.main <file> <threshold> " "[warning_margin]")
        return 1

    file_path = sys.argv[1]
    threshold_text = sys.argv[2]
    warning_margin_text = sys.argv[3] if len(sys.argv) >= 4 else "5.0"

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

    try:
        metrics = parse_cobertura(file_path)
        result = enforce(metrics, threshold, warning_margin)
    except (FileNotFoundError, ValueError) as error:
        print(f"Coverage Gate Error: {error}")
        return 1

    print(result.message)
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
