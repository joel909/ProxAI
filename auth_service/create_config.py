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
DEFAULT_WARNING_TOKEN_LIMIT = 100000
WARNING_TOKEN_LIMIT_OPTIONS = ["100k (recommended)", "50k", "200k", "500k", "Custom"]


def is_provider_enabled(provider):
    return provider == "OpenAI"


def get_warning_token_limit():
    selected_limit = select_menu(
        WARNING_TOKEN_LIMIT_OPTIONS,
        "Select warning token limit",
    )
    if selected_limit != "Custom":
        return parse_token_limit(selected_limit)

    raw_limit = Inputs.getInput(
        f"{CYAN}Enter custom warning token limit, e.g. 150k{RESET}",
        result_type=str,
    ).strip()
    if raw_limit == "" or not raw_limit.lower().endswith("k"):
        print(f"{RED}Custom token limit must use k format. Using default: {DEFAULT_WARNING_TOKEN_LIMIT}{RESET}")
        return DEFAULT_WARNING_TOKEN_LIMIT

    try:
        warning_token_limit = parse_token_limit(raw_limit)
    except ValueError:
        print(f"{RED}Invalid token limit. Using default: {DEFAULT_WARNING_TOKEN_LIMIT}{RESET}")
        return DEFAULT_WARNING_TOKEN_LIMIT

    if warning_token_limit <= 0:
        print(f"{RED}Token limit must be positive. Using default: {DEFAULT_WARNING_TOKEN_LIMIT}{RESET}")
        return DEFAULT_WARNING_TOKEN_LIMIT

    return warning_token_limit


def parse_token_limit(raw_limit):
    normalized_limit = raw_limit.strip().lower().replace("_", "").replace(",", "")
    normalized_limit = normalized_limit.replace("(recommended)", "").strip()
    multiplier = 1
    if normalized_limit.endswith("k"):
        multiplier = 1000
        normalized_limit = normalized_limit[:-1]

    if normalized_limit == "":
        raise ValueError("empty token limit")

    return int(float(normalized_limit) * multiplier)


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

    warning_token_limit = get_warning_token_limit()
    config["warning_token_limit"] = warning_token_limit
    print(f"Warning token limit: {warning_token_limit}")

    try:
        save_provider_key(
            provider,
            api_key,
            default_model=config["model"],
            warning_token_limit=warning_token_limit,
        )
        print(f"{GREEN}Config created and Validated successfully!{RESET}")

        sys.exit(0)  # Exit the application to restart it
    except IntegrityError:
        print(f"{RED}A provider with this API key already exists.{RESET}")
    except Exception as e:
        print(f"{RED}An error occurred while saving the provider key: {e}{RESET}")
        sys.exit(1)  # Exit with an error code
