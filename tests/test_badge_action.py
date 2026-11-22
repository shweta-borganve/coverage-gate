import src.main as main_module
from src.main import main
from tests.test_main import configure_action_environment


def test_action_generates_badge_when_enabled(monkeypatch, tmp_path):
    workspace, _, _, _ = configure_action_environment(monkeypatch, tmp_path)
    monkeypatch.setenv("ENABLE_COVERAGE_BADGE", "true")

    result = main()

    badge_path = workspace / "coverage-badge.svg"

    assert result == 0
    assert badge_path.is_file()
    assert "85.0%" in badge_path.read_text(encoding="utf-8")


def test_action_generates_badge_at_custom_nested_path(monkeypatch, tmp_path):
    workspace, _, _, _ = configure_action_environment(monkeypatch, tmp_path)
    monkeypatch.setenv("ENABLE_COVERAGE_BADGE", "true")
    monkeypatch.setenv("BADGE_OUTPUT_PATH", "reports/badges/coverage.svg")

    result = main()

    badge_path = workspace / "reports" / "badges" / "coverage.svg"

    assert result == 0
    assert badge_path.is_file()
    assert "85.0%" in badge_path.read_text(encoding="utf-8")


def test_action_does_not_generate_badge_by_default(monkeypatch, tmp_path):
    workspace, _, _, _ = configure_action_environment(monkeypatch, tmp_path)
    monkeypatch.delenv("ENABLE_COVERAGE_BADGE", raising=False)

    generate_calls = []
    monkeypatch.setattr(
        main_module,
        "generate_badge",
        lambda *args: generate_calls.append(args),
    )

    result = main()

    assert result == 0
    assert generate_calls == []
    assert not (workspace / "coverage-badge.svg").exists()


def test_action_rejects_badge_path_outside_workspace(monkeypatch, tmp_path):
    workspace, _, _, _ = configure_action_environment(monkeypatch, tmp_path)
    monkeypatch.setenv("ENABLE_COVERAGE_BADGE", "true")
    monkeypatch.setenv("BADGE_OUTPUT_PATH", "../outside.svg")

    generate_calls = []
    monkeypatch.setattr(
        main_module,
        "generate_badge",
        lambda *args: generate_calls.append(args),
    )

    result = main()

    assert result == 0
    assert generate_calls == []
    assert not (workspace.parent / "outside.svg").exists()


def test_action_rejects_badge_symlink_outside_workspace(monkeypatch, tmp_path):
    workspace, _, _, _ = configure_action_environment(monkeypatch, tmp_path)
    outside_file = workspace.parent / f"{workspace.name}-outside.svg"
    symlink = workspace / "badge-link.svg"
    symlink.symlink_to(outside_file)

    monkeypatch.setenv("ENABLE_COVERAGE_BADGE", "true")
    monkeypatch.setenv("BADGE_OUTPUT_PATH", "badge-link.svg")

    generate_calls = []
    monkeypatch.setattr(
        main_module,
        "generate_badge",
        lambda *args: generate_calls.append(args),
    )

    result = main()

    assert result == 0
    assert generate_calls == []
    assert not outside_file.exists()


def test_badge_generation_failure_does_not_fail_action(monkeypatch, tmp_path):
    configure_action_environment(monkeypatch, tmp_path)
    monkeypatch.setenv("ENABLE_COVERAGE_BADGE", "true")

    def fail_generation(*_args):
        raise OSError("Unable to write badge")

    monkeypatch.setattr(main_module, "generate_badge", fail_generation)

    result = main()

    assert result == 0


def test_badge_is_generated_when_coverage_threshold_fails(monkeypatch, tmp_path):
    workspace, _, _, _ = configure_action_environment(
        monkeypatch,
        tmp_path,
        threshold="90",
    )
    monkeypatch.setenv("ENABLE_COVERAGE_BADGE", "true")

    result = main()

    badge_path = workspace / "coverage-badge.svg"

    assert result == 1
    assert badge_path.is_file()
    assert "85.0%" in badge_path.read_text(encoding="utf-8")
