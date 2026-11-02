from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
ACTION_FILE = ROOT_DIR / "action.yml"
MAIN_FILE = ROOT_DIR / "src" / "main.py"


def test_action_runs_existing_main_module():
    action = ACTION_FILE.read_text(encoding="utf-8")

    assert "python -m src.main --github-action" in action
    assert "python - <<'PY'" not in action


def test_main_uses_summary_and_changed_coverage_helpers():
    main = MAIN_FILE.read_text(encoding="utf-8")

    assert "from src.summary import generate_summary" in main
    assert "from src.changed_lines import parse_changed_lines" in main
    assert "from src.changed_coverage import" in main
    assert "parse_line_coverage" in main
    assert "generate_summary(" in main
    assert "metrics.file_coverage," in main
    assert "changed_coverage," in main


def test_action_summary_is_optional_for_local_execution():
    main = MAIN_FILE.read_text(encoding="utf-8")

    assert 'summary_path = os.environ.get("GITHUB_STEP_SUMMARY")' in main
    assert "if summary_path:" in main


def test_action_writes_summary_before_failing():
    main = MAIN_FILE.read_text(encoding="utf-8")

    summary_position = main.index("generate_summary(")
    failure_position = main.index("if not result.passed:")

    assert summary_position < failure_position


def test_changed_coverage_does_not_add_a_failure_condition():
    main = MAIN_FILE.read_text(encoding="utf-8")

    assert "if not result.passed:" in main
    assert "if not changed_coverage.available:" not in main
    assert "return 1" in main
