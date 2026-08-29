import unittest
from types import SimpleNamespace
from unittest import mock

from openAI_manager.tool_calling_logic import check_for_tool_calling
from openAI_manager.request_llm_reply_with_tools_list import tools
from tools.cloudflare_tunnels import list_cloudflare_domains as domain_tool


class ListCloudflareDomainsTests(unittest.TestCase):
    def test_tool_is_available_to_the_llm(self):
        self.assertIn(
            "list_cloudflare_domains",
            {tool["name"] for tool in tools},
        )

    def test_returns_active_domains_with_deployment_ids(self):
        zones = [
            SimpleNamespace(
                id="zone-123",
                name="example.com",
                status="active",
                account=SimpleNamespace(id="account-123"),
            ),
            SimpleNamespace(
                id="zone-456",
                name="pending.example",
                status="pending",
                account=SimpleNamespace(id="account-123"),
            ),
        ]
        client = SimpleNamespace(
            zones=SimpleNamespace(list=mock.Mock(return_value=zones))
        )

        with (
            mock.patch.object(
                domain_tool,
                "get_tool_api_key",
                return_value="saved-token",
            ),
            mock.patch.object(
                domain_tool,
                "Cloudflare",
                return_value=client,
            ) as cloudflare,
        ):
            result = domain_tool.list_cloudflare_domains()

        cloudflare.assert_called_once_with(api_token="saved-token")
        self.assertTrue(result["success"])
        self.assertEqual(
            result["domains"],
            [
                {
                    "domain": "example.com",
                    "zone_id": "zone-123",
                    "account_id": "account-123",
                    "status": "active",
                }
            ],
        )

    def test_returns_no_available_domain_message(self):
        zone = SimpleNamespace(
            id="zone-123",
            name="pending.example",
            status="pending",
            account=SimpleNamespace(id="account-123"),
        )
        client = SimpleNamespace(
            zones=SimpleNamespace(list=mock.Mock(return_value=[zone]))
        )

        with (
            mock.patch.object(
                domain_tool,
                "get_tool_api_key",
                return_value="saved-token",
            ),
            mock.patch.object(domain_tool, "Cloudflare", return_value=client),
        ):
            result = domain_tool.list_cloudflare_domains()

        self.assertEqual(
            result,
            {
                "success": True,
                "domains": [],
                "message": (
                    "No Cloudflare domain found. Deployment will use its default domain."
                ),
            },
        )

    def test_returns_configuration_error_without_saved_token(self):
        with mock.patch.object(
            domain_tool,
            "get_tool_api_key",
            return_value=None,
        ):
            result = domain_tool.list_cloudflare_domains()

        self.assertFalse(result["success"])
        self.assertEqual(result["domains"], [])
        self.assertIn("not configured", result["error"])

    def test_dispatcher_calls_cloudflare_domain_handler(self):
        tool_call = SimpleNamespace(
            name="list_cloudflare_domains",
            arguments="{}",
        )

        with mock.patch(
            "openAI_manager.tool_calling_logic.list_cloudflare_domains",
            return_value={"success": True, "domains": []},
        ) as list_domains:
            result = check_for_tool_calling(
                tool_call,
                search_tool=mock.Mock(),
                desktop_tool=mock.Mock(),
                chat_history_manager=mock.Mock(),
            )

        list_domains.assert_called_once_with()
        self.assertEqual(result, {"success": True, "domains": []})


if __name__ == "__main__":
    unittest.main()
