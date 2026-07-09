from inputs import CYAN, Inputs, RED, RESET, YELLOW, select_menu
from inputs.terminal_ui import GREEN
from storage import DEFAULT_TOOL_CREDENTIALS
from storage.tool_credentials import get_tool_api_key, save_tool_api_key


def setup_tools():
    pending_providers = []
    for credential in DEFAULT_TOOL_CREDENTIALS:
        provider = credential["provider"]
        if not get_tool_api_key(provider):
            print(f"{RED}setup pending for {provider}{RESET}")
            pending_providers.append(provider)

    if not pending_providers:
        print(f"{YELLOW}All tools are already set up.{RESET}")
        return

    setup_options = [f"Setup {provider}" for provider in pending_providers]
    selected_option = select_menu(
        setup_options,
        "",
    )
    selected_provider = pending_providers[setup_options.index(selected_option)]

    if selected_provider == "firecrawl":
        setup_firecrawl()


def setup_firecrawl():
    from tools.search_tools import FireCrawlTool

    api_key = Inputs.getInput(
        f"{CYAN}Enter your Firecrawl API key{RESET}",
        result_type=str,
    )

    try:
        FireCrawlTool(api_key=api_key).search(["Firecrawl API test"], limit=1)
    except Exception as e:
        print(f"{RED}Firecrawl API key validation failed: {e}{RESET}")
        return

    save_tool_api_key("firecrawl", api_key)
    print(f"{GREEN}Firecrawl API key saved.{RESET}")
