import io
import unittest
from types import SimpleNamespace
from unittest import mock

from cloudflare import AuthenticationError, PermissionDeniedError

from tools import setup_tools_manager
from tools.cloudflare_tunnels import get_cloudflare_account_id as account_lookup
from tools.cloudflare_tunnels import setup_cloudflare
from tools.cloudflare_tunnels import validate_cloudflare_token as validator


def make_client(*, verify=None, zones=None, records=None, tunnels=None):
    zone = SimpleNamespace(
        id="zone-123",
        name="example.com",
        account=SimpleNamespace(id="account-123", name="Personal"),
    )
    return SimpleNamespace(
        user=SimpleNamespace(
            tokens=SimpleNamespace(
                verify=verify or mock.Mock(return_value=SimpleNamespace(status="active"))
            )
        ),
        zones=SimpleNamespace(
            list=zones or mock.Mock(return_value=[zone])
        ),
        dns=SimpleNamespace(
            records=SimpleNamespace(list=records or mock.Mock(return_value=[]))
        ),
        zero_trust=SimpleNamespace(
            tunnels=SimpleNamespace(
                cloudflared=SimpleNamespace(
                    list=tunnels or mock.Mock(return_value=[])
                )
            )
        ),
    )


class CloudflareTokenTests(unittest.TestCase):
    def test_validator_checks_zone_dns_and_tunnel_access(self):
        client = make_client()
        with mock.patch.object(validator, "Cloudflare", return_value=client):
            result = validator.validate_cloudflare_token("test-token")

        self.assertTrue(result["valid"])
        self.assertEqual(result["stage"], "complete")
        self.assertEqual(result["account_id"], "account-123")
        self.assertEqual(result["zones"][0]["id"], "zone-123")
        self.assertEqual(
            result["permissions"],
            {"zone_read": True, "dns_read": True, "tunnel_read": True},
        )
        client.dns.records.list.assert_called_once_with(
            zone_id="zone-123",
            per_page=5,
        )
        client.zero_trust.tunnels.cloudflared.list.assert_called_once_with(
            account_id="account-123",
            is_deleted=False,
            per_page=5,
        )

    def test_validator_reports_authentication_failure(self):
        verify = mock.Mock(
            side_effect=AuthenticationError(
                "invalid",
                response=mock.Mock(),
                body=None,
            )
        )
        with mock.patch.object(
            validator,
            "Cloudflare",
            return_value=make_client(verify=verify),
        ):
            result = validator.validate_cloudflare_token("bad-token")

        self.assertFalse(result["valid"])
        self.assertEqual(result["stage"], "authentication")
        self.assertIn("rejected the token", result["error"])

    def test_validator_reports_missing_zone_access(self):
        zones = mock.Mock(
            side_effect=PermissionDeniedError(
                "denied",
                response=mock.Mock(),
                body=None,
            )
        )
        with mock.patch.object(
            validator,
            "Cloudflare",
            return_value=make_client(zones=zones),
        ):
            result = validator.validate_cloudflare_token("test-token")

        self.assertEqual(result["stage"], "zone_access")
        self.assertIn("Zone > DNS > Edit", result["error"])

    def test_validator_reports_missing_dns_access(self):
        records = mock.Mock(
            side_effect=PermissionDeniedError(
                "denied",
                response=mock.Mock(),
                body=None,
            )
        )
        with mock.patch.object(
            validator,
            "Cloudflare",
            return_value=make_client(records=records),
        ):
            result = validator.validate_cloudflare_token("test-token")

        self.assertEqual(result["stage"], "dns_access")
        self.assertIn("Zone > DNS > Read or Edit", result["error"])
        self.assertIn("example.com", result["error"])

    def test_validator_reports_missing_tunnel_access(self):
        tunnels = mock.Mock(
            side_effect=PermissionDeniedError(
                "denied",
                response=mock.Mock(),
                body=None,
            )
        )
        with mock.patch.object(
            validator,
            "Cloudflare",
            return_value=make_client(tunnels=tunnels),
        ):
            result = validator.validate_cloudflare_token("test-token")

        self.assertEqual(result["stage"], "tunnel_access")
        self.assertIn("Cloudflare Tunnel > Read or Edit", result["error"])
        self.assertIn("Personal", result["error"])

    def test_setup_prints_the_exact_validation_failure(self):
        validation = validator._failure(
            "dns_access",
            "Token is active but DNS access is missing.",
        )
        with (
            mock.patch.object(setup_cloudflare.Inputs, "getInput", return_value="token"),
            mock.patch.object(
                setup_cloudflare,
                "validate_cloudflare_token",
                return_value=validation,
            ),
            mock.patch.object(setup_cloudflare, "save_tool_api_key") as save,
            mock.patch.object(
                setup_cloudflare,
                "show_cloudflare_permission_guide",
            ) as show_guide,
            mock.patch("sys.stdout", new=io.StringIO()) as stdout,
        ):
            result = setup_cloudflare.setup_cloudflare_token()

        self.assertEqual(result["stage"], "dns_access")
        self.assertEqual(result["error"], validation["error"])
        self.assertIn("failed during dns access", stdout.getvalue())
        self.assertIn(validation["error"], stdout.getvalue())
        self.assertNotIn("Invalid token", stdout.getvalue())
        show_guide.assert_called_once_with()
        save.assert_not_called()

    def test_permission_guide_shows_link_settings_and_screenshot(self):
        with (
            mock.patch.object(setup_cloudflare.subprocess, "Popen") as open_image,
            mock.patch("sys.stdout", new=io.StringIO()) as stdout,
        ):
            result = setup_cloudflare.show_cloudflare_permission_guide()

        output = stdout.getvalue()
        self.assertTrue(result)
        self.assertIn("https://dash.cloudflare.com/profile/api-tokens", output)
        self.assertIn("Account > Cloudflare Tunnel > Edit", output)
        self.assertIn("Zone > DNS > Edit", output)
        self.assertIn("cloudflare-token-permissions.png", output)
        open_image.assert_called_once()

    def test_setup_saves_account_and_zone_for_valid_token(self):
        validation = {
            "valid": True,
            "stage": "complete",
            "error": None,
            "account_id": "account-123",
            "accounts": [{"id": "account-123", "name": "Personal"}],
            "zones": [
                {
                    "id": "zone-123",
                    "name": "example.com",
                    "account_id": "account-123",
                }
            ],
            "permissions": {
                "zone_read": True,
                "dns_read": True,
                "tunnel_read": True,
            },
        }
        with (
            mock.patch.object(setup_cloudflare.Inputs, "getInput", return_value="token"),
            mock.patch.object(
                setup_cloudflare,
                "validate_cloudflare_token",
                return_value=validation,
            ),
            mock.patch.object(
                setup_cloudflare,
                "validate_cloudflare_edit_permissions",
                return_value={
                    "valid": True,
                    "stage": "complete",
                    "error": None,
                    "permissions": {
                        "tunnel_edit": True,
                        "dns_edit": True,
                    },
                },
            ) as validate_edit,
            mock.patch.object(setup_cloudflare, "save_tool_api_key") as save,
            mock.patch("sys.stdout", new=io.StringIO()),
        ):
            result = setup_cloudflare.setup_cloudflare_token()

        self.assertTrue(result["success"])
        self.assertEqual(result["account_id"], "account-123")
        self.assertEqual(result["zone_id"], "zone-123")
        validate_edit.assert_called_once_with(
            "token",
            "account-123",
            "zone-123",
            "example.com",
        )
        self.assertTrue(result["permissions"]["tunnel_edit"])
        self.assertTrue(result["permissions"]["dns_edit"])
        save.assert_called_once_with("Cloudflare", "token")

    def test_setup_rejects_read_only_tunnel_token(self):
        validation = {
            "valid": True,
            "stage": "complete",
            "error": None,
            "account_id": "account-123",
            "accounts": [{"id": "account-123", "name": "Personal"}],
            "zones": [
                {
                    "id": "zone-123",
                    "name": "example.com",
                    "account_id": "account-123",
                }
            ],
            "permissions": {
                "zone_read": True,
                "dns_read": True,
                "tunnel_read": True,
            },
        }
        edit_failure = validator._failure(
            "tunnel_edit",
            "Token can read Tunnels but cannot create them.",
        )
        with (
            mock.patch.object(setup_cloudflare.Inputs, "getInput", return_value="token"),
            mock.patch.object(
                setup_cloudflare,
                "validate_cloudflare_token",
                return_value=validation,
            ),
            mock.patch.object(
                setup_cloudflare,
                "validate_cloudflare_edit_permissions",
                return_value=edit_failure,
            ),
            mock.patch.object(setup_cloudflare, "show_cloudflare_permission_guide"),
            mock.patch.object(setup_cloudflare, "save_tool_api_key") as save,
            mock.patch("sys.stdout", new=io.StringIO()) as stdout,
        ):
            result = setup_cloudflare.setup_cloudflare_token()

        self.assertFalse(result["success"])
        self.assertEqual(result["stage"], "tunnel_edit")
        self.assertIn("cannot create", stdout.getvalue())
        save.assert_not_called()

    def test_edit_probe_reports_missing_tunnel_edit_without_testing_dns(self):
        tunnel_create = mock.Mock(
            side_effect=PermissionDeniedError(
                "denied",
                response=mock.Mock(),
                body=None,
            )
        )
        dns_create = mock.Mock()
        client = SimpleNamespace(
            zero_trust=SimpleNamespace(
                tunnels=SimpleNamespace(
                    cloudflared=SimpleNamespace(create=tunnel_create)
                )
            ),
            dns=SimpleNamespace(records=SimpleNamespace(create=dns_create)),
        )
        with mock.patch.object(validator, "Cloudflare", return_value=client):
            result = validator.validate_cloudflare_edit_permissions(
                "token",
                "account-123",
                "zone-123",
                "example.com",
            )

        self.assertFalse(result["valid"])
        self.assertEqual(result["stage"], "tunnel_edit")
        self.assertIn("Cloudflare Tunnel > Edit", result["error"])
        dns_create.assert_not_called()

    def test_edit_probe_creates_and_deletes_temporary_resources(self):
        tunnel = SimpleNamespace(id="tunnel-123")
        record = SimpleNamespace(id="record-123")
        tunnel_create = mock.Mock(return_value=tunnel)
        tunnel_delete = mock.Mock()
        dns_create = mock.Mock(return_value=record)
        dns_delete = mock.Mock()
        client = SimpleNamespace(
            zero_trust=SimpleNamespace(
                tunnels=SimpleNamespace(
                    cloudflared=SimpleNamespace(
                        create=tunnel_create,
                        delete=tunnel_delete,
                    )
                )
            ),
            dns=SimpleNamespace(
                records=SimpleNamespace(
                    create=dns_create,
                    delete=dns_delete,
                )
            ),
        )

        with mock.patch.object(validator, "Cloudflare", return_value=client):
            result = validator.validate_cloudflare_edit_permissions(
                "token",
                "account-123",
                "zone-123",
                "example.com",
            )

        self.assertTrue(result["valid"])
        tunnel_delete.assert_called_once_with(
            "tunnel-123",
            account_id="account-123",
        )
        dns_delete.assert_called_once_with(
            "record-123",
            zone_id="zone-123",
        )

    def test_account_lookup_derives_account_from_zone(self):
        zone = SimpleNamespace(
            id="zone-123",
            account=SimpleNamespace(id="account-123"),
        )
        client = SimpleNamespace(
            zones=SimpleNamespace(list=mock.Mock(return_value=[zone]))
        )
        with mock.patch.object(account_lookup, "Cloudflare", return_value=client):
            self.assertEqual(
                account_lookup.get_cloudflare_account_id("token"),
                "account-123",
            )

    def test_menu_dispatches_cloudflare_setup(self):
        with (
            mock.patch.object(
                setup_tools_manager,
                "DEFAULT_TOOL_CREDENTIALS",
                [{"provider": "Cloudflare"}],
            ),
            mock.patch.object(setup_tools_manager, "get_tool_api_key", return_value=None),
            mock.patch.object(
                setup_tools_manager,
                "get_tool_credential",
                return_value=SimpleNamespace(required_token="API token"),
            ),
            mock.patch.object(
                setup_tools_manager,
                "select_menu",
                return_value="Setup Cloudflare API token",
            ),
            mock.patch.object(setup_tools_manager, "setup_cloudflare_token") as setup,
        ):
            setup_tools_manager.setup_tools()

        setup.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
