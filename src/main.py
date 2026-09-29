import sys

from src.enforcer import enforce
from src.parser import parse_cobertura


def main():
    if len(sys.argv) < 3:
        print("Usage: python -m src.main <file> <threshold>")
        return 1

    file_path = sys.argv[1]
    threshold_text = sys.argv[2]

    try:
        threshold = float(threshold_text)
    except ValueError:
        print(f"Coverage Gate Error: Invalid threshold: {threshold_text}")
        return 1

    try:
        metrics = parse_cobertura(file_path)
        result = enforce(metrics, threshold)
    except (FileNotFoundError, ValueError) as error:
        print(f"Coverage Gate Error: {error}")
        return 1

    print(result.message)
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main()) 