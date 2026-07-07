import sys
from auth_service import AuthService
from inputs import (
    BLUE,
    CYAN,
    RED,
    RESET,
    YELLOW,
    LoadingSpinner,
    copy_code_block,
    print_assistant_response,
)
from openAI_manager import OpenAIManager
from storage import ChatHistoryManager
from storage.service import StorageService


def format_token_limit(token_limit):
    if token_limit % 1000 == 0:
        return f"{token_limit // 1000}k"

    return f"{token_limit / 1000:.1f}k"


def main():
    print("Welcome to ProxAI CLI!")
    auth_service = AuthService()
    validated_config = auth_service.is_user_config_validated()

    chat_history_manager = ChatHistoryManager()
    openai_manager = OpenAIManager(
        validated_config["api_key"],
        chat_history_manager,
        validated_config["model"],
        validated_config.get("warning_token_limit"),
    )
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
            # Add more commands as needed
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

            def show_tool_call(tool_name, event="started"):
                spinner.stop()

                if event == "started":
                    print(f"{YELLOW}Tool requested: {tool_name}{RESET}")
                elif event == "finished":
                    spinner.start()

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
