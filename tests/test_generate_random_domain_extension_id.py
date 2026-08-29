import unittest
from unittest import mock

from tools.cloudflare_tunnels import generate_random_domain_extension_id as domain_tool


class GenerateRandomDomainExtensionIdTests(unittest.TestCase):
    def test_generates_sixteen_character_hostname_under_saved_zone(self):
        with mock.patch.object(
            domain_tool,
            "get_tool_config",
            return_value={"zone_name": "Example.COM."},
        ):
            hostname = domain_tool.generate_random_domain_extension_id()

        extension_id, zone_name = hostname.split(".", 1)
        self.assertEqual(len(extension_id), 16)
        self.assertTrue(extension_id.isalnum())
        self.assertEqual(zone_name, "example.com")

    def test_rejects_missing_saved_domain(self):
        with mock.patch.object(domain_tool, "get_tool_config", return_value={}):
            with self.assertRaisesRegex(ValueError, "domain is not configured"):
                domain_tool.generate_random_domain_extension_id()


if __name__ == "__main__":
    unittest.main()
