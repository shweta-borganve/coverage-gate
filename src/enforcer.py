from dataclasses import dataclass

from src.logger_config import configure_logger
from src.parser import CoverageMetrics

logger = configure_logger(__name__)


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
    logger.info("Starting coverage enforcement.")
    logger.debug(
        "Enforcement settings: coverage=%.1f%%, threshold=%.1f%%, "
        "warning_margin=%.1f%%, baseline=%s, max_regression=%.1f%%",
        metrics.total_coverage,
        threshold,
        warning_margin,
        (
            f"{baseline_coverage:.1f}%"
            if baseline_coverage is not None
            else "not provided"
        ),
        max_regression,
    )

    if not 0 <= threshold <= 100:
        logger.error(
            "Invalid threshold: %.1f. Expected a value from 0 to 100.", threshold
        )
        raise ValueError("Threshold must be between 0 and 100")

    if not 0 <= warning_margin <= 100:
        logger.error(
            "Invalid warning margin: %.1f. Expected a value from 0 to 100.",
            warning_margin,
        )
        raise ValueError("Warning margin must be between 0 and 100")

    if baseline_coverage is not None and not 0 <= baseline_coverage <= 100:
        logger.error(
            "Invalid baseline coverage: %.1f. Expected a value from 0 to 100.",
            baseline_coverage,
        )
        raise ValueError("Baseline coverage must be between 0 and 100")

    if not 0 <= max_regression <= 100:
        logger.error(
            "Invalid maximum regression: %.1f. Expected a value from 0 to 100.",
            max_regression,
        )
        raise ValueError("Maximum regression must be between 0 and 100")

    passed_threshold = metrics.total_coverage >= threshold

    margin = metrics.total_coverage - threshold
    warning = passed_threshold and margin <= warning_margin

    regression_amount = 0.0
    regression = False

    if baseline_coverage is not None:
        regression_amount = baseline_coverage - metrics.total_coverage
        regression = regression_amount > max_regression

        logger.debug(
            "Coverage regression check: baseline=%.1f%%, current=%.1f%%, "
            "drop=%.1f percentage points, allowed=%.1f percentage points.",
            baseline_coverage,
            metrics.total_coverage,
            regression_amount,
            max_regression,
        )

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
        logger.warning(
            "Coverage passed but is close to the threshold: "
            "%.1f%% coverage, %.1f%% threshold.",
            metrics.total_coverage,
            threshold,
        )

    if regression:
        message += (
            " — REGRESSION: Coverage dropped "
            f"{regression_amount:.1f} percentage points "
            f"from baseline {baseline_coverage:.1f}%."
        )
        logger.error(
            "Coverage regression detected: coverage dropped by "
            "%.1f percentage points from the %.1f%% baseline.",
            regression_amount,
            baseline_coverage,
        )

    if not passed_threshold:
        logger.error(
            "Coverage is below the required threshold: "
            "%.1f%% current coverage, %.1f%% required.",
            metrics.total_coverage,
            threshold,
        )

    result = EnforcementResult(
        passed=passed,
        warning=warning,
        regression=regression,
        coverage=metrics.total_coverage,
        threshold=threshold,
        baseline_coverage=baseline_coverage,
        regression_amount=regression_amount,
        message=message,
    )

    logger.info("Coverage enforcement finished: %s.", status)
    logger.debug("Enforcement result: %s", result)

    return result
