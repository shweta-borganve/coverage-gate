import io
import json
import zipfile

import pytest

from src import coverage_trend


def make_record(
    coverage=85.0,
    branch="main",
    commit_sha="abc123",
    run_id="100",
    run_number=10,
    workflow_ref="owner/repo/.github/workflows/ci.yml@refs/heads/main",
    recorded_at="2026-11-20T10:00:00+00:00",
):
    return coverage_trend.create_history_record(
        coverage=coverage,
        branch=branch,
        commit_sha=commit_sha,
        run_id=run_id,
        run_number=run_number,
        workflow_ref=workflow_ref,
        recorded_at=recorded_at,
    )


def make_artifact_zip(record):
    """Create an in-memory artifact ZIP containing a history record."""
    archive_buffer = io.BytesIO()

    with zipfile.ZipFile(archive_buffer, "w") as archive:
        archive.writestr(
            coverage_trend.ARTIFACT_FILENAME,
            json.dumps(record),
        )

    return archive_buffer.getvalue()


def make_artifact(record, run_id="100", branch="main", commit_sha="abc123"):
    return {
        "name": coverage_trend.DEFAULT_ARTIFACT_NAME,
        "expired": False,
        "archive_download_url": "https://example.com/artifact.zip",
        "created_at": "2026-11-20T10:00:00Z",
        "workflow_run": {
            "id": int(run_id),
            "head_branch": branch,
            "head_sha": commit_sha,
        },
        "record": record,
    }


def test_create_history_record():
    record = make_record()

    assert record["schema_version"] == 1
    assert record["coverage"] == 85.0
    assert record["branch"] == "main"
    assert record["commit_sha"] == "abc123"
    assert record["run_id"] == "100"
    assert record["run_number"] == 10
    assert record["workflow_path"] == "owner/repo/.github/workflows/ci.yml"
    assert record["recorded_at"] == "2026-11-20T10:00:00+00:00"


@pytest.mark.parametrize(
    "coverage",
    [-1, 101, float("nan"), float("inf"), True, "85"],
)
def test_create_history_record_rejects_invalid_coverage(coverage):
    with pytest.raises(ValueError, match="invalid coverage"):
        make_record(coverage=coverage)


def test_validate_history_record_rejects_non_dictionary():
    with pytest.raises(TypeError, match="JSON object"):
        coverage_trend.validate_history_record([])


def test_validate_history_record_rejects_unsupported_schema():
    record = make_record()
    record["schema_version"] = 2

    with pytest.raises(ValueError, match="schema version"):
        coverage_trend.validate_history_record(record)


def test_validate_history_record_rejects_missing_required_fields():
    record = make_record()
    del record["branch"]

    with pytest.raises(ValueError, match="branch"):
        coverage_trend.validate_history_record(record)


def test_validate_history_record_rejects_invalid_run_number():
    record = make_record()
    record["run_number"] = -1

    with pytest.raises(ValueError, match="run number"):
        coverage_trend.validate_history_record(record)


def test_write_history_record(tmp_path):
    record = make_record()
    output_path = tmp_path / "history" / "record.json"

    coverage_trend.write_history_record(record, output_path)

    saved_record = json.loads(output_path.read_text(encoding="utf-8"))

    assert saved_record == record


def test_read_artifact_record():
    record = make_record()
    archive_data = make_artifact_zip(record)

    result = coverage_trend._read_artifact_record(archive_data)

    assert result == record


def test_read_artifact_record_rejects_missing_file():
    archive_buffer = io.BytesIO()

    with zipfile.ZipFile(archive_buffer, "w") as archive:
        archive.writestr("other.json", "{}")

    with pytest.raises(ValueError, match="exactly one"):
        coverage_trend._read_artifact_record(archive_buffer.getvalue())


def test_read_artifact_record_rejects_oversized_file():
    archive_buffer = io.BytesIO()

    with zipfile.ZipFile(archive_buffer, "w") as archive:
        archive.writestr(
            coverage_trend.ARTIFACT_FILENAME,
            "x" * (coverage_trend.MAX_RECORD_SIZE + 1),
        )

    with pytest.raises(ValueError, match="size limit"):
        coverage_trend._read_artifact_record(archive_buffer.getvalue())


def test_calculate_trend_when_coverage_improves():
    history = [
        make_record(coverage=80.0),
        make_record(coverage=82.0, run_id="101"),
    ]

    trend = coverage_trend.calculate_trend(85.0, history)

    assert trend["available"] is True
    assert trend["direction"] == "improved"
    assert trend["previous_coverage"] == 82.0
    assert trend["change"] == 3.0
    assert trend["history"] == [80.0, 82.0, 85.0]


def test_calculate_trend_when_coverage_declines():
    history = [make_record(coverage=90.0)]

    trend = coverage_trend.calculate_trend(85.0, history)

    assert trend["direction"] == "declined"
    assert trend["change"] == -5.0
    assert "declined" in trend["message"]


def test_calculate_trend_when_coverage_is_unchanged():
    history = [make_record(coverage=85.0)]

    trend = coverage_trend.calculate_trend(85.0, history)

    assert trend["direction"] == "unchanged"
    assert trend["change"] == 0.0
    assert "unchanged" in trend["message"]


def test_calculate_trend_without_history():
    trend = coverage_trend.calculate_trend(85.0, [])

    assert trend["available"] is False
    assert trend["direction"] == "no-history"
    assert trend["previous_coverage"] is None
    assert trend["change"] is None
    assert trend["history"] == [85.0]


