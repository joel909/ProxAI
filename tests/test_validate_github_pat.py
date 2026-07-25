import io
import unittest
from unittest import mock

from tools.setup_tools.validate_github_pull_with_PAT import validate_github_pull_with_PAT


class ValidateGitHubPatTests(unittest.TestCase):
    def test_empty_repository_list_shows_private_repository_guidance_in_red(self):
        with (
            mock.patch(
                "tools.setup_tools.validate_github_pull_with_PAT.fetch_repos",
                return_value=[],
            ),
            mock.patch(
                "tools.setup_tools.validate_github_pull_with_PAT.os.path.exists",
                return_value=False,
            ),
            mock.patch(
                "tools.setup_tools.validate_github_pull_with_PAT.select_menu",
                return_value="Exit",
            ) as proceed,
            mock.patch("sys.stdout", new=io.StringIO()) as stdout,
        ):
            validate_github_pull_with_PAT("test-pat")

        output = stdout.getvalue()
        self.assertIn("\033[31mNo Private repositories found.", output)
        self.assertIn("repo scope enabled for private repositories", output)
        self.assertIn("you can ignore this message", output)
        self.assertIn("You will not be able to pull any private repositories", proceed.call_args.args[1])
        self.assertEqual(
            proceed.call_args.args[0],
            ["Exit", "Continue with public repositories only"],
        )


if __name__ == "__main__":
    unittest.main()
