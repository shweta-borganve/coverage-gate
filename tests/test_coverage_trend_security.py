from urllib.request import Request

import pytest

from src import coverage_trend


def test_redirect_to_different_host_removes_authorization_header():
    handler = coverage_trend._SafeRedirectHandler()
    request = Request(
        "https://api.github.com/repos/owner/repo/actions/artifacts",
        headers={"Authorization": "Bearer secret-token"},
    )

    redirected = handler.redirect_request(
        request,
        None,
        302,
        "Found",
        {},
        "https://storage.example.com/artifact.zip",
    )

    assert redirected is not None
    assert redirected.get_header("Authorization") is None


def test_redirect_to_different_port_removes_authorization_header():
    handler = coverage_trend._SafeRedirectHandler()
    request = Request(
        "https://api.github.com/repos/owner/repo/actions/artifacts",
        headers={"Authorization": "Bearer secret-token"},
    )

    redirected = handler.redirect_request(
        request,
        None,
        302,
        "Found",
        {},
        "https://api.github.com:8443/artifact.zip",
    )

    assert redirected is not None
    assert redirected.get_header("Authorization") is None


def test_redirect_to_same_origin_keeps_authorization_header():
    handler = coverage_trend._SafeRedirectHandler()
    request = Request(
        "https://api.github.com/repos/owner/repo/actions/artifacts",
        headers={"Authorization": "Bearer secret-token"},
    )

    redirected = handler.redirect_request(
        request,
        None,
        302,
        "Found",
        {},
        "https://api.github.com/repos/owner/repo/actions/artifacts?page=2",
    )

    assert redirected is not None
    assert redirected.get_header("Authorization") == "Bearer secret-token"


def test_github_request_rejects_oversized_response(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, size):
            assert size == coverage_trend.MAX_RESPONSE_SIZE + 1
            return b"x" * size

    class FakeOpener:
        def open(self, _request, timeout):
            assert timeout == 15
            return FakeResponse()

    monkeypatch.setattr(
        coverage_trend,
        "build_opener",
        lambda *_args: FakeOpener(),
    )

    with pytest.raises(ValueError, match="maximum allowed size"):
        coverage_trend._github_request(
            "https://api.github.com/repos/owner/repo/actions/artifacts",
            "test-token",
        )


def test_github_request_accepts_response_within_size_limit(monkeypatch):
    expected_data = b'{"artifacts": []}'

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, size):
            assert size == coverage_trend.MAX_RESPONSE_SIZE + 1
            return expected_data

    class FakeOpener:
        def open(self, _request, timeout):
            return FakeResponse()

    monkeypatch.setattr(
        coverage_trend,
        "build_opener",
        lambda *_args: FakeOpener(),
    )

    result = coverage_trend._github_request(
        "https://api.github.com/repos/owner/repo/actions/artifacts",
        "test-token",
    )

    assert result == expected_data
