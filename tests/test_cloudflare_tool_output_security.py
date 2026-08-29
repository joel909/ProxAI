import unittest

from openAI_manager.reply_flow import redact_sensitive_tool_output


class CloudflareToolOutputSecurityTests(unittest.TestCase):
    def test_redacts_connector_token_from_stored_history(self):
        original = {
            "tunnel_id": "tunnel-123",
            "tunnel_name": "my-app",
            "token": "secret-connector-token",
        }

        stored = redact_sensitive_tool_output("create_cloudflare_tunnel", original)

        self.assertEqual(stored["token"], "<redacted>")
        self.assertEqual(original["token"], "secret-connector-token")

    def test_leaves_other_tool_outputs_unchanged(self):
        output = {"token": "not-a-cloudflare-connector-token"}

        self.assertIs(redact_sensitive_tool_output("another_tool", output), output)


if __name__ == "__main__":
    unittest.main()
