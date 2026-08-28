import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from openAI_manager.tool_calling_logic import check_for_tool_calling
from openAI_manager.request_llm_reply import tools
from tools.destop_tools.run_shell import run_shell_command
from tools.github.explore_repository import explore_repository
from tools.github.unset_repository import unset_repository
from var_files import get_active_repository_path, unset_active_repository_path


class ExploreRepositoryTests(unittest.TestCase):
    def tearDown(self):
        unset_active_repository_path()

    def test_returns_error_when_repository_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            result = explore_repository("demo", directory)

        self.assertFalse(result["success"])
        self.assertEqual(result["repo_name"], "demo")
        self.assertIn("not cloned", result["error"])

    def test_returns_path_when_repository_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_path = Path(directory) / "demo"
            (repo_path / ".git").mkdir(parents=True)

            result = explore_repository("demo", directory)

        self.assertTrue(result["success"])
        self.assertEqual(result["repo_name"], "demo")
        self.assertEqual(result["path"], str(repo_path.resolve()))
        self.assertEqual(get_active_repository_path(), repo_path.resolve())

    def test_shell_commands_run_from_active_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_path = Path(directory) / "demo"
            (repo_path / ".git").mkdir(parents=True)
            explore_repository("demo", directory)

            result = run_shell_command("pwd")

        self.assertIsNone(result["error"])
        self.assertEqual(result["output"], str(repo_path.resolve()))

    def test_unset_repository_clears_active_path(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_path = Path(directory) / "demo"
            (repo_path / ".git").mkdir(parents=True)
            explore_repository("demo", directory)

            result = unset_repository()

        self.assertTrue(result["success"])
        self.assertEqual(result["previous_path"], str(repo_path.resolve()))
        self.assertIsNone(get_active_repository_path())

    def test_tool_is_available_to_the_llm(self):
        tool_names = {tool["name"] for tool in tools}
        self.assertIn("explore_repository", tool_names)
        self.assertIn("unset_repository", tool_names)

    def test_dispatcher_calls_explore_repository(self):
        tool_call = SimpleNamespace(
            name="explore_repository",
            arguments='{"repo_name": "demo"}',
        )

        with mock.patch(
            "openAI_manager.check_for_tool_calling.explore_repository",
            return_value={"repo_name": "demo"},
        ) as explore:
            result = check_for_tool_calling(
                tool_call,
                search_tool=mock.Mock(),
                desktop_tool=mock.Mock(),
                chat_history_manager=mock.Mock(),
            )

        explore.assert_called_once_with("demo")
        self.assertEqual(result, {"repo_name": "demo"})

    def test_dispatcher_calls_unset_repository(self):
        tool_call = SimpleNamespace(name="unset_repository", arguments="{}")

        with mock.patch(
            "openAI_manager.check_for_tool_calling.unset_repository",
            return_value={"success": True},
        ) as unset:
            result = check_for_tool_calling(
                tool_call,
                search_tool=mock.Mock(),
                desktop_tool=mock.Mock(),
                chat_history_manager=mock.Mock(),
            )

        unset.assert_called_once_with()
        self.assertEqual(result, {"success": True})


if __name__ == "__main__":
    unittest.main()
