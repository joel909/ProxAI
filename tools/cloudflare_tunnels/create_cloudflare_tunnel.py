from storage.tool_credentials import get_tool_api_key
from .get_cloudflare_account_id import get_cloudflare_account_id
from cloudflare import Cloudflare

def create_cloudflare_tunnel(tunnel_name):
    api_token = get_tool_api_key("Cloudflare")
    account_id = get_cloudflare_account_id(api_token)
    client = Cloudflare(api_token=api_token)
    tunnel = client.zero_trust.tunnels.cloudflared.create(account_id=account_id, name=tunnel_name)
    print("returned tunnel:", tunnel)
    return tunnel