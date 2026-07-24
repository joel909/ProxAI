from inputs import RESET, YELLOW, select_menu
from storage import DEFAULT_TOOL_CREDENTIALS
from storage.tool_credentials import get_tool_api_key, get_tool_credential
from tools.setup_tools.setup_firecrawl import setup_firecrawl
from tools.setup_tools.setup_github import show_github_pat_setup_instructions

EXIT_OPTION = "Exit"


def setup_tools():
    providers = [credential["provider"] for credential in DEFAULT_TOOL_CREDENTIALS]
    if not providers:
        print(f"{YELLOW}No tool providers are configured.{RESET}")
        return

    setup_options = []
    for provider in providers:
        credential = get_tool_credential(provider)
        required_token = credential.required_token if credential else "token"
        action = "Update" if get_tool_api_key(provider) else "Setup"
        setup_options.append(f"{action} {provider.title()} {required_token}")
    setup_options.append(EXIT_OPTION)

    selected_option = select_menu(setup_options, "")
    if selected_option == EXIT_OPTION:
        return

    selected_provider = providers[setup_options.index(selected_option)]

    if selected_provider == "firecrawl":
        setup_firecrawl()
    elif selected_provider == "github":
        show_github_pat_setup_instructions()
    else:
        print(f"{YELLOW}{selected_provider.title()} setup is not implemented yet.{RESET}")
