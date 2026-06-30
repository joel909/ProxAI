from openai import AuthenticationError
import sys
from inputs import CYAN, Inputs, LoadingSpinner, RED, RESET, select_menu
from inputs.terminal_ui import GREEN
from storage.service import StorageService
from storage.store_provider_info import save_provider_key
from .validate_current_config import validate_current_config_and_fetch_models
from sqlalchemy.exc import IntegrityError


def get_api_key_env_var_name(provider):
    return f"PROXAI_{provider.upper()}_API_KEY"


PROVIDER_OPTIONS = ["OpenAI", "HackclubAI", "Other"]


def is_provider_enabled(provider):
    return provider == "OpenAI"


def create_config(isStratup=True):
    if isStratup:
        print(f"{CYAN}Hey there, your setup is pending{RESET}")
    setup_action = select_menu(
        ["Start setup", "Exit"],
        "Select an option",
    )
    if setup_action == "Exit":
        print("Exiting setup.")
        sys.exit(0)

    provider = select_menu(
        PROVIDER_OPTIONS,
        "Select your provider",
    )
    if not is_provider_enabled(provider):
        print(f"{RED}not enabled{RESET}")
        return False

    api_key = Inputs.getInput(f"{CYAN}Enter your API key{RESET}", result_type=str)
    #pass values to storage

    print(f"Provider: {provider}")
    config = {
        "api_key_env_var": get_api_key_env_var_name(provider),
        "provider": provider,
        "model": None,
    }
    spinner = LoadingSpinner("Validating config")
    models = None
    while models is None:
        try:
            spinner.start()
            models = validate_current_config_and_fetch_models(api_key, provider)
            break
        except AuthenticationError:
            spinner.stop()
            print(f"{RED}Authentication failed. Please check your API key and provider.{RESET}")
            provider = select_menu(
                PROVIDER_OPTIONS,
                "Re-select your provider",
            )
            if not is_provider_enabled(provider):
                print(f"{RED}not enabled{RESET}")
                return False

            api_key = Inputs.getInput(f"{CYAN}Re-enter your API key{RESET}", result_type=str)
            config["provider"] = provider
            config["api_key_env_var"] = get_api_key_env_var_name(provider)
        except Exception as e:
            spinner.stop()
            print(f"{RED}An error occurred while validating the config: {e}{RESET}")
            return False
        finally:
            spinner.stop()
    if models:
        print("Config validated successfully!",models)
    else:
        print(f"{RED}Config validation failed. Please check your API key and provider.{RESET}")
        return

    
    model_selected = False
    while not model_selected:
        selected_model =  select_menu(
                models,
                "Please select your prefered model from the available options",
            )

        if selected_model:
            config["model"] = selected_model
            model_selected = True
            print(f"Selected model: {selected_model}")

    try:
        save_provider_key(provider, api_key)
        print(f"{GREEN}Config created and Validated successfully!{RESET}")

        sys.exit(0)  # Exit the application to restart it
    except IntegrityError:
        print(f"{RED}A provider with this API key already exists.{RESET}")
    except Exception as e:
        print(f"{RED}An error occurred while saving the provider key: {e}{RESET}")
        sys.exit(1)  # Exit with an error code

