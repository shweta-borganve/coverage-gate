import pytest

from src.parser import parse_lcov, parse_line_coverage


def test_parse_lcov_merges_repeated_source_records(tmp_path):
    coverage_file = tmp_path / "coverage.info"
    coverage_file.write_text(
        """TN:first
SF:src/main.py
DA:1,0
DA:2,0
LF:2
LH:0
end_of_record
TN:second
SF:src/main.py
DA:1,1
DA:3,1
LF:2
LH:2
end_of_record
""",
        encoding="utf-8",
    )

    metrics = parse_lcov(coverage_file)

    assert metrics.total_coverage == 66.66666666666666
    assert metrics.file_coverage == {"src/main.py": 66.66666666666666}


def test_parse_lcov_line_coverage_merges_repeated_source_records(tmp_path):
    coverage_file = tmp_path / "coverage.info"
    coverage_file.write_text(
        """TN:first
SF:src/main.py
DA:1,0
DA:2,0
end_of_record
TN:second
SF:src/main.py
DA:1,1
DA:3,1
end_of_record
""",
        encoding="utf-8",
    )

    result = parse_line_coverage(str(coverage_file))

    assert result == {"src/main.py": {1: True, 2: False, 3: True}}


def test_parse_lcov_rejects_mixed_detailed_and_summary_only_records(tmp_path):
    coverage_file = tmp_path / "coverage.info"
    coverage_file.write_text(
        """TN:detailed
SF:src/main.py
DA:1,1
DA:2,0
LF:2
LH:1
end_of_record
TN:summary
SF:src/main.py
LF:2
LH:2
end_of_record
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Ambiguous LCOV records"):
        parse_lcov(coverage_file)


def test_parse_lcov_rejects_repeated_summary_only_records(tmp_path):
    coverage_file = tmp_path / "coverage.info"
    coverage_file.write_text(
        """TN:first
SF:src/main.py
LF:2
LH:1
end_of_record
TN:second
SF:src/main.py
LF:2
LH:2
end_of_record
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Ambiguous LCOV records"):
        parse_lcov(coverage_file)
