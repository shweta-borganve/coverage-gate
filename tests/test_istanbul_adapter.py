import pytest

from src.istanbul_adapter import parse_istanbul
from src.parser import CoverageMetrics


def test_parse_istanbul_returns_coverage_metrics():
    result = parse_istanbul("tests/fixtures/sample_istanbul.json")

    assert isinstance(result, CoverageMetrics)
    assert result.total_coverage == pytest.approx(60.0)
    assert result.file_coverage == {
        "/project/src/app.js": pytest.approx(200 / 3),
        "/project/src/utils.js": pytest.approx(50.0),
    }
