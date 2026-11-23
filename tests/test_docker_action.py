from pathlib import Path

import pytest

from docker.entrypoint import resolve_coverage_path

ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT_DIR / "src"
DOCKER_DIR = ROOT_DIR / "docker"
DOCKER_SOURCE_DIR = DOCKER_DIR / "src"


def test_docker_source_is_not_duplicated():
    assert SOURCE_DIR.is_dir()
    assert not DOCKER_SOURCE_DIR.exists()


def test_dockerfile_uses_root_source_directory():
    dockerfile = DOCKER_DIR / "Dockerfile"
    dockerfile_text = dockerfile.read_text(encoding="utf-8")

    assert "COPY src/ ./src/" in dockerfile_text
    assert "COPY docker/entrypoint.py ./entrypoint.py" in dockerfile_text


def test_docker_action_metadata_is_configured():
    action_file = DOCKER_DIR / "action.yml"
    action_text = action_file.read_text(encoding="utf-8")

    assert "using: 'composite'" in action_text
    assert "id: run-docker" in action_text
    assert "docker build" in action_text
    assert '"$GITHUB_WORKSPACE"' in action_text

    assert "LOG_LEVEL: ${{ env.LOG_LEVEL || 'INFO' }}" in action_text
    assert "--env LOG_LEVEL" in action_text

    for input_name in (
        "coverage-file:",
        "threshold:",
        "changed-lines-threshold:",
        "warning-margin:",
        "baseline-coverage:",
        "max-regression:",
        "enable-coverage-badge:",
        "badge-output-path:",
    ):
        assert input_name in action_text

    for output_name in (
        "coverage:",
        "changed-lines-coverage:",
        "changed-lines-passed:",
        "passed:",
    ):
        assert output_name in action_text


def test_resolve_coverage_path_rejects_parent_directory(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(
        ValueError,
        match="coverage-file must point to a file inside GITHUB_WORKSPACE",
    ):
        resolve_coverage_path(workspace, "../coverage.xml")


def test_resolve_coverage_path_rejects_external_absolute_path(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    outside_file = tmp_path / "coverage.xml"

    with pytest.raises(
        ValueError,
        match="coverage-file must point to a file inside GITHUB_WORKSPACE",
    ):
        resolve_coverage_path(workspace, str(outside_file))


def test_resolve_coverage_path_rejects_symlink_outside_workspace(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    outside_file = tmp_path / "coverage.xml"
    outside_file.write_text("<coverage />", encoding="utf-8")

    symlink = workspace / "coverage-link.xml"
    symlink.symlink_to(outside_file)

    with pytest.raises(
        ValueError,
        match="coverage-file must point to a file inside GITHUB_WORKSPACE",
    ):
        resolve_coverage_path(workspace, "coverage-link.xml")
