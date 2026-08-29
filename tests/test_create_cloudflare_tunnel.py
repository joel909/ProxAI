import unittest
from types import SimpleNamespace
from unittest import mock

from tools.cloudflare_tunnels import create_cloudflare_tunnel as tunnel_tool


class CreateCloudflareTunnelTests(unittest.TestCase):
    def test_creates_remotely_managed_tunnel_and_returns_needed_fields(self):
        create = mock.Mock(
            return_value=SimpleNamespace(
                id="tunnel-123",
                name="my-app",
                token="connector-token",
            )
        )
        client = SimpleNamespace(
            zero_trust=SimpleNamespace(
                tunnels=SimpleNamespace(
                    cloudflared=SimpleNamespace(create=create)
                )
            )
        )

        with (
            mock.patch.object(tunnel_tool, "get_tool_api_key", return_value="api-token"),
            mock.patch.object(
                tunnel_tool,
                "get_cloudflare_account_id",
                return_value="account-123",
            ),
            mock.patch.object(tunnel_tool, "Cloudflare", return_value=client),
        ):
            result = tunnel_tool.create_cloudflare_tunnel(" my-app ")

        create.assert_called_once_with(
            account_id="account-123",
            name="my-app",
            config_src="cloudflare",
        )
        self.assertEqual(
            result,
            {
                "tunnel_id": "tunnel-123",
                "tunnel_name": "my-app",
                "token": "connector-token",
            },
        )


if __name__ == "__main__":
    unittest.main()
