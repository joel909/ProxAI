from cloudflare import Cloudflare


def get_cloudflare_account_id(api_key):
    client = Cloudflare(api_token=api_key)
    for zone in client.zones.list():
        account = getattr(zone, "account", None)
        account_id = getattr(account, "id", None)
        if account_id:
            return account_id

    raise ValueError("Cloudflare token cannot access any DNS zones or accounts")
