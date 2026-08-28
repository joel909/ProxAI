from cloudflare import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    Cloudflare,
    PermissionDeniedError,
)

from storage.tool_credentials import get_tool_api_key


NO_AVAILABLE_DOMAIN_MESSAGE = (
    "No Cloudflare domain found. Deployment will use its default domain."
)


def list_cloudflare_domains():
    """Return active Cloudflare domains available for app deployment."""
    api_token = get_tool_api_key("Cloudflare")
    if not api_token:
        return {
            "success": False,
            "domains": [],
            "error": "Cloudflare API token is not configured.",
        }

    try:
        client = Cloudflare(api_token=api_token)
        domains = []
        for zone in client.zones.list():
            status = getattr(zone, "status", None)
            if status != "active":
                continue

            account = getattr(zone, "account", None)
            domains.append(
                {
                    "domain": zone.name,
                    "zone_id": zone.id,
                    "account_id": getattr(account, "id", None),
                    "status": status,
                }
            )
    except AuthenticationError:
        return {
            "success": False,
            "domains": [],
            "error": "Cloudflare rejected the saved API token.",
        }
    except PermissionDeniedError:
        return {
            "success": False,
            "domains": [],
            "error": "Cloudflare token cannot list DNS zones.",
        }
    except APIConnectionError:
        return {
            "success": False,
            "domains": [],
            "error": "Could not connect to Cloudflare.",
        }
    except APIStatusError as exc:
        return {
            "success": False,
            "domains": [],
            "error": f"Cloudflare returned HTTP {exc.status_code} while listing domains.",
        }

    if not domains:
        return {
            "success": True,
            "domains": [],
            "message": NO_AVAILABLE_DOMAIN_MESSAGE,
        }

    return {
        "success": True,
        "domains": domains,
        "message": f"Found {len(domains)} available Cloudflare domain(s).",
    }
