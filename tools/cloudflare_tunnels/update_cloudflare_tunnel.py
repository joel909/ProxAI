from cloudflare import Cloudflare

from storage.tool_credentials import get_tool_api_key, get_tool_config
from tools.cloudflare_tunnels.generate_random_domain_extension_id import (
    generate_random_domain_extension_id,
)


def setup_cloudflare_tunnel_and_domain(tunnel_id, service_url):
    api_token = get_tool_api_key("Cloudflare")
    if not api_token:
        raise ValueError(
            "Cloudflare API token is not configured. Run /setup-tools and configure "
            "Cloudflare with a domain first."
        )

    cloudflare_config = get_tool_config("Cloudflare")
    account_id = cloudflare_config.get("account_id")
    zone_id = cloudflare_config.get("zone_id")
    if not zone_id:
        raise ValueError(
            "Cloudflare Zone ID is not configured. Run /setup-tools and configure "
            "Cloudflare with a domain first."
        )
    if not account_id:
        raise ValueError(
            "Cloudflare Account ID is not configured. Run /setup-tools and configure "
            "Cloudflare with a domain first."
        )
    if not service_url:
        raise ValueError("A service URL is required to configure the Cloudflare tunnel.")

    host_name = generate_random_domain_extension_id()
    client = Cloudflare(api_token=api_token)
    client.zero_trust.tunnels.cloudflared.configurations.update(
        tunnel_id=tunnel_id,
        account_id=account_id,
        config={
            "ingress": [
                {
                    "hostname": host_name,
                    "service": service_url,
                },
                {"service": "http_status:404"},  # required catch-all, must be last
            ]
        },
    )

    client.dns.records.create(
        zone_id=zone_id,
        type="CNAME",
        name=host_name,
        content=f"{tunnel_id}.cfargotunnel.com",
        proxied=True,
    )
    return {
        "success": True,
        "hostname": host_name,
        "url": f"https://{host_name}",
        "service_url": service_url,
        "tunnel_id": tunnel_id,
        "cname_target": f"{tunnel_id}.cfargotunnel.com",
    }
