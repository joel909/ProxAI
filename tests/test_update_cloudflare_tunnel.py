import unittest
from types import SimpleNamespace
from unittest import mock

from openAI_manager.request_llm_reply_with_tools_list import tools
from tools.cloudflare_tunnels import update_cloudflare_tunnel as tunnel_tool


class UpdateCloudflareTunnelTests(unittest.TestCase):
    def test_tool_schema_requires_service_url_and_explains_docker_addressing(self):
        definition = next(
            tool
            for tool in tools
            if tool["name"] == "update_cloudflare_tunnel_and_domain"
        )

        self.assertEqual(
            definition["parameters"]["required"],
            ["tunnel_id", "service_url"],
        )
        description = definition["parameters"]["properties"]["service_url"][
            "description"
        ]
        self.assertIn("Compose service name", description)
        self.assertIn("http://app:3000", description)

    def test_uses_saved_zone_id_for_dns_record(self):
        tunnel_update = mock.Mock()
        dns_create = mock.Mock()
        client = SimpleNamespace(
            zero_trust=SimpleNamespace(
                tunnels=SimpleNamespace(
                    cloudflared=SimpleNamespace(
                        configurations=SimpleNamespace(update=tunnel_update)
                    )
                )
            ),
            dns=SimpleNamespace(records=SimpleNamespace(create=dns_create)),
        )

        with (
            mock.patch.object(tunnel_tool, "get_tool_api_key", return_value="token"),
            mock.patch.object(
                tunnel_tool,
                "get_tool_config",
                return_value={
                    "account_id": "account-123",
                    "zone_id": "zone-123",
                },
            ),
            mock.patch.object(
                tunnel_tool,
                "generate_random_domain_extension_id",
                return_value="random123.example.com",
            ),
            mock.patch.object(tunnel_tool, "Cloudflare", return_value=client),
        ):
            result = tunnel_tool.setup_cloudflare_tunnel_and_domain(
                "tunnel-123",
                "http://app:8080",
            )

        self.assertEqual(result["hostname"], "random123.example.com")
        self.assertEqual(result["url"], "https://random123.example.com")
        self.assertEqual(dns_create.call_args.kwargs["zone_id"], "zone-123")
        self.assertEqual(dns_create.call_args.kwargs["name"], "random123.example.com")
        self.assertEqual(dns_create.call_args.kwargs["ttl"], 1)
        ingress = tunnel_update.call_args.kwargs["config"]["ingress"]
        self.assertEqual(ingress[0]["hostname"], "random123.example.com")
        self.assertEqual(ingress[0]["service"], "http://app:8080")
        tunnel_update.assert_called_once_with(
            tunnel_id="tunnel-123",
            account_id="account-123",
            config=mock.ANY,
        )

    def test_rejects_missing_saved_zone_id(self):
        with (
            mock.patch.object(tunnel_tool, "get_tool_api_key", return_value="token"),
            mock.patch.object(
                tunnel_tool,
                "get_tool_config",
                return_value={"account_id": "account-123"},
            ),
            mock.patch.object(tunnel_tool, "Cloudflare") as cloudflare,
        ):
            with self.assertRaisesRegex(ValueError, "Zone ID is not configured"):
                tunnel_tool.setup_cloudflare_tunnel_and_domain(
                    "tunnel-123",
                    "http://app:8080",
                )

        cloudflare.assert_not_called()

if __name__ == "__main__":
    unittest.main()
