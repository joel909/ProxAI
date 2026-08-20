from cloudflare import Cloudflare
def get_cloudflare_account_id(api_key):
    client = Cloudflare(api_token=api_key)
    accounts = client.accounts.list()
    for account in accounts:
        if account.get("type") == "user":
            return account.get("id")
    raise ValueError("User account not found")