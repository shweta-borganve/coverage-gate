import os
import shutil
import subprocess
from pathlib import Path

import pytest

from docker.entrypoint import resolve_coverage_path

ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT_DIR / "src"
DOCKER_DIR = ROOT_DIR / "docker"
DOCKER_SOURCE_DIR = DOCKER_DIR / "src"
DOCKER_ENTRYPOINT = DOCKER_DIR / "entrypoint.py"
SAMPLE_REPORT = ROOT_DIR / "tests" / "fixtures" / "sample.xml"


@pytest.fixture
def docker_cli():
    """Return Docker CLI when a working Docker daemon is available."""
    if shutil.which("docker") is None:
        pytest.skip("Docker CLI is not installed.")

    result = subprocess.run(
        ["docker", "info"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        pytest.skip("Docker daemon is not available.")

    return "docker"


def test_docker_source_is_not_duplicated():
    assert SOURCE_DIR.is_dir()
    assert not DOCKER_SOURCE_DIR.exists()


def test_dockerfile_uses_root_source_directory():
    dockerfile = DOCKER_DIR / "Dockerfile"
    dockerfile_text = dockerfile.read_text(encoding="utf-8")

    assert "COPY requirements.txt ./requirements.txt" in dockerfile_text
    assert "COPY src/ ./src/" in dockerfile_text
    assert "COPY docker/entrypoint.py ./entrypoint.py" in dockerfile_text
    assert "requirements-dev.txt" not in dockerfile_text


def test_docker_entrypoint_is_available():
    dockerfile = DOCKER_DIR / "Dockerfile"
    dockerfile_text = dockerfile.read_text(encoding="utf-8")

    assert DOCKER_ENTRYPOINT.is_file()
    assert 'ENTRYPOINT ["python", "/app/entrypoint.py"]' in dockerfile_text


def test_docker_action_metadata_is_configured():
    action_file = DOCKER_DIR / "action.yml"
    action_text = action_file.read_text(encoding="utf-8")

    assert "using: 'composite'" in action_text
    assert "id: run-docker" in action_text
    assert "docker build" in action_text
    assert '"$GITHUB_ACTION_PATH/.."' in action_text
    assert '"$GITHUB_WORKSPACE:/github/workspace"' in action_text

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


def test_docker_action_works_with_external_consumer_workspace(
    docker_cli,
    tmp_path,
):
    consumer_workspace = tmp_path / "consumer-repository"
    consumer_workspace.mkdir()

    shutil.copy2(
        SAMPLE_REPORT,
        consumer_workspace / "coverage.xml",
    )

    output_file = consumer_workspace / "github_output"
    summary_file = consumer_workspace / "github_summary"

    image_tag = f"coverage-gate-external-consumer:{os.getpid()}"

    try:
        build_result = subprocess.run(
            [
                docker_cli,
                "build",
                "--file",
                str(DOCKER_DIR / "Dockerfile"),
                "--tag",
                image_tag,
                str(DOCKER_DIR.parent),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert build_result.returncode == 0, (
            "Docker image build failed.\n"
            f"stdout:\n{build_result.stdout}\n"
            f"stderr:\n{build_result.stderr}"
        )

        run_result = subprocess.run(
            [
                docker_cli,
                "run",
                "--rm",
                "--volume",
                f"{consumer_workspace}:/github/workspace",
                "--env",
                "GITHUB_WORKSPACE=/github/workspace",
                "--env",
                "GITHUB_OUTPUT=/github/workspace/github_output",
                "--env",
                "GITHUB_STEP_SUMMARY=/github/workspace/github_summary",
                "--env",
                "INPUT_COVERAGE-FILE=coverage.xml",
                "--env",
                "INPUT_THRESHOLD=80",
                "--env",
                "INPUT_CHANGED-LINES-THRESHOLD=0",
                "--env",
                "INPUT_WARNING-MARGIN=5",
                "--env",
                "INPUT_BASELINE-COVERAGE=",
                "--env",
                "INPUT_MAX-REGRESSION=5",
                "--env",
                "INPUT_ENABLE-COVERAGE-BADGE=false",
                "--env",
                "INPUT_BADGE-OUTPUT-PATH=coverage-badge.svg",
                "--env",
                "LOG_LEVEL=INFO",
                image_tag,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert run_result.returncode == 0, (
            "Docker action execution failed.\n"
            f"stdout:\n{run_result.stdout}\n"
            f"stderr:\n{run_result.stderr}"
        )

        assert output_file.is_file()
        output_text = output_file.read_text(encoding="utf-8")

        assert "coverage=85.0" in output_text
        assert "changed-lines-coverage=" in output_text
        assert "changed-lines-passed=true" in output_text
        assert "passed=true" in output_text

        assert summary_file.is_file()
        assert summary_file.read_text(encoding="utf-8").strip()

    finally:
        subprocess.run(
            [docker_cli, "image", "rm", "--force", image_tag],
            capture_output=True,
            text=True,
            check=False,
        )


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
