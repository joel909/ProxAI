import unittest
from unittest import mock

from tools.github.clone_repo import clone_github_repo, normalize_github_repo


class CloneGitHubRepoTests(unittest.TestCase):
    def test_normalizes_github_urls(self):
        self.assertEqual(
            normalize_github_repo("https://github.com/example/project.git"),
            "example/project",
        )
        self.assertEqual(normalize_github_repo("example/project"), "example/project")

    @mock.patch("tools.github.clone_repo.subprocess.run")
    def test_clones_normalized_repo_into_destination(self, run):
        run.return_value.returncode = 0

        clone_github_repo("ghp_secret", "https://github.com/example/project", "/tmp/project")

        command = run.call_args.args[0]
        self.assertEqual(command[0:2], ["git", "clone"])
        self.assertEqual(command[2], "https://ghp_secret@github.com/example/project.git")
        self.assertEqual(command[3], "/tmp/project")


if __name__ == "__main__":
    unittest.main()
