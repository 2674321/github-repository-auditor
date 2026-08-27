"""Tests para el cliente de GitHub API con mocks."""

import io
import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from repository_auditor.github.client import (
    _make_request,
    fetch_actions,
    fetch_dependabot,
    fetch_issues,
    fetch_pull_requests,
    fetch_releases,
    fetch_repository,
)
from repository_auditor.github.errors import (
    GitHubAPIError,
    GitHubAuthenticationError,
    GitHubNetworkError,
    GitHubNotFoundError,
    GitHubRateLimitError,
)


def _mock_response(data, status=200, headers=None):
    """Crea un mock de urllib response."""
    mock = MagicMock()
    mock.read.return_value = json.dumps(data).encode("utf-8") if data else b""
    mock.__enter__ = MagicMock(return_value=mock)
    mock.__exit__ = MagicMock(return_value=False)
    if headers:
        mock.headers = headers
    return mock


def _mock_http_error(status, headers=None):
    """Crea un HTTPError real para que mock lo pueda usar como side_effect."""
    msg = f"HTTP Error {status}"
    err = urllib.error.HTTPError(
        url="https://api.github.com/test",
        code=status,
        msg=msg,
        hdrs=headers or {},
        fp=io.BytesIO(b""),
    )
    return err


class TestMakeRequest:
    @patch("repository_auditor.github.client.urllib.request.urlopen")
    def test_success(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"key": "value"})
        result = _make_request("/repos/owner/repo")
        assert result == {"key": "value"}

    @patch("repository_auditor.github.client.urllib.request.urlopen")
    def test_empty_response(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(None)
        result = _make_request("/repos/owner/repo")
        assert result is None

    @patch("repository_auditor.github.client.urllib.request.urlopen")
    def test_404_error(self, mock_urlopen):
        mock_urlopen.side_effect = _mock_http_error(404)
        with pytest.raises(GitHubNotFoundError):
            _make_request("/repos/owner/nonexistent")

    @patch("repository_auditor.github.client.urllib.request.urlopen")
    def test_401_error(self, mock_urlopen):
        mock_urlopen.side_effect = _mock_http_error(401)
        with pytest.raises(GitHubAuthenticationError):
            _make_request("/repos/owner/repo")

    @patch("repository_auditor.github.client.urllib.request.urlopen")
    def test_403_rate_limit(self, mock_urlopen):
        mock_urlopen.side_effect = _mock_http_error(403)
        with pytest.raises(GitHubRateLimitError):
            _make_request("/repos/owner/repo")

    @patch("repository_auditor.github.client.urllib.request.urlopen")
    def test_429_rate_limit(self, mock_urlopen):
        mock_urlopen.side_effect = _mock_http_error(429)
        with pytest.raises(GitHubRateLimitError):
            _make_request("/repos/owner/repo")

    @patch("repository_auditor.github.client.urllib.request.urlopen")
    def test_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        with pytest.raises(GitHubNetworkError):
            _make_request("/repos/owner/repo")

    @patch("repository_auditor.github.client.urllib.request.urlopen")
    def test_invalid_json(self, mock_urlopen):
        mock = MagicMock()
        mock.read.return_value = b"not json"
        mock.__enter__ = MagicMock(return_value=mock)
        mock.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock
        with pytest.raises(GitHubAPIError):
            _make_request("/repos/owner/repo")

    @patch("repository_auditor.github.client._get_token")
    @patch("repository_auditor.github.client.urllib.request.urlopen")
    def test_token_in_header(self, mock_urlopen, mock_token):
        mock_token.return_value = "test_token_abc"
        mock_urlopen.return_value = _mock_response({"ok": True})
        _make_request("/repos/owner/repo")
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        assert req.get_header("Authorization") == "token test_token_abc"

    @patch("repository_auditor.github.client._get_token")
    @patch("repository_auditor.github.client.urllib.request.urlopen")
    def test_no_token_no_auth(self, mock_urlopen, mock_token):
        mock_token.return_value = None
        mock_urlopen.return_value = _mock_response({"ok": True})
        _make_request("/repos/owner/repo")
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        assert req.get_header("Authorization") is None


class TestTokenSecurity:
    @patch("repository_auditor.github.client._get_token")
    @patch("repository_auditor.github.client.urllib.request.urlopen")
    def test_token_not_in_error_message(self, mock_urlopen, mock_token):
        mock_token.return_value = "secret_token_12345"
        mock_urlopen.side_effect = _mock_http_error(404)
        with pytest.raises(GitHubNotFoundError) as exc_info:
            _make_request("/repos/owner/repo")
        assert "secret_token_12345" not in str(exc_info.value)

    @patch("repository_auditor.github.client._get_token")
    @patch("repository_auditor.github.client.urllib.request.urlopen")
    def test_token_not_in_exception_repr(self, mock_urlopen, mock_token):
        mock_token.return_value = "super_secret_xyz"
        mock_urlopen.side_effect = urllib.error.URLError("fail")
        with pytest.raises(GitHubNetworkError) as exc_info:
            _make_request("/repos/owner/repo")
        assert "super_secret_xyz" not in repr(exc_info.value)


class TestFetchRepository:
    @patch("repository_auditor.github.client._make_request")
    def test_success(self, mock_req):
        mock_req.return_value = {
            "owner": {"login": "testuser"},
            "name": "testrepo",
            "full_name": "testuser/testrepo",
            "description": "A test repo",
            "html_url": "https://github.com/testuser/testrepo",
            "default_branch": "main",
            "visibility": "public",
            "archived": False,
            "fork": False,
            "stargazers_count": 42,
            "forks_count": 7,
            "open_issues_count": 3,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-08-26T00:00:00Z",
            "pushed_at": "2026-08-26T12:00:00Z",
            "license": {"spdx_id": "MIT"},
            "topics": ["python", "audit"],
        }
        result = fetch_repository("testuser", "testrepo")
        assert result.owner == "testuser"
        assert result.name == "testrepo"
        assert result.stars == 42
        assert result.license == "MIT"
        assert result.topics == ["python", "audit"]

    @patch("repository_auditor.github.client._make_request")
    def test_empty_response(self, mock_req):
        mock_req.return_value = None
        with pytest.raises(GitHubAPIError):
            fetch_repository("owner", "repo")


class TestFetchReleases:
    @patch("repository_auditor.github.client._make_request")
    def test_with_releases(self, mock_req):
        mock_req.return_value = [
            {
                "name": "v1.0.0",
                "tag_name": "v1.0.0",
                "published_at": "2026-08-26T00:00:00Z",
                "prerelease": False,
                "draft": False,
            },
        ]
        result = fetch_releases("owner", "repo")
        assert result.total_count == 1
        assert result.latest_tag == "v1.0.0"
        assert result.has_published_release is True

    @patch("repository_auditor.github.client._make_request")
    def test_no_releases(self, mock_req):
        mock_req.return_value = []
        result = fetch_releases("owner", "repo")
        assert result.total_count == 0
        assert result.has_published_release is False

    @patch("repository_auditor.github.client._make_request")
    def test_prerelease(self, mock_req):
        mock_req.return_value = [
            {"tag_name": "v2.0.0-beta", "prerelease": True, "draft": False},
        ]
        result = fetch_releases("owner", "repo")
        assert result.latest_prerelease is True


class TestFetchIssues:
    @patch("repository_auditor.github.client._make_request")
    def test_with_issues(self, mock_req):
        mock_req.return_value = [{"number": 1}, {"number": 2}]
        result = fetch_issues("owner", "repo")
        assert result.open_count == 2

    @patch("repository_auditor.github.client._make_request")
    def test_no_issues(self, mock_req):
        mock_req.return_value = []
        result = fetch_issues("owner", "repo")
        assert result.open_count == 0


class TestFetchPullRequests:
    @patch("repository_auditor.github.client._make_request")
    def test_with_prs(self, mock_req):
        mock_req.return_value = [{"number": 1}]
        result = fetch_pull_requests("owner", "repo")
        assert result.open_count == 1

    @patch("repository_auditor.github.client._make_request")
    def test_no_prs(self, mock_req):
        mock_req.return_value = []
        result = fetch_pull_requests("owner", "repo")
        assert result.open_count == 0


class TestFetchActions:
    @patch("repository_auditor.github.client._make_request")
    def test_with_runs(self, mock_req):
        mock_req.return_value = {
            "workflow_runs": [
                {
                    "name": "CI",
                    "status": "completed",
                    "conclusion": "success",
                    "head_branch": "main",
                    "updated_at": "2026-08-26T00:00:00Z",
                },
            ],
        }
        result = fetch_actions("owner", "repo")
        assert result.has_workflows is True
        assert result.latest_run_conclusion == "success"

    @patch("repository_auditor.github.client._make_request")
    def test_no_runs(self, mock_req):
        mock_req.return_value = {"workflow_runs": []}
        result = fetch_actions("owner", "repo")
        assert result.has_workflows is False

    @patch("repository_auditor.github.client._make_request")
    def test_auth_required(self, mock_req):
        mock_req.side_effect = GitHubAuthenticationError()
        result = fetch_actions("owner", "repo")
        assert result.has_workflows is False


class TestFetchDependabot:
    @patch("repository_auditor.github.client._make_request")
    def test_auth_required(self, mock_req):
        mock_req.side_effect = GitHubAuthenticationError()
        result = fetch_dependabot("owner", "repo")
        assert result.requires_auth is True

    @patch("repository_auditor.github.client._make_request")
    def test_not_found(self, mock_req):
        mock_req.side_effect = GitHubNotFoundError()
        result = fetch_dependabot("owner", "repo")
        assert result.requires_auth is True
