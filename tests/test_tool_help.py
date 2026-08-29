import unittest
from types import SimpleNamespace
from unittest import mock

from openAI_manager.tool_calling_logic import check_for_tool_calling
from openAI_manager.request_llm_reply_with_tools_list import build_tool_help_definition, tools
from storage import DEFAULT_TOOL_CREDENTIALS
from storage.tool_credentials import get_tool_help


class ToolHelpTests(unittest.TestCase):
    def test_every_default_tool_has_setup_instructions(self):
        for credential in DEFAULT_TOOL_CREDENTIALS:
            with self.subTest(provider=credential["provider"]):
                self.assertTrue(credential["setup_instructions"].strip())

    def test_tool_is_available_to_the_llm(self):
        self.assertIn("tool_help", {tool["name"] for tool in tools})

    def test_tool_choices_come_from_sqlite(self):
        with mock.patch(
            "openAI_manager.request_llm_reply_with_tools_list.list_tool_providers",
            return_value=["alpha", "beta"],
        ):
            definition = build_tool_help_definition()

        self.assertEqual(
            definition["parameters"]["properties"]["tool"]["enum"],
            ["alpha", "beta"],
        )

    def test_help_returns_instructions_without_the_saved_secret(self):
        help_result = get_tool_help("github")

        self.assertEqual(help_result["tool"].casefold(), "github")
        self.assertEqual(help_result["required_token"], "PAT token")
        self.assertTrue(help_result["setup_instructions"])
        self.assertNotIn("api_key", help_result)

    def test_dispatcher_returns_tool_help_to_the_llm(self):
        tool_call = SimpleNamespace(
            name="tool_help",
            arguments='{"tool": "github"}',
        )
        expected = {"tool": "github", "setup_instructions": "steps"}

        with mock.patch(
            "openAI_manager.tool_calling_logic.get_tool_help",
            return_value=expected,
        ) as help_lookup:
            result = check_for_tool_calling(
                tool_call,
                search_tool=mock.Mock(),
                desktop_tool=mock.Mock(),
                chat_history_manager=mock.Mock(),
            )

        help_lookup.assert_called_once_with("github")
        self.assertEqual(result, expected)

    def test_unknown_tool_lists_available_choices(self):
        result = get_tool_help("missing-provider")

        self.assertIn("error", result)
        self.assertIn(
            "github",
            {provider.casefold() for provider in result["available_tools"]},
        )


if __name__ == "__main__":
    unittest.main()
