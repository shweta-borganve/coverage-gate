from dataclasses import dataclass

from src.parser import CoverageMetrics


@dataclass
class EnforcementResult:
    passed: bool
    warning: bool
    regression: bool
    coverage: float
    threshold: float
    baseline_coverage: float | None
    regression_amount: float
    message: str


def enforce(
    metrics: CoverageMetrics,
    threshold: float,
    warning_margin: float = 5.0,
    baseline_coverage: float | None = None,
    max_regression: float = 5.0,
) -> EnforcementResult:
    if not 0 <= threshold <= 100:
        raise ValueError("Threshold must be between 0 and 100")

    if not 0 <= warning_margin <= 100:
        raise ValueError("Warning margin must be between 0 and 100")

    if baseline_coverage is not None and not 0 <= baseline_coverage <= 100:
        raise ValueError("Baseline coverage must be between 0 and 100")

    if not 0 <= max_regression <= 100:
        raise ValueError("Maximum regression must be between 0 and 100")

    passed_threshold = metrics.total_coverage >= threshold

    margin = metrics.total_coverage - threshold
    warning = passed_threshold and margin <= warning_margin

    regression_amount = 0.0
    regression = False

    if baseline_coverage is not None:
        regression_amount = baseline_coverage - metrics.total_coverage
        regression = regression_amount > max_regression

    passed = passed_threshold and not regression

    status = "PASS" if passed else "FAIL"

    message = (
        f"Coverage {metrics.total_coverage:.1f}% "
        f"vs threshold {threshold}% — {status}"
    )

    if warning and not regression:
        message += (
            " — WARNING: Coverage is within " f"{warning_margin}% of the threshold."
        )

    if regression:
        message += (
            " — REGRESSION: Coverage dropped "
            f"{regression_amount:.1f} percentage points "
            f"from baseline {baseline_coverage:.1f}%."
        )

    return EnforcementResult(
        passed=passed,
        warning=warning,
        regression=regression,
        coverage=metrics.total_coverage,
        threshold=threshold,
        baseline_coverage=baseline_coverage,
        regression_amount=regression_amount,
        message=message,
    )
