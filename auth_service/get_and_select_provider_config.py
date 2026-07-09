from .create_config import create_config
from inputs.terminal_ui import GREEN, RED, RESET, LoadingSpinner, select_menu
from storage.get_provider_info import get_provider_info
import sys  
def get_and_select_provider_config():
    spinner = LoadingSpinner("Fetching configs")
    provider_info = None
    try:
        spinner.start()    
        provider_info = get_provider_info()
    finally:
        spinner.stop()
        if provider_info == []:
            return create_config(isStratup=True)
    
    add_new_provider_text = "Add new provider"
    setup_action = select_menu(
        [provider.provider for provider in provider_info] + [add_new_provider_text] ,
        "Select an option",
    )    
    for item in provider_info:
        if item.provider == setup_action:
            return {
                "provider_id": item.id,
                "api_key": item.api_token,
                "provider": item.provider,
                "model": item.default_model,
                "warning_token_limit": item.warning_token_limit,
            }
    if setup_action == add_new_provider_text:
        create_config(isStratup=False)
        print(f"{GREEN}Restarting application...{RESET}")
        sys.exit(0)  # Exit the application to restart it
    return setup_action
    
