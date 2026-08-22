from dataclasses import dataclass
from src.parser import CoverageMetrics

@dataclass
class EnforcementResult:
    passed: bool
    coverage: float
    threshold: float
    message: str

def enforce(metrics: CoverageMetrics, threshold: float) -> EnforcementResult:
    passed = metrics.total_coverage >= threshold
    message = f"Coverage {metrics.total_coverage:.1f}% vs threshold {threshold}%"
    
    return EnforcementResult(
        passed=passed,
        coverage=metrics.total_coverage,
        threshold=threshold,
        message=message,
    ) 