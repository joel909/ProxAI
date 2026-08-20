from cloudflare import Cloudflare
def setup_cloudflare_token(api_key):
    """
    Function to set up the Cloudflare API token.
    """
    from storage.tool_credentials import update_tool_api_key

    print("Setting up Cloudflare API token...")
    api_token = input("Enter your Cloudflare API token: ").strip()

    if not api_token:
        print("No API token provided. Setup aborted.")
        return

    # Update the tool credentials with the new API token
    #check if the api token is valid by making a request to cloudflare api

    update_tool_api_key("Cloudflare", api_token)
    print("Cloudflare API token has been set up successfully.")