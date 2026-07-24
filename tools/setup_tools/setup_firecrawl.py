from inputs import CYAN, Inputs, RED, RESET
from inputs.terminal_ui import GREEN
from storage.tool_credentials import save_tool_api_key
from tools.search_tools import FireCrawlTool


def setup_firecrawl():
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
