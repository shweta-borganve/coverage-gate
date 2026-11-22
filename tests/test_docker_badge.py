from docker import entrypoint


def test_docker_badge_generates_default_output(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    monkeypatch.setenv("INPUT_ENABLE-COVERAGE-BADGE", "true")

    entrypoint.generate_coverage_badge(workspace, 85.5)

    badge_path = workspace / "coverage-badge.svg"

    assert badge_path.is_file()
    assert "85.5%" in badge_path.read_text(encoding="utf-8")


def test_docker_badge_generates_custom_nested_output(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    monkeypatch.setenv("INPUT_ENABLE-COVERAGE-BADGE", "true")
    monkeypatch.setenv("INPUT_BADGE-OUTPUT-PATH", "reports/coverage.svg")

    entrypoint.generate_coverage_badge(workspace, 92.0)

    badge_path = workspace / "reports" / "coverage.svg"

    assert badge_path.is_file()
    assert "92.0%" in badge_path.read_text(encoding="utf-8")


def test_docker_badge_is_disabled_by_default(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    monkeypatch.delenv("INPUT_ENABLE-COVERAGE-BADGE", raising=False)

    entrypoint.generate_coverage_badge(workspace, 85.0)

    assert not (workspace / "coverage-badge.svg").exists()


def test_docker_badge_rejects_path_outside_workspace(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    monkeypatch.setenv("INPUT_ENABLE-COVERAGE-BADGE", "true")
    monkeypatch.setenv("INPUT_BADGE-OUTPUT-PATH", "../outside.svg")

    entrypoint.generate_coverage_badge(workspace, 85.0)

    assert not (tmp_path / "outside.svg").exists()


def test_docker_badge_rejects_symlink_escape(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    outside_file = tmp_path / "outside.svg"
    symlink = workspace / "badge.svg"
    symlink.symlink_to(outside_file)

    monkeypatch.setenv("INPUT_ENABLE-COVERAGE-BADGE", "true")
    monkeypatch.setenv("INPUT_BADGE-OUTPUT-PATH", "badge.svg")

    entrypoint.generate_coverage_badge(workspace, 85.0)

    assert not outside_file.exists()


def test_docker_badge_generation_failure_does_not_raise(
    monkeypatch,
    tmp_path,
):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    monkeypatch.setenv("INPUT_ENABLE-COVERAGE-BADGE", "true")

    def fail_generation(coverage, output_path):
        raise OSError("Simulated file error")

    monkeypatch.setattr(entrypoint, "generate_badge", fail_generation)

    entrypoint.generate_coverage_badge(workspace, 85.0)
