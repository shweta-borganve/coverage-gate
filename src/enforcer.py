from dataclasses import dataclass

from src.parser import CoverageMetrics


@dataclass
class EnforcementResult:
    passed: bool
    warning: bool
    coverage: float
    threshold: float
    message: str


def enforce(metrics: CoverageMetrics, threshold: float) -> EnforcementResult:
    if not 0 <= threshold <= 100:
        raise ValueError("Threshold must be between 0 and 100")

    passed = metrics.total_coverage >= threshold

    margin = metrics.total_coverage - threshold
    warning = passed and margin <= 5

    status = "PASS" if passed else "FAIL"

    message = (
        f"Coverage {metrics.total_coverage:.1f}% "
        f"vs threshold {threshold}% — {status}"
    )

    if warning:
        message += " — WARNING: Coverage is within 5% of the threshold."

    return EnforcementResult(
        passed=passed,
        warning=warning,
        coverage=metrics.total_coverage,
        threshold=threshold,
        message=message,
    )
