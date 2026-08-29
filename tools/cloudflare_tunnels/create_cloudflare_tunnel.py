from cloudflare import Cloudflare

from storage.tool_credentials import get_tool_api_key

from .get_cloudflare_account_id import get_cloudflare_account_id


def create_cloudflare_tunnel(tunnel_name):
    api_token = get_tool_api_key("Cloudflare")
    if not api_token:
        raise ValueError("Cloudflare API token is not configured")
    if not isinstance(tunnel_name, str) or not tunnel_name.strip():
        raise ValueError("A Cloudflare tunnel name is required")

    account_id = get_cloudflare_account_id()
    client = Cloudflare(api_token=api_token)
    tunnel = client.zero_trust.tunnels.cloudflared.create(
        account_id=account_id,
        name=tunnel_name.strip(),
        config_src="cloudflare",
    )
    return {
        "tunnel_id": tunnel.id,
        "tunnel_name": tunnel.name,
        "token": tunnel.token,
    }
