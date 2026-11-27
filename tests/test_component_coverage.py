import pytest

from src.component_coverage import (
    evaluate_component_coverage,
    parse_component_thresholds,
)


def test_parse_component_thresholds():
    thresholds = parse_component_thresholds(
        '{"src/api/": 90, "src/database/": 85, "src/file.py": 95}'
    )

    assert len(thresholds) == 3
    assert thresholds[0].path == "src/api"
    assert thresholds[0].threshold == 90
    assert thresholds[0].is_directory is True
    assert thresholds[2].is_directory is False


def test_empty_configuration_returns_no_thresholds():
    assert parse_component_thresholds("") == []


@pytest.mark.parametrize(
    "configuration",
    [
        "not-json",
        "[]",
        '"src": 80',
        '{"src/": "80"}',
        '{"src/": true}',
        '{"src/": -1}',
        '{"src/": 101}',
        '{"src/": NaN}',
        '{"../outside/": 80}',
        '{"/absolute/path/": 80}',
        '{"src//api/": 80}',
        '{"src/./api/": 80}',
    ],
)
def test_invalid_component_configuration_raises_error(configuration):
    with pytest.raises(ValueError):
        parse_component_thresholds(configuration)


def test_nested_component_uses_most_specific_threshold():
    thresholds = parse_component_thresholds('{"src/": 50, "src/api/": 90}')
    line_coverage = {
        "src/api/routes.py": {1: True, 2: False},
        "src/models.py": {1: True, 2: True},
    }

    results = evaluate_component_coverage(line_coverage, thresholds)

    assert results[0].total_lines == 2
    assert results[0].covered_lines == 2
    assert results[0].coverage == 100
    assert results[0].passed is True

    assert results[1].total_lines == 2
    assert results[1].covered_lines == 1
    assert results[1].coverage == 50
    assert results[1].passed is False


def test_exact_file_component_matches_only_that_file():
    thresholds = parse_component_thresholds('{"tests/test_parser.py": 90}')
    line_coverage = {
        "tests/test_parser.py": {1: True, 2: False},
        "tests/test_other.py": {1: True},
    }

    results = evaluate_component_coverage(line_coverage, thresholds)

    assert len(results) == 1
    assert results[0].files == ["tests/test_parser.py"]
    assert results[0].coverage == 50
    assert results[0].passed is False


def test_component_coverage_is_weighted_by_executable_lines():
    thresholds = parse_component_thresholds('{"src/": 70}')
    line_coverage = {
        "src/short.py": {1: True},
        "src/long.py": {
            1: False,
            2: False,
            3: False,
            4: True,
            5: True,
            6: True,
            7: True,
            8: True,
            9: True,
        },
    }

    results = evaluate_component_coverage(line_coverage, thresholds)

    assert results[0].total_lines == 10
    assert results[0].covered_lines == 7
    assert results[0].coverage == 70
    assert results[0].passed is True


def test_unmatched_component_fails_instead_of_passing():
    thresholds = parse_component_thresholds('{"src/api/": 80}')
    line_coverage = {
        "src/models.py": {1: True, 2: True},
    }

    results = evaluate_component_coverage(line_coverage, thresholds)

    assert results[0].coverage is None
    assert results[0].passed is False
    assert results[0].total_lines == 0
    assert "No executable coverage lines" in results[0].message


def test_component_results_include_files_and_line_counts():
    thresholds = parse_component_thresholds('{"src/": 60}')
    line_coverage = {
        "src/a.py": {1: True, 2: False},
        "src/b.py": {1: True, 2: True},
    }

    results = evaluate_component_coverage(line_coverage, thresholds)

    assert results[0].files == ["src/a.py", "src/b.py"]
    assert results[0].total_lines == 4
    assert results[0].covered_lines == 3
    assert results[0].coverage == 75
    assert results[0].passed is True


def test_directory_rule_does_not_match_similar_prefix():
    thresholds = parse_component_thresholds('{"src/api/": 80}')
    line_coverage = {
        "src/api_client.py": {1: True},
    }

    results = evaluate_component_coverage(line_coverage, thresholds)

    assert results[0].coverage is None
    assert results[0].passed is False
