from cloudflare import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    Cloudflare,
    PermissionDeniedError,
)
from uuid import uuid4

from inputs.terminal_ui import LoadingSpinner


def _failure(stage, error):
    return {
        "valid": False,
        "stage": stage,
        "error": error,
        "account_id": None,
        "accounts": [],
        "zones": [],
        "permissions": {
            "zone_read": False,
            "dns_read": False,
            "tunnel_read": False,
        },
    }


def _permission_error(stage, context):
    if stage == "zone_access":
        return (
            "Token is active but cannot list zones. Add Zone > DNS > Edit "
            "and assign the intended zone resources."
        )
    if stage == "dns_access":
        return (
            f"Token is active but cannot read DNS records for {context}. "
            "Add Zone > DNS > Read or Edit for that zone."
        )
    if stage == "tunnel_access":
        return (
            f"Token is active but cannot read Cloudflare Tunnels for {context}. "
            "Add Account > Cloudflare Tunnel > Read or Edit for that account."
        )
    return "Cloudflare rejected the API token. Check that it is active."


def validate_cloudflare_token(api_token):
    """Validate token authentication plus Zone, DNS, and Tunnel read access."""
    if not isinstance(api_token, str) or not api_token.strip():
        return _failure("authentication", "A Cloudflare API token is required.")

    spinner = LoadingSpinner("Validating Cloudflare API token...")
    stage = "authentication"
    context = ""

    try:
        spinner.start()
        client = Cloudflare(api_token=api_token.strip())

        verification = client.user.tokens.verify()
        if verification is None:
            return _failure(
                "authentication",
                "Cloudflare returned no token-verification result.",
            )
        if verification.status != "active":
            return _failure(
                "authentication",
                f"Cloudflare reports that this token is {verification.status}.",
            )

        stage = "zone_access"
        zones_response = list(client.zones.list())
        if not zones_response:
            return _failure(
                stage,
                "Token is active but no zones are accessible. Add Zone > DNS > Edit "
                "and assign at least one zone resource.",
            )

        accounts_by_id = {}
        zones = []
        for zone in zones_response:
            account = getattr(zone, "account", None)
            account_id = getattr(account, "id", None)
            if not account_id:
                return _failure(
                    stage,
                    f"Zone {zone.name} did not provide an account ID.",
                )

            account_name = getattr(account, "name", None) or account_id
            accounts_by_id[account_id] = {
                "id": account_id,
                "name": account_name,
            }
            zones.append(
                {
                    "id": zone.id,
                    "name": zone.name,
                    "account_id": account_id,
                }
            )

        stage = "dns_access"
        for zone in zones:
            context = f'zone {zone["name"]}'
            client.dns.records.list(zone_id=zone["id"], per_page=5)

        accounts = list(accounts_by_id.values())
        stage = "tunnel_access"
        for account in accounts:
            context = f'account {account["name"]}'
            client.zero_trust.tunnels.cloudflared.list(
                account_id=account["id"],
                is_deleted=False,
                per_page=5,
            )

        return {
            "valid": True,
            "stage": "complete",
            "error": None,
            "account_id": accounts[0]["id"] if len(accounts) == 1 else None,
            "accounts": accounts,
            "zones": zones,
            "permissions": {
                "zone_read": True,
                "dns_read": True,
                "tunnel_read": True,
            },
        }
    except AuthenticationError:
        return _failure(
            "authentication",
            "Cloudflare rejected the token. Check that it is correct and active.",
        )
    except PermissionDeniedError:
        return _failure(stage, _permission_error(stage, context))
    except APIConnectionError:
        return _failure(
            stage,
            f"Could not connect to Cloudflare while checking {stage}.",
        )
    except APIStatusError as exc:
        error_text = str(exc)
        if stage == "authentication" and (
            exc.status_code == 400
            or "Invalid format for Authorization header" in error_text
            or "6111" in error_text
        ):
            return _failure(
                stage,
                "Token format is invalid. Paste only the raw Cloudflare API token; "
                "do not include 'Bearer' or 'Authorization:'.",
            )
        return _failure(
            stage,
            f"Cloudflare returned HTTP {exc.status_code} while checking {stage}.",
        )
    except Exception as exc:
        return _failure(
            stage,
            f"Unexpected {type(exc).__name__} while checking {stage}: {exc}",
        )
    finally:
        spinner.stop()


def validate_cloudflare_edit_permissions(api_token, account_id, zone_id, zone_name):
    """Prove Tunnel and DNS Edit access using temporary resources and cleanup."""
    spinner = LoadingSpinner("Testing Cloudflare Edit permissions...")
    client = Cloudflare(api_token=api_token.strip())
    suffix = uuid4().hex[:12]

    try:
        spinner.start()

        tunnel_name = f"proxai-permission-test-{suffix}"
        try:
            tunnel = client.zero_trust.tunnels.cloudflared.create(
                account_id=account_id,
                name=tunnel_name,
                config_src="cloudflare",
            )
        except PermissionDeniedError:
            return _failure(
                "tunnel_edit",
                "Token can read Tunnels but cannot create them. Add "
                "Account > Cloudflare Tunnel > Edit for the selected account.",
            )
        except APIStatusError as exc:
            return _failure(
                "tunnel_edit",
                f"Cloudflare rejected the temporary Tunnel create with HTTP "
                f"{exc.status_code}. Add Account > Cloudflare Tunnel > Edit.",
            )

        try:
            client.zero_trust.tunnels.cloudflared.delete(
                tunnel.id,
                account_id=account_id,
            )
        except Exception as exc:
            return _failure(
                "tunnel_cleanup",
                f"Temporary Tunnel {tunnel_name} was created but could not be deleted. "
                f"Delete Tunnel ID {tunnel.id} manually. Error: {type(exc).__name__}.",
            )

        record_name = f"_proxai-permission-test-{suffix}.{zone_name}"
        try:
            record = client.dns.records.create(
                zone_id=zone_id,
                type="TXT",
                name=record_name,
                content='"proxai temporary permission test"',
                ttl=60,
                comment="Temporary ProxAI permission test; safe to delete",
            )
        except PermissionDeniedError:
            return _failure(
                "dns_edit",
                f"Token can read DNS for {zone_name} but cannot create records. Add "
                "Zone > DNS > Edit for the selected zone.",
            )
        except APIStatusError as exc:
            return _failure(
                "dns_edit",
                f"Cloudflare rejected the temporary DNS create with HTTP "
                f"{exc.status_code}. Add Zone > DNS > Edit for {zone_name}.",
            )

        if record is None:
            return _failure(
                "dns_edit",
                "Cloudflare returned no DNS record after the temporary create request.",
            )

        try:
            client.dns.records.delete(record.id, zone_id=zone_id)
        except Exception as exc:
            return _failure(
                "dns_cleanup",
                f"Temporary DNS record {record_name} was created but could not be "
                f"deleted. Delete record ID {record.id} manually. Error: "
                f"{type(exc).__name__}.",
            )

        return {
            "valid": True,
            "stage": "complete",
            "error": None,
            "permissions": {
                "tunnel_edit": True,
                "dns_edit": True,
            },
        }
    except APIConnectionError:
        return _failure(
            "edit_connection",
            "Could not connect to Cloudflare while testing Edit permissions.",
        )
    except Exception as exc:
        return _failure(
            "edit_test",
            f"Unexpected {type(exc).__name__} while testing Edit permissions: {exc}",
        )
    finally:
        spinner.stop()