@pytest.mark.parametrize("coverage", [-1, 101, float("nan"), True, "85"])
def test_calculate_trend_rejects_invalid_current_coverage(coverage):
    with pytest.raises(ValueError, match="Current coverage"):
        coverage_trend.calculate_trend(coverage, [])


def test_get_coverage_trend_skips_when_token_is_missing(caplog):
    trend = coverage_trend.get_coverage_trend(
        token="",
        repository="owner/repo",
        branch="main",
        commit_sha="abc123",
        current_run_id="200",
        workflow_ref="owner/repo/.github/workflows/ci.yml@refs/heads/main",
        current_coverage=85.0,
    )

    assert trend["available"] is False
    assert trend["direction"] == "unavailable"
    assert "token is unavailable" in caplog.text


def test_get_coverage_trend_skips_when_metadata_is_missing():
    trend = coverage_trend.get_coverage_trend(
        token="test-token",
        repository="owner/repo",
        branch="",
        commit_sha="abc123",
        current_run_id="200",
        workflow_ref="owner/repo/.github/workflows/ci.yml@refs/heads/main",
        current_coverage=85.0,
    )

    assert trend["available"] is False


def test_get_coverage_trend_handles_api_failure(monkeypatch, caplog):
    def fail_request(*_args, **_kwargs):
        raise OSError("GitHub API unavailable")

    monkeypatch.setattr(coverage_trend, "_github_request", fail_request)

    trend = coverage_trend.get_coverage_trend(
        token="test-token",
        repository="owner/repo",
        branch="main",
        commit_sha="new-sha",
        current_run_id="200",
        workflow_ref="owner/repo/.github/workflows/ci.yml@refs/heads/main",
        current_coverage=85.0,
    )

    assert trend["available"] is False
    assert "GitHub API unavailable" in caplog.text


def test_get_coverage_trend_uses_matching_branch_and_workflow(monkeypatch):
    matching_record = make_record()
    wrong_branch_record = make_record(
        branch="feature/example",
        run_id="101",
    )
    wrong_workflow_record = make_record(
        run_id="102",
        workflow_ref="owner/repo/.github/workflows/other.yml@refs/heads/main",
    )

    artifacts = [
        make_artifact(matching_record),
        make_artifact(
            wrong_branch_record,
            run_id="101",
            branch="feature/example",
        ),
        make_artifact(wrong_workflow_record, run_id="102"),
    ]

    def fake_request(url, _token):
        if url.endswith(
            "/actions/artifacts?name=coverage-gate-history&per_page=100&page=1"
        ):
            return json.dumps({"artifacts": artifacts}).encode("utf-8")

        for artifact in artifacts:
            if artifact["archive_download_url"] == url:
                return make_artifact_zip(artifact["record"])

        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(coverage_trend, "_github_request", fake_request)

    trend = coverage_trend.get_coverage_trend(
        token="test-token",
        repository="owner/repo",
        branch="main",
        commit_sha="new-sha",
        current_run_id="200",
        workflow_ref="owner/repo/.github/workflows/ci.yml@refs/heads/main",
        current_coverage=90.0,
    )

    assert trend["available"] is True
    assert trend["previous_coverage"] == 85.0
    assert trend["change"] == 5.0
    assert trend["direction"] == "improved"


def test_get_coverage_trend_ignores_current_run(monkeypatch):
    current_record = make_record(
        run_id="200",
        commit_sha="new-sha",
    )
    artifact = make_artifact(
        current_record,
        run_id="200",
        commit_sha="new-sha",
    )

    monkeypatch.setattr(
        coverage_trend,
        "_github_request",
        lambda *_args: json.dumps({"artifacts": [artifact]}).encode("utf-8"),
    )

    trend = coverage_trend.get_coverage_trend(
        token="test-token",
        repository="owner/repo",
        branch="main",
        commit_sha="new-sha",
        current_run_id="200",
        workflow_ref="owner/repo/.github/workflows/ci.yml@refs/heads/main",
        current_coverage=85.0,
    )

    assert trend["available"] is False
    assert trend["direction"] == "no-history"


def test_get_coverage_trend_skips_expired_artifacts(monkeypatch):
    record = make_record()
    artifact = make_artifact(record)
    artifact["expired"] = True

    monkeypatch.setattr(
        coverage_trend,
        "_github_request",
        lambda *_args: json.dumps({"artifacts": [artifact]}).encode("utf-8"),
    )

    trend = coverage_trend.get_coverage_trend(
        token="test-token",
        repository="owner/repo",
        branch="main",
        commit_sha="new-sha",
        current_run_id="200",
        workflow_ref="owner/repo/.github/workflows/ci.yml@refs/heads/main",
        current_coverage=85.0,
    )

    assert trend["available"] is False
    assert trend["direction"] == "no-history"


def test_get_coverage_trend_skips_corrupt_artifact(monkeypatch, caplog):
    artifact = make_artifact(make_record())

    def fake_request(url, _token):
        if url.endswith(
            "/actions/artifacts?name=coverage-gate-history&per_page=100&page=1"
        ):
            return json.dumps({"artifacts": [artifact]}).encode("utf-8")

        return b"not a valid ZIP archive"

    monkeypatch.setattr(coverage_trend, "_github_request", fake_request)

    trend = coverage_trend.get_coverage_trend(
        token="test-token",
        repository="owner/repo",
        branch="main",
        commit_sha="new-sha",
        current_run_id="200",
        workflow_ref="owner/repo/.github/workflows/ci.yml@refs/heads/main",
        current_coverage=85.0,
    )

    assert trend["available"] is False
    assert "Skipping an invalid" in caplog.text
