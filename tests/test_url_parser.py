"""Tests para el parser de URLs de GitHub."""


from repository_auditor.github.url_parser import find_github_remote, parse_github_url


class TestParseGitHubUrlHTTPS:
    def test_https_with_git(self):
        result = parse_github_url("https://github.com/owner/repo.git")
        assert result.is_github is True
        assert result.owner == "owner"
        assert result.repository == "repo"

    def test_https_without_git(self):
        result = parse_github_url("https://github.com/owner/repo")
        assert result.is_github is True
        assert result.owner == "owner"
        assert result.repository == "repo"

    def test_https_with_trailing_slash(self):
        result = parse_github_url("https://github.com/owner/repo/")
        assert result.is_github is True
        assert result.owner == "owner"
        assert result.repository == "repo"

    def test_https_complex_owner(self):
        result = parse_github_url("https://github.com/my-org/my-repo.git")
        assert result.is_github is True
        assert result.owner == "my-org"
        assert result.repository == "my-repo"

    def test_https_preserves_url(self):
        url = "https://github.com/owner/repo.git"
        result = parse_github_url(url)
        assert result.url == url


class TestParseGitHubUrlSSH:
    def test_ssh_git_at(self):
        result = parse_github_url("git@github.com:owner/repo.git")
        assert result.is_github is True
        assert result.owner == "owner"
        assert result.repository == "repo"

    def test_ssh_git_at_without_git(self):
        result = parse_github_url("git@github.com:owner/repo")
        assert result.is_github is True
        assert result.owner == "owner"
        assert result.repository == "repo"

    def test_ssh_protocol(self):
        result = parse_github_url("ssh://git@github.com/owner/repo.git")
        assert result.is_github is True
        assert result.owner == "owner"
        assert result.repository == "repo"


class TestParseGitHubUrlNotGitHub:
    def test_gitlab(self):
        result = parse_github_url("https://gitlab.com/owner/repo.git")
        assert result.is_github is False

    def test_bitbucket(self):
        result = parse_github_url("https://bitbucket.org/owner/repo.git")
        assert result.is_github is False

    def test_random_url(self):
        result = parse_github_url("https://example.com/something")
        assert result.is_github is False

    def test_empty_url(self):
        result = parse_github_url("")
        assert result.is_github is False


class TestParseGitHubUrlEdgeCases:
    def test_whitespace(self):
        result = parse_github_url("  https://github.com/owner/repo.git  ")
        assert result.is_github is True
        assert result.owner == "owner"
        assert result.repository == "repo"

    def test_number_in_owner(self):
        result = parse_github_url("https://github.com/user123/repo456.git")
        assert result.is_github is True
        assert result.owner == "user123"
        assert result.repository == "repo456"


class TestFindGithubRemote:
    def test_finds_https(self):
        urls = ["https://gitlab.com/foo/bar.git", "https://github.com/owner/repo.git"]
        result = find_github_remote(urls)
        assert result is not None
        assert result.is_github is True
        assert result.owner == "owner"

    def test_finds_ssh(self):
        urls = ["git@github.com:owner/repo.git"]
        result = find_github_remote(urls)
        assert result is not None
        assert result.is_github is True

    def test_no_github(self):
        urls = ["https://gitlab.com/owner/repo.git"]
        result = find_github_remote(urls)
        assert result is None

    def test_empty_list(self):
        result = find_github_remote([])
        assert result is None
