import sys

from src.main import main


def test_main_uses_default_warning_margin(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "tests/fixtures/sample.xml",
            "80",
        ],
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 0
    assert "WARNING: Coverage is within 5.0% of the threshold." in captured.out


def test_main_uses_custom_warning_margin(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "tests/fixtures/sample.xml",
            "80",
            "10",
        ],
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 0
    assert "WARNING: Coverage is within 10.0% of the threshold." in captured.out


def test_main_invalid_threshold(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "tests/fixtures/sample.xml",
            "invalid",
        ],
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "Invalid threshold: invalid" in captured.out


def test_main_invalid_warning_margin(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "tests/fixtures/sample.xml",
            "80",
            "invalid",
        ],
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "Invalid warning margin: invalid" in captured.out


def test_main_missing_arguments(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py"],
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "Usage:" in captured.out


def test_main_fails_when_coverage_is_below_threshold(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "tests/fixtures/sample.xml",
            "90",
        ],
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "FAIL" in captured.out


def test_main_uses_baseline_and_max_regression(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "tests/fixtures/sample.xml",
            "80",
            "5",
            "90",
            "5",
        ],
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 0
    assert "Coverage 85.0% vs threshold 80.0% — PASS" in captured.out


def test_main_fails_when_regression_exceeds_limit(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "tests/fixtures/sample.xml",
            "80",
            "5",
            "95",
            "5",
        ],
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "REGRESSION" in captured.out
    assert "Coverage 85.0% vs threshold 80.0% — FAIL" in captured.out


def test_main_invalid_baseline_coverage(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "tests/fixtures/sample.xml",
            "80",
            "5",
            "invalid",
            "5",
        ],
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "Invalid baseline coverage: invalid" in captured.out


def test_main_invalid_max_regression(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "tests/fixtures/sample.xml",
            "80",
            "5",
            "90",
            "invalid",
        ],
    )

    result = main()

    captured = capsys.readouterr()

    assert result == 1
    assert "Invalid max regression: invalid" in captured.out
