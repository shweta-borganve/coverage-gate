from src.parser import parse_cobertura


def test_parse():
    metrics = parse_cobertura("tests/fixtures/sample.xml")
    assert metrics.total_coverage == 85.0
