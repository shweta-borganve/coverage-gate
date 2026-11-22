"""Retrieve and calculate branch-specific coverage history from GitHub artifacts."""

import io
import json
import math
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from src.logger_config import configure_logger

logger = configure_logger(__name__)

ARTIFACT_FILENAME = "coverage-gate-history.json"
DEFAULT_ARTIFACT_NAME = "coverage-gate-history"
HISTORY_LIMIT = 10
MAX_ARTIFACT_DOWNLOADS = 20
MAX_RECORD_SIZE = 64 * 1024
MAX_RESPONSE_SIZE = 5 * 1024 * 1024
SCHEMA_VERSION = 1


def _origin(url):
    """Return the security origin of a URL."""
    parsed = urlsplit(url)

    return (
        parsed.scheme.lower(),
        (parsed.hostname or "").lower(),
        parsed.port,
    )


class _SafeRedirectHandler(HTTPRedirectHandler):
    """Prevent credentials from being forwarded to a different origin."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected_request = super().redirect_request(
            req,
            fp,
            code,
            msg,
            headers,
            newurl,
        )

        if redirected_request is not None and _origin(req.full_url) != _origin(newurl):
            redirected_request.remove_header("Authorization")

        return redirected_request


def _workflow_path(workflow_ref):
    """Extract the workflow file path from a GitHub workflow reference."""
    if not isinstance(workflow_ref, str) or not workflow_ref.strip():
        return ""

    return workflow_ref.split("@", 1)[0]


def create_history_record(
    coverage,
    branch,
    commit_sha,
    run_id,
    run_number,
    workflow_ref,
    recorded_at=None,
):
    """Create a minimal, versioned coverage history record."""
    record = {
        "schema_version": SCHEMA_VERSION,
        "coverage": coverage,
        "branch": branch,
        "commit_sha": commit_sha,
        "run_id": str(run_id),
        "run_number": run_number,
        "workflow_path": _workflow_path(workflow_ref),
        "recorded_at": recorded_at or datetime.now(UTC).isoformat(),
    }

    validate_history_record(record)
    return record


def validate_history_record(record):
    """Validate a history record before using or writing it."""
    if not isinstance(record, dict):
        raise TypeError("History record must be a JSON object.")

    if record.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported coverage history schema version.")

    coverage = record.get("coverage")

    if (
        isinstance(coverage, bool)
        or not isinstance(coverage, (int, float))
        or not math.isfinite(coverage)
        or not 0 <= coverage <= 100
    ):
        raise ValueError("History record contains an invalid coverage value.")

    required_strings = (
        "branch",
        "commit_sha",
        "run_id",
        "workflow_path",
        "recorded_at",
    )

    for field in required_strings:
        value = record.get(field)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"History record is missing a valid {field}.")

    run_number = record.get("run_number")

    if (
        isinstance(run_number, bool)
        or not isinstance(run_number, int)
        or run_number < 0
    ):
        raise ValueError("History record contains an invalid run number.")

    return record


def write_history_record(record, output_path):
    """Write the current coverage record to the runner's temporary directory."""
    validate_history_record(record)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    logger.info("[Coverage Gate] Coverage history record created.")


def _github_request(url, token):
    """Send a bounded GitHub request without leaking credentials on redirects."""
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Coverage-Gate",
    }

    request = Request(url, headers=headers, method="GET")
    opener = build_opener(_SafeRedirectHandler())

    with opener.open(request, timeout=15) as response:
        response_data = response.read(MAX_RESPONSE_SIZE + 1)

    if len(response_data) > MAX_RESPONSE_SIZE:
        raise ValueError("GitHub response exceeds the maximum allowed size.")

    return response_data


def _read_artifact_record(archive_data):
    """Read and validate the JSON history record from an artifact ZIP archive."""
    with zipfile.ZipFile(io.BytesIO(archive_data)) as archive:
        matching_files = [
            item
            for item in archive.infolist()
            if Path(item.filename).name == ARTIFACT_FILENAME
        ]

        if len(matching_files) != 1:
            raise ValueError(
                "Artifact must contain exactly one coverage history record."
            )

        item = matching_files[0]

        if item.file_size > MAX_RECORD_SIZE:
            raise ValueError("Coverage history record exceeds the size limit.")

        record_data = archive.read(item)
        record = json.loads(record_data.decode("utf-8"))

    return validate_history_record(record)


def _load_artifact_record(artifact, token):
    """Download and read one historical artifact."""
    download_url = artifact.get("archive_download_url")

    if not isinstance(download_url, str) or not download_url:
        raise ValueError("Artifact is missing its download URL.")

    archive_data = _github_request(download_url, token)
    return _read_artifact_record(archive_data)


