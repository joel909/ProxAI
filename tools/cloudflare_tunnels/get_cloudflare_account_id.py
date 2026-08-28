from cloudflare import Cloudflare
from storage.tool_credentials import get_tool_api_key, get_tool_config


def get_cloudflare_account_id(api_key=None):
    if api_key is None:
        config = get_tool_config("Cloudflare")
        if config.get("account_id"):
            return config["account_id"]
        api_key = get_tool_api_key("Cloudflare")

    if not api_key:
        raise ValueError("Cloudflare API token is not configured")

    client = Cloudflare(api_token=api_key)
    for zone in client.zones.list():
        account = getattr(zone, "account", None)
        account_id = getattr(account, "id", None)
        if account_id:
            return account_id

    raise ValueError("Cloudflare token cannot access any DNS zones or accounts")
