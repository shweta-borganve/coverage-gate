import json
from urllib.parse import quote
from urllib.request import Request, urlopen

from src.logger_config import configure_logger

logger = configure_logger(__name__)

COMMENT_MARKER = "<!-- coverage-gate -->"


def _github_request(url, token, method="GET", body=None):
    """Send an authenticated request to the GitHub REST API."""
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Coverage-Gate",
    }

    data = None

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )

    with urlopen(request, timeout=15) as response:
        response_data = response.read()

    if not response_data:
        return None

    return json.loads(response_data.decode("utf-8"))


def _find_existing_comment(comments_url, token):
    """Find an existing Coverage Gate comment on the pull request."""
    page = 1

    while True:
        url = f"{comments_url}?per_page=100&page={page}"
        comments = _github_request(url, token)

        if not isinstance(comments, list):
            raise TypeError("Unexpected response while listing PR comments.")

        for comment in comments:
            if COMMENT_MARKER in comment.get("body", ""):
                return comment["id"]

        if len(comments) < 100:
            return None

        page += 1


def publish_pr_comment(
    summary,
    token,
    repository,
    pull_number,
    api_url="https://api.github.com",
):
    """Create or update the Coverage Gate comment on a pull request."""
    if not token:
        raise ValueError("GitHub token is required to publish a PR comment.")

    if not repository or "/" not in repository:
        raise ValueError("A valid GitHub repository is required.")

    try:
        pull_number = int(pull_number)
    except (TypeError, ValueError) as error:
        raise ValueError("A valid pull request number is required.") from error

    if pull_number < 1:
        raise ValueError("Pull request number must be greater than zero.")

    encoded_repository = quote(repository, safe="/")
    comments_url = (
        f"{api_url.rstrip('/')}/repos/"
        f"{encoded_repository}/issues/{pull_number}/comments"
    )

    comment_body = f"{COMMENT_MARKER}\n{summary}"

    existing_comment_id = _find_existing_comment(comments_url, token)

    if existing_comment_id is not None:
        comment_url = f"{comments_url}/{existing_comment_id}"

        _github_request(
            comment_url,
            token,
            method="PATCH",
            body={"body": comment_body},
        )

        logger.info("[Coverage Gate] Existing PR comment updated.")
        return "updated"

    _github_request(
        comments_url,
        token,
        method="POST",
        body={"body": comment_body},
    )

    logger.info("[Coverage Gate] New PR comment created.")
    return "created"
