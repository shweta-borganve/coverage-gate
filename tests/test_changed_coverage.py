from src.changed_coverage import generate_changed_coverage_report


def test_report_ranks_files_by_uncovered_changed_lines():
    changed_lines = {
        "src/parser.py": {10, 11, 12},
        "src/main.py": {20, 21},
    }
    line_coverage = {
        "src/parser.py": {10: True, 11: False, 12: False},
        "src/main.py": {20: False, 21: False},
    }

    report = generate_changed_coverage_report(changed_lines, line_coverage)

    assert report.available is True
    assert [item.filename for item in report.files] == [
        "src/main.py",
        "src/parser.py",
    ]
    assert report.files[0].uncovered_lines == 2
    assert report.files[1].uncovered_lines == 2


def test_report_counts_covered_and_uncovered_lines():
    report = generate_changed_coverage_report(
        {"src/main.py": {10, 11, 12}},
        {"src/main.py": {10: True, 11: False, 12: True}},
    )

    result = report.files[0]

    assert result.changed_lines == 3
    assert result.covered_lines == 2
    assert result.uncovered_lines == 1


def test_report_is_unavailable_when_line_data_is_missing():
    report = generate_changed_coverage_report(
        {"src/main.py": {10}},
        None,
    )

    assert report.available is False
    assert "not available" in report.message.lower()


def test_report_is_unavailable_when_file_data_is_missing():
    report = generate_changed_coverage_report(
        {"src/main.py": {10}},
        {},
    )

    assert report.available is False
    assert "not available" in report.message.lower()


def test_report_with_no_changed_lines():
    report = generate_changed_coverage_report({}, {})

    assert report.available is True
    assert report.files == []


def test_report_lists_exact_uncovered_line_numbers():
    report = generate_changed_coverage_report(
        {"src/parser.py": {10, 11, 12, 13}},
        {
            "src/parser.py": {
                10: True,
                11: False,
                12: True,
                13: False,
            }
        },
    )

    result = report.files[0]

    assert result.uncovered_line_numbers == [11, 13]
    assert result.covered_lines == 2
    assert result.uncovered_lines == 2


def test_report_is_unavailable_when_changed_line_data_is_missing():
    report = generate_changed_coverage_report(
        {"src/parser.py": {10, 11, 12}},
        {"src/parser.py": {10: True, 11: False}},
    )

    assert report.available is False
    assert "not available" in report.message.lower()
    assert "12" in report.message
