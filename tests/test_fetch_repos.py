import io
import unittest
from unittest import mock

from tools.github.fetch_repos import fetch_repos


class FetchReposTests(unittest.TestCase):
    def _fetch_and_capture_output(self, token):
        response = mock.Mock(status_code=200)
        response.json.return_value = []

        with (
            mock.patch("tools.github.fetch_repos.requests.get", return_value=response),
            mock.patch("tools.github.fetch_repos.LoadingSpinner"),
            mock.patch("sys.stdout", new=io.StringIO()) as stdout,
        ):
            fetch_repos(token)

        return stdout.getvalue()

    def test_prints_fine_grained_pat_type_in_green_without_exposing_token(self):
        token = "github_pat_private-token-value"

        output = self._fetch_and_capture_output(token)

        self.assertIn("\033[32mUsing a fine-grained GitHub PAT (github_pat_).", output)
        self.assertIn("repositories granted to this token", output)
        self.assertNotIn(token, output)

    def test_prints_classic_pat_type_in_green_without_exposing_token(self):
        token = "ghp_private-token-value"

        output = self._fetch_and_capture_output(token)

        self.assertIn("\033[32mUsing GitHub's classic PAT (ghp_).", output)
        self.assertIn("public repository access if enabled by the token's scopes", output)
        self.assertNotIn(token, output)


if __name__ == "__main__":
    unittest.main()
