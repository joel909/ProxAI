from openai import AuthenticationError

from inputs import Inputs
from storage.service import StorageService
from storage.store_api_key import store_api_key
from .validate_current_config import validate_current_config_and_fetch_models


def get_api_key_env_var_name(provider):
    return f"PROXAI_{provider.upper()}_API_KEY"


def create_config():
    api_key = Inputs.getInput("Enter your API key", result_type=str)
    provider = Inputs.getInputWithOptions(
        "Select your provider",
        ["OpenAI", "HackclubAI"],
        None,
    )
    #pass values to storage

    print(f"Provider: {provider}")
    config = {
        "api_key_env_var": get_api_key_env_var_name(provider),
        "provider": provider,
        "model": None,
    }
    print("Validating config... Please wait.")
    models = None
    while models is None:
        try:
            models = validate_current_config_and_fetch_models(api_key, provider)
            break
        except AuthenticationError:
            print("Authentication failed. Please check your API key and provider.")
            api_key = Inputs.getInput("Re-enter your API key", result_type=str)
            provider = Inputs.getInputWithOptions(
                "Re-select your provider",
                ["OpenAI", "HackclubAI"],
                None,
            )
            config["provider"] = provider
            config["api_key_env_var"] = get_api_key_env_var_name(provider)
        except Exception as e:
            print(f"An error occurred while validating the config: {e}")
            return False
    if models:
        print("Config validated successfully!",models)
    else:
        print("Config validation failed. Please check your API key and provider.")
        return

    model_selected = False
    while not model_selected:
        selected_model = Inputs.getInputWithOptions(
            "Select your OpenAI model",
            models,
            None,
        )

        if selected_model:
            config["model"] = selected_model
            model_selected = True
            print(f"Selected model: {selected_model}")

    storage_service = StorageService()
    store_api_key(api_key, config["api_key_env_var"], storage_service.get_env_path())
    storage_service.store_session_info(config)
    print("Config created and Validated successfully!")
