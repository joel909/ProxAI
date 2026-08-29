import secrets
import string

from storage.tool_credentials import get_tool_config


DOMAIN_EXTENSION_ID_LENGTH = 16
DOMAIN_EXTENSION_ID_ALPHABET = string.ascii_lowercase + string.digits


def generate_random_domain_extension_id():
    """Return a random hostname under the configured Cloudflare DNS zone."""
    zone_name = get_tool_config("Cloudflare").get("zone_name")
    if not zone_name:
        raise ValueError(
            "Cloudflare domain is not configured. Named tunnels require a domain "
            "on Cloudflare; *.trycloudflare.com is available only through a "
            "development Quick Tunnel."
        )

    zone_name = zone_name.strip().strip(".").lower()
    extension_id = "".join(
        secrets.choice(DOMAIN_EXTENSION_ID_ALPHABET)
        for _ in range(DOMAIN_EXTENSION_ID_LENGTH)
    )
    return f"{extension_id}.{zone_name}"
