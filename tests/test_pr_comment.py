import json
from unittest.mock import MagicMock

import pytest

from src import pr_comment


def mock_response(data):
    """Create a mock GitHub API response."""
    response = MagicMock()
    response.read.return_value = json.dumps(data).encode("utf-8")
    response.__enter__.return_value = response
    return response


def test_publish_pr_comment_creates_new_comment(monkeypatch):
    requests = []

    def fake_urlopen(request, timeout):
        requests.append((request, timeout))

        if request.method == "GET":
            return mock_response([])

        return mock_response({"id": 123})

    monkeypatch.setattr(pr_comment, "urlopen", fake_urlopen)

    result = pr_comment.publish_pr_comment(
        summary="Coverage: 85%",
        token="test-token",
        repository="owner/repo",
        pull_number=10,
    )

    assert result == "created"
    assert len(requests) == 2

    get_request, timeout = requests[0]
    post_request, _ = requests[1]

    assert get_request.method == "GET"
    assert post_request.method == "POST"
    assert timeout == 15

    body = json.loads(post_request.data.decode("utf-8"))

    assert pr_comment.COMMENT_MARKER in body["body"]
    assert "Coverage: 85%" in body["body"]


def test_publish_pr_comment_updates_existing_comment(monkeypatch):
    requests = []

    def fake_urlopen(request, timeout):
        requests.append(request)

        if request.method == "GET":
            return mock_response(
                [
                    {
                        "id": 456,
                        "body": (
                            f"{pr_comment.COMMENT_MARKER}\n" "Old coverage report"
                        ),
                    }
                ]
            )

        return mock_response({"id": 456})

    monkeypatch.setattr(pr_comment, "urlopen", fake_urlopen)

    result = pr_comment.publish_pr_comment(
        summary="Coverage: 90%",
        token="test-token",
        repository="owner/repo",
        pull_number=10,
    )

    assert result == "updated"
    assert len(requests) == 2
    assert requests[1].method == "PATCH"

    body = json.loads(requests[1].data.decode("utf-8"))

    assert pr_comment.COMMENT_MARKER in body["body"]
    assert "Coverage: 90%" in body["body"]


def test_publish_pr_comment_rejects_missing_token():
    with pytest.raises(ValueError, match="GitHub token is required"):
        pr_comment.publish_pr_comment(
            summary="Coverage: 85%",
            token="",
            repository="owner/repo",
            pull_number=10,
        )


def test_publish_pr_comment_rejects_invalid_repository():
    with pytest.raises(ValueError, match="valid GitHub repository"):
        pr_comment.publish_pr_comment(
            summary="Coverage: 85%",
            token="test-token",
            repository="invalid-repository",
            pull_number=10,
        )


@pytest.mark.parametrize("pull_number", ["invalid", 0, -1])
def test_publish_pr_comment_rejects_invalid_pull_number(pull_number):
    with pytest.raises(ValueError):
        pr_comment.publish_pr_comment(
            summary="Coverage: 85%",
            token="test-token",
            repository="owner/repo",
            pull_number=pull_number,
        )


def test_publish_pr_comment_rejects_unexpected_comments_response(monkeypatch):
    monkeypatch.setattr(
        pr_comment,
        "_github_request",
        lambda *args, **kwargs: {"message": "Not a list"},
    )

    with pytest.raises(TypeError, match="Unexpected response"):
        pr_comment.publish_pr_comment(
            summary="Coverage: 85%",
            token="test-token",
            repository="owner/repo",
            pull_number=10,
        )