def calculate_trend(current_coverage, historical_records):
    """Compare current coverage with the most recent valid historical record."""
    if (
        isinstance(current_coverage, bool)
        or not isinstance(current_coverage, (int, float))
        or not math.isfinite(current_coverage)
        or not 0 <= current_coverage <= 100
    ):
        raise ValueError("Current coverage must be between 0 and 100.")

    if not historical_records:
        return {
            "available": False,
            "direction": "no-history",
            "previous_coverage": None,
            "change": None,
            "history": [current_coverage],
            "records_count": 0,
            "message": "No previous coverage history is available.",
        }

    previous_coverage = historical_records[-1]["coverage"]
    change = round(current_coverage - previous_coverage, 2)

    if change > 0:
        direction = "improved"
    elif change < 0:
        direction = "declined"
    else:
        direction = "unchanged"

    recent_records = historical_records[-4:]
    history = [record["coverage"] for record in recent_records]
    history.append(current_coverage)

    return {
        "available": True,
        "direction": direction,
        "previous_coverage": previous_coverage,
        "change": change,
        "history": history,
        "records_count": len(historical_records),
        "message": (
            f"Coverage {direction} by {abs(change):.2f} percentage points."
            if change
            else "Coverage is unchanged from the previous run."
        ),
    }


def get_coverage_trend(
    token,
    repository,
    branch,
    commit_sha,
    current_run_id,
    workflow_ref,
    current_coverage,
    api_url="https://api.github.com",
    artifact_name=DEFAULT_ARTIFACT_NAME,
):
    """Retrieve previous coverage records for the same branch and workflow."""
    unavailable = {
        "available": False,
        "direction": "unavailable",
        "previous_coverage": None,
        "change": None,
        "history": [current_coverage],
        "records_count": 0,
        "message": "Coverage history is currently unavailable.",
    }

    if not token:
        logger.warning(
            "[Coverage Gate] Coverage trend skipped: history token is unavailable."
        )
        return unavailable

    if not repository or "/" not in repository:
        logger.warning(
            "[Coverage Gate] Coverage trend skipped: repository is unavailable."
        )
        return unavailable

    workflow_path = _workflow_path(workflow_ref)

    if not branch or not commit_sha or not current_run_id or not workflow_path:
        logger.warning(
            "[Coverage Gate] Coverage trend skipped: "
            "required GitHub run metadata is unavailable."
        )
        return unavailable

    try:
        current_run_id = str(current_run_id)
        encoded_repository = quote(repository, safe="/")
        query = urlencode(
            {
                "name": artifact_name,
                "per_page": 100,
                "page": 1,
            }
        )

        artifacts_url = (
            f"{api_url.rstrip('/')}/repos/{encoded_repository}/actions/artifacts"
            f"?{query}"
        )

        response_data = _github_request(artifacts_url, token)
        response = json.loads(response_data.decode("utf-8"))

        if not isinstance(response, dict):
            raise TypeError("Unexpected response while listing artifacts.")

        artifacts = response.get("artifacts")

        if not isinstance(artifacts, list):
            raise TypeError("GitHub returned an invalid artifact list.")

        candidates = []

        for artifact in artifacts:
            if not isinstance(artifact, dict):
                continue

            if artifact.get("name") != artifact_name:
                continue

            if artifact.get("expired") is True:
                continue

            workflow_run = artifact.get("workflow_run")

            if not isinstance(workflow_run, dict):
                continue

            if workflow_run.get("head_branch") != branch:
                continue

            if str(workflow_run.get("id", "")) == current_run_id:
                continue

            candidates.append(artifact)

        candidates.sort(
            key=lambda item: item.get("created_at", ""),
            reverse=True,
        )

        historical_records = []

        for artifact in candidates[:MAX_ARTIFACT_DOWNLOADS]:
            try:
                record = _load_artifact_record(artifact, token)
                workflow_run = artifact["workflow_run"]

                if record["branch"] != branch:
                    continue

                if record["workflow_path"] != workflow_path:
                    continue

                if record["run_id"] == current_run_id:
                    continue

                if record["run_id"] != str(workflow_run.get("id", "")):
                    continue

                artifact_sha = workflow_run.get("head_sha")

                if artifact_sha and record["commit_sha"] != artifact_sha:
                    continue

                historical_records.append(record)

            except (
                OSError,
                ValueError,
                TypeError,
                KeyError,
                zipfile.BadZipFile,
                json.JSONDecodeError,
            ) as error:
                logger.warning(
                    "[Coverage Gate] Skipping an invalid or unavailable "
                    "history artifact: %s",
                    error,
                )

        historical_records.sort(key=lambda item: item["recorded_at"])
        historical_records = historical_records[-HISTORY_LIMIT:]

        trend = calculate_trend(current_coverage, historical_records)

        logger.info(
            "[Coverage Gate] Coverage trend: %s",
            trend["message"],
        )

        return trend

    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        zipfile.BadZipFile,
        json.JSONDecodeError,
    ) as error:
        logger.warning(
            "[Coverage Gate] WARNING: Could not retrieve coverage history: %s",
            error,
        )
        return unavailable
