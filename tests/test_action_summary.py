from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ACTION_FILE = PROJECT_ROOT / "action.yml"


def test_action_uses_summary_generator():
    action = ACTION_FILE.read_text(encoding="utf-8")

    assert "from src.summary import generate_summary" in action
    assert "summary_file.write(generate_summary(result))" in action


def test_action_summary_is_optional_for_local_execution():
    action = ACTION_FILE.read_text(encoding="utf-8")

    assert 'os.environ.get("GITHUB_STEP_SUMMARY")' in action
    assert "if summary_path:" in action


def test_action_writes_summary_before_failing():
    action = ACTION_FILE.read_text(encoding="utf-8")

    summary_position = action.index("summary_file.write(generate_summary(result))")
    failure_position = action.index("raise SystemExit(1)")

    assert summary_position < failure_position