from pathlib import Path

feature/add-coverage-report-parser

import pytest

from docker.entrypoint import resolve_coverage_path

main
ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT_DIR / "src"
DOCKER_SOURCE_DIR = ROOT_DIR / "docker" / "src"


def test_docker_source_modules_match_original_modules():
    source_modules = {
        path.name for path in SOURCE_DIR.glob("*.py") if path.name != "main.py"
    }
    docker_modules = {path.name for path in DOCKER_SOURCE_DIR.glob("*.py")}

    assert docker_modules == source_modules

    for module_name in sorted(source_modules):
        original = (SOURCE_DIR / module_name).read_bytes()
        docker_copy = (DOCKER_SOURCE_DIR / module_name).read_bytes()

        assert (
            docker_copy == original
        ), f"docker/src/{module_name} differs from src/{module_name}"


def test_docker_action_metadata_is_configured():
    action_file = ROOT_DIR / "docker" / "action.yml"
    action_text = action_file.read_text(encoding="utf-8")

    assert "using: 'docker'" in action_text
    assert "image: 'Dockerfile'" in action_text
    assert "coverage-file:" in action_text
    assert "threshold:" in action_text
    assert "warning-margin:" in action_text
    assert "baseline-coverage:" in action_text
    assert "max-regression:" in action_text
    assert "coverage:" in action_text
feature/add-coverage-report-parser



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
main
