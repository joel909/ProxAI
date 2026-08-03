import tempfile
import unittest
from pathlib import Path

from tools.github.fetch_pre_cloned_repos import fetch_pre_cloned_repos


class FetchPreClonedReposTests(unittest.TestCase):
    def test_returns_only_git_repositories_in_name_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "zebra" / ".git").mkdir(parents=True)
            (root / "Alpha" / ".git").mkdir(parents=True)
            (root / "ordinary-folder").mkdir()

            repos = fetch_pre_cloned_repos(root)

        self.assertEqual([repo["name"] for repo in repos], ["Alpha", "zebra"])
        self.assertTrue(repos[0]["path"].endswith("/Alpha"))

    def test_returns_empty_list_when_clone_root_does_not_exist(self):
        with tempfile.TemporaryDirectory() as directory:
            missing_root = Path(directory) / "missing"

            self.assertEqual(fetch_pre_cloned_repos(missing_root), [])


if __name__ == "__main__":
    unittest.main()
