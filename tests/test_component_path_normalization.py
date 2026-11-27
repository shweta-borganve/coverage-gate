from src.component_coverage import (
    evaluate_component_coverage,
    parse_component_thresholds,
)


def test_component_matching_accepts_windows_style_paths():
    thresholds = parse_component_thresholds('{"src/api/": 80}')
    line_coverage = {
        r"src\api\service.py": {
            1: True,
            2: True,
        }
    }

    results = evaluate_component_coverage(line_coverage, thresholds)

    assert results[0].files == [r"src\api\service.py"]
    assert results[0].coverage == 100
    assert results[0].passed is True


def test_component_matching_accepts_leading_dot_slash():
    thresholds = parse_component_thresholds('{"src/api/": 80}')
    line_coverage = {
        "./src/api/service.py": {
            1: True,
            2: False,
        }
    }

    results = evaluate_component_coverage(line_coverage, thresholds)

    assert results[0].files == ["./src/api/service.py"]
    assert results[0].coverage == 50
    assert results[0].passed is False
