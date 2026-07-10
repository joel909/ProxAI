import sys
from auth_service import AuthService
from auth_service.create_config import get_warning_token_limit
from inputs import (
    BLUE,
    CYAN,
    Inputs,
    RED,
    RESET,
    YELLOW,
    LoadingSpinner,
    copy_code_block,
    create_tool_call_handler,
    print_assistant_response,
    select_menu,
)
from openAI_manager import OpenAIManager
from storage import ChatHistoryManager
from storage.tool_credentials import save_tool_api_key
from storage.update_token_warn_limit import update_token_warning_limit
from tools.setup_tools import setup_tools

from setup_flow import SetupFlow


def format_token_limit(token_limit):
    if token_limit % 1000 == 0:
        return f"{token_limit // 1000}k"

    return f"{token_limit / 1000:.1f}k"


def main():
    print("Welcome to ProxAI CLI!")
    # the flow should be like first get a LLM working first that after getting the LLM working the user ne
    #okay now this validates LLM configss 
    auth_service = AuthService()
    validated_config = auth_service.is_llm_config_validated()
    #validate if intial setup for proxAI to collect the information was done or not js check mainefiest
    chat_history_manager = ChatHistoryManager()
    openai_manager = OpenAIManager(
        validated_config["api_key"],
        chat_history_manager,
        validated_config["model"],
        validated_config.get("warning_token_limit"),
    )

    setup_flow = SetupFlow(openai_manager)
    is_setup_complete = setup_flow.is_setup_completed()
    if not is_setup_complete:
        setup_action = select_menu(
            ["Start", "Exit"],
            f"{RED}Setup is not completed. Do you want to setup now or exit?{RESET}",
        )
        if setup_action == "Exit":
            print("Exiting ProxAI CLI.")
            sys.exit(0)
        else:
            print("Starting setup...")
            setup_flow.begin_setup_flow()
            


    print("User config validated. Proceeding with the application...")
    print(f"Provider: {validated_config['provider']}")
    print(f"Model: {validated_config['model']}")
    print(f"Token warning limit: {format_token_limit(openai_manager.warning_token_limit)}")
    print("type /help for help!!")
    print("type /exit to exit the application!!")
    while True:
        user_input = input(f"{CYAN}Enter your Prompt: {BLUE}")
        print(RESET, end="")
        if user_input.lower() == "/exit":
            print("Exiting ProxAI CLI. Goodbye!")
            sys.exit(0)
        elif user_input.lower() == "/help":
            print(f"{CYAN}ProxAI Help Menu{RESET}")
            print(f"{YELLOW}/help{RESET}   Show this help menu")
            print(f"{YELLOW}/exit{RESET}   Exit the application")
            print(f"{YELLOW}/copy N{RESET} Copy code block N from the last response")
            print(f"{YELLOW}/token-warn-limit{RESET} Update the token warning limit")
            print(f"{YELLOW}/firecrawl-key{RESET} Add or update the Firecrawl API key")
            print(f"{YELLOW}/setup-tools{RESET} Show tools pending setup")
            # Add more commands as needed
        elif user_input.lower() == "/token-warn-limit":
            try:
                warning_token_limit = get_warning_token_limit()
                update_token_warning_limit(
                    validated_config["provider_id"],
                    warning_token_limit,
                )
                validated_config["warning_token_limit"] = warning_token_limit
                openai_manager.warning_token_limit = warning_token_limit
                print(
                    f"{YELLOW}Token warning limit updated to "
                    f"{format_token_limit(warning_token_limit)}{RESET}"
                )
            except Exception as e:
                print(f"{RED}Error updating token warning limit: {e}{RESET}")
        elif user_input.lower() == "/firecrawl-key":
            try:
                api_key = Inputs.getInput(
                    f"{CYAN}Enter your Firecrawl API key{RESET}",
                    result_type=str,
                )
                save_tool_api_key("firecrawl", api_key)
                print(f"{YELLOW}Firecrawl API key saved.{RESET}")
            except Exception as e:
                print(f"{RED}Error saving Firecrawl API key: {e}{RESET}")
        elif user_input.lower() == "/setup-tools":
            setup_tools()
        elif user_input.lower().startswith("/copy"):
            parts = user_input.split()
            try:
                index = int(parts[1]) if len(parts) > 1 else 1
            except ValueError:
                print(f"{RED}Usage: /copy N{RESET}")
                continue

            copied, message = copy_code_block(index)
            color = YELLOW if copied else RED
            print(f"{color}{message}{RESET}")
        else:
            spinner = LoadingSpinner()
            spinner.start()
            show_tool_call = create_tool_call_handler(spinner)

            try:
                response = openai_manager.request_llm_reply(
                    user_input,
                    on_tool_call=show_tool_call,
                )
            finally:
                spinner.stop()

            if response is None:
                print(f"{YELLOW}Request cancelled.{RESET}")
                continue

            print_assistant_response(response)
            # Here you can add logic to handle other commands
    
    # else:
    #     print("User config not validated. Follow below steps to validate it:")
    #     auth_service.create_config()
if __name__ == "__main__":
    main()
