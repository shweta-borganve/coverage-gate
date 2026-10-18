from pathlib import Path

ACTION_FILE = Path(__file__).resolve().parents[1] / "action.yml"


def test_action_uses_summary_generator():
    action = ACTION_FILE.read_text(encoding="utf-8")

    assert "from src.summary import generate_summary" in action
    assert "from src.changed_lines import parse_changed_lines" in action
    assert "from src.changed_coverage import" in action
    assert "parse_line_coverage" in action
    assert "generate_summary(" in action
    assert "metrics.file_coverage," in action
    assert "changed_coverage," in action


def test_action_summary_is_optional_for_local_execution():
    action = ACTION_FILE.read_text(encoding="utf-8")

    assert 'summary_path = os.environ.get("GITHUB_STEP_SUMMARY")' in action
    assert "if summary_path:" in action


def test_action_writes_summary_before_failing():
    action = ACTION_FILE.read_text(encoding="utf-8")

    summary_position = action.index("generate_summary(")
    failure_position = action.index("if not result.passed:")

    assert summary_position < failure_position


def test_changed_coverage_does_not_add_a_failure_condition():
    action = ACTION_FILE.read_text(encoding="utf-8")

    assert "if not result.passed:" in action
    assert "if not changed_coverage.available:" not in action
    assert "raise SystemExit(1)" in action
