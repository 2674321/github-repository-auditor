"""Tests para las excepciones de GitHub."""


from repository_auditor.github.errors import (
    GitHubAPIError,
    GitHubAuthenticationError,
    GitHubError,
    GitHubNetworkError,
    GitHubNotFoundError,
    GitHubRateLimitError,
)


class TestGitHubErrorHierarchy:
    def test_base_exception(self):
        assert issubclass(GitHubError, Exception)

    def test_auth_is_github_error(self):
        assert issubclass(GitHubAuthenticationError, GitHubError)

    def test_not_found_is_github_error(self):
        assert issubclass(GitHubNotFoundError, GitHubError)

    def test_rate_limit_is_github_error(self):
        assert issubclass(GitHubRateLimitError, GitHubError)

    def test_api_error_is_github_error(self):
        assert issubclass(GitHubAPIError, GitHubError)

    def test_network_error_is_github_error(self):
        assert issubclass(GitHubNetworkError, GitHubError)


class TestErrorMessages:
    def test_auth_error_default_message(self):
        err = GitHubAuthenticationError()
        assert "token" in str(err).lower() or "autenticación" in str(err).lower()

    def test_not_found_error(self):
        err = GitHubNotFoundError("repositorio")
        assert "repositorio" in str(err)

    def test_rate_limit_error(self):
        err = GitHubRateLimitError(reset_at="1234567890")
        assert err.reset_at == "1234567890"

    def test_api_error_with_status(self):
        err = GitHubAPIError(status_code=500)
        assert "500" in str(err)

    def test_network_error(self):
        err = GitHubNetworkError()
        assert "conectar" in str(err).lower() or "red" in str(err).lower()


class TestTokenNotLeaked:
    """Verifica que los tokens nunca aparezcan en los errores."""

    def test_auth_error_no_token(self):
        err = GitHubAuthenticationError()
        token = "ghp_secret123"
        assert token not in str(err)
        assert token not in repr(err)

    def test_api_error_no_token(self):
        err = GitHubAPIError(status_code=403)
        token = "ghp_secret123"
        assert token not in str(err)
        assert token not in repr(err)
