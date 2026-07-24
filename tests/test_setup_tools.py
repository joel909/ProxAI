import io
import importlib
import unittest
from types import SimpleNamespace
from unittest import mock

from tools import setup_tools_manager as setup_tools

firecrawl_setup = importlib.import_module("tools.setup_tools.setup_firecrawl")
github_setup = importlib.import_module("tools.setup_tools.setup_github")


class SetupToolsTests(unittest.TestCase):
    def test_shows_update_for_a_configured_tool(self):
        with (
            mock.patch.object(
                setup_tools,
                "DEFAULT_TOOL_CREDENTIALS",
                [{"provider": "firecrawl"}],
            ),
            mock.patch.object(setup_tools, "get_tool_api_key", return_value="key"),
            mock.patch.object(
                setup_tools,
                "get_tool_credential",
                return_value=SimpleNamespace(required_token="API Key"),
            ),
            mock.patch.object(
                setup_tools,
                "select_menu",
                return_value="Update Firecrawl API Key",
            ) as menu,
            mock.patch.object(setup_tools, "setup_firecrawl"),
        ):
            setup_tools.setup_tools()

        menu.assert_called_once_with(["Update Firecrawl API Key", "Exit"], "")

    def test_selecting_firecrawl_starts_its_setup(self):
        with (
            mock.patch.object(
                setup_tools,
                "DEFAULT_TOOL_CREDENTIALS",
                [{"provider": "firecrawl"}],
            ),
            mock.patch.object(setup_tools, "get_tool_api_key", return_value=None),
            mock.patch.object(
                setup_tools,
                "get_tool_credential",
                return_value=SimpleNamespace(required_token="API Key"),
            ),
            mock.patch.object(
                setup_tools,
                "select_menu",
                return_value="Setup Firecrawl API Key",
            ) as menu,
            mock.patch.object(setup_tools, "setup_firecrawl") as configure,
            mock.patch("sys.stdout", new=io.StringIO()),
        ):
            setup_tools.setup_tools()

        menu.assert_called_once_with(["Setup Firecrawl API Key", "Exit"], "")
        configure.assert_called_once()

    def test_menu_uses_the_provider_required_token(self):
        with (
            mock.patch.object(
                setup_tools,
                "DEFAULT_TOOL_CREDENTIALS",
                [{"provider": "github"}],
            ),
            mock.patch.object(setup_tools, "get_tool_api_key", return_value=None),
            mock.patch.object(
                setup_tools,
                "get_tool_credential",
                return_value=SimpleNamespace(required_token="PAT token"),
            ),
            mock.patch.object(
                setup_tools,
                "select_menu",
                return_value="Setup Github PAT token",
            ) as menu,
            mock.patch("sys.stdout", new=io.StringIO()),
        ):
            setup_tools.setup_tools()

        menu.assert_called_once_with(["Setup Github PAT token", "Exit"], "")

    def test_github_setup_highlights_repository_access_and_expiration(self):
        with mock.patch("sys.stdout", new=io.StringIO()) as stdout:
            github_setup.show_github_pat_setup_instructions()

        output = stdout.getvalue()
        self.assertIn("fine-grained personal access token", output)
        self.assertIn("\033[31mAll repositories\033[0m", output)
        self.assertIn("\033[31mexpiration date\033[0m", output)

    def test_selecting_github_shows_pat_guidance(self):
        with (
            mock.patch.object(
                setup_tools,
                "DEFAULT_TOOL_CREDENTIALS",
                [{"provider": "github"}],
            ),
            mock.patch.object(setup_tools, "get_tool_api_key", return_value=None),
            mock.patch.object(
                setup_tools,
                "get_tool_credential",
                return_value=SimpleNamespace(required_token="PAT token"),
            ),
            mock.patch.object(
                setup_tools,
                "select_menu",
                return_value="Setup Github PAT token",
            ),
            mock.patch.object(setup_tools, "show_github_pat_setup_instructions") as guide,
        ):
            setup_tools.setup_tools()

        guide.assert_called_once()

    def test_exit_returns_without_starting_provider_setup(self):
        with (
            mock.patch.object(
                setup_tools,
                "DEFAULT_TOOL_CREDENTIALS",
                [{"provider": "firecrawl"}],
            ),
            mock.patch.object(setup_tools, "get_tool_api_key", return_value=None),
            mock.patch.object(
                setup_tools,
                "get_tool_credential",
                return_value=SimpleNamespace(required_token="API Key"),
            ),
            mock.patch.object(setup_tools, "select_menu", return_value="Exit"),
            mock.patch.object(setup_tools, "setup_firecrawl") as configure,
        ):
            setup_tools.setup_tools()

        configure.assert_not_called()

    def test_firecrawl_setup_validates_then_saves_key(self):
        firecrawl = mock.Mock()
        firecrawl.search.return_value = []

        with (
            mock.patch.object(firecrawl_setup.Inputs, "getInput", return_value="test-key"),
            mock.patch.object(firecrawl_setup, "FireCrawlTool", return_value=firecrawl) as tool,
            mock.patch.object(firecrawl_setup, "save_tool_api_key") as save,
            mock.patch("sys.stdout", new=io.StringIO()) as stdout,
        ):
            firecrawl_setup.setup_firecrawl()

        tool.assert_called_once_with(api_key="test-key")
        firecrawl.search.assert_called_once_with(["Firecrawl API test"], limit=1)
        save.assert_called_once_with("firecrawl", "test-key")
        self.assertIn("Firecrawl API key saved.", stdout.getvalue())

    def test_firecrawl_setup_does_not_save_an_invalid_key(self):
        firecrawl = mock.Mock()
        firecrawl.search.side_effect = RuntimeError("invalid key")

        with (
            mock.patch.object(firecrawl_setup.Inputs, "getInput", return_value="bad-key"),
            mock.patch.object(firecrawl_setup, "FireCrawlTool", return_value=firecrawl),
            mock.patch.object(firecrawl_setup, "save_tool_api_key") as save,
            mock.patch("sys.stdout", new=io.StringIO()) as stdout,
        ):
            firecrawl_setup.setup_firecrawl()

        save.assert_not_called()
        self.assertIn("Firecrawl API key validation failed: invalid key", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
