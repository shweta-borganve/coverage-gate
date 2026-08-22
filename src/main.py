import sys

from src.enforcer import enforce
from src.parser import parse_cobertura

if len(sys.argv) < 3:
    print("Usage: python -m src.main <file> <threshold>")
    sys.exit(1)

metrics = parse_cobertura(sys.argv[1])
result = enforce(metrics, float(sys.argv[2]))
print(result.message)
sys.exit(0 if result.passed else 1)
