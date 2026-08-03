import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from openAI_manager.check_for_tool_calling import check_for_tool_calling
from tools.github.pull_repo import _run_git, pull_github_repo


class PullGithubRepoTests(unittest.TestCase):
    def make_repo(self, root, name="demo"):
        repo = Path(root) / name
        (repo / ".git").mkdir(parents=True)
        return repo

    def test_rejects_path_instead_of_repo_name(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                pull_github_repo("../other", directory)

    def test_rejects_missing_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                pull_github_repo("missing", directory)

    def test_dirty_repository_is_not_pulled(self):
        with tempfile.TemporaryDirectory() as directory:
            self.make_repo(directory)
            with mock.patch(
                "tools.github.pull_repo._run_git",
                return_value=" M changed.py",
            ) as run_git:
                result = pull_github_repo("demo", directory)

        self.assertFalse(result["success"])
        self.assertIn("uncommitted changes", result["error"])
        run_git.assert_called_once()

    def test_clean_repository_is_fast_forwarded(self):
        with tempfile.TemporaryDirectory() as directory:
            self.make_repo(directory)
            with mock.patch(
                "tools.github.pull_repo._run_git",
                side_effect=["", "main", "old", "Updating old..new", "new"],
            ) as run_git:
                result = pull_github_repo("demo", directory)

        self.assertTrue(result["success"])
        self.assertTrue(result["updated"])
        self.assertEqual(result["branch"], "main")
        self.assertEqual(run_git.call_args_list[3].args[1:], ("pull", "--ff-only"))

    def test_git_error_redacts_url_credentials(self):
        failed = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="fatal: https://secret-token@github.com/example/repo.git",
        )
        with mock.patch("tools.github.pull_repo.subprocess.run", return_value=failed):
            with self.assertRaisesRegex(RuntimeError, r"https://\*\*\*@github.com"):
                _run_git(Path("/tmp/repo"), "pull", "--ff-only")

    def test_dispatcher_calls_pull_handler(self):
        tool_call = SimpleNamespace(
            name="pull_github_repo",
            arguments='{"repo_name": "demo"}',
        )
        expected = {"success": True, "repo": "demo"}

        with mock.patch(
            "openAI_manager.check_for_tool_calling.pull_github_repo",
            return_value=expected,
        ) as pull:
            result = check_for_tool_calling(
                tool_call,
                search_tool=mock.Mock(),
                desktop_tool=mock.Mock(),
                chat_history_manager=mock.Mock(),
            )

        pull.assert_called_once_with("demo")
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
