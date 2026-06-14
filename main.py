import sys
from auth_service import AuthService
from openAI_manager import OpenAIManager
from storage.service import StorageService

def main():
    print("Welcome to ProxAI CLI!")
    auth_service = AuthService()
    validated_config = auth_service.is_user_config_validated()
    if validated_config:
        chat_history_file = StorageService().create_temp_chat_history_file()
        openai_manager = OpenAIManager(
            validated_config["api_key"],
            validated_config["model"],
            chat_history_file,
        )
        print("User config validated. Proceeding with the application...")
        print(f"Provider: {validated_config['provider']}")
        print(f"Model: {validated_config['model']}")
        print(f"Chat history temp file: {chat_history_file}")
        print("type /help for help!!")
        print("type /exit to exit the application!!")
        while True:
            user_input = input("Enter your Prompt: ")
            if user_input.lower() == "/exit":
                print("Exiting ProxAI CLI. Goodbye!")
                sys.exit(0)
            elif user_input.lower() == "/help":
                print("Available commands:")
                print("/help - Show this help message")
                print("/exit - Exit the application")
                # Add more commands as needed
            else:
                print("Processing your request... Please wait.")
                print("output - >")
                should_continue = True
                response = openai_manager.request_llm_reply(user_input)
                print(response)
                # Here you can add logic to handle other commands
    
    else:
        print("User config not validated. Follow below steps to validate it:")
        auth_service.create_config()
if __name__ == "__main__":
    main()
