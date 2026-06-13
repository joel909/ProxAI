import os

from openai import AuthenticationError

from inputs import Inputs
from storage.service import StorageService
from storage.store_api_key import load_env_file, store_api_key
from .create_config import create_config
from .validate_current_config import validate_current_config_and_fetch_models


class AuthService:
    def __init__(self):
        self.users = {}  # In-memory user store

    def create_config(self):
        try:
            create_config()
        except Exception as e:
            print(f"Error occurred while creating config: {e}")

    # This function will be used to fetch the user config and validate it against the stored config
    def is_user_config_validated(self):
        storage_service = StorageService()
        config = storage_service.get_session_info()
        if not config:
            return False

        provider = config.get("provider")
        saved_model = config.get("model")
        api_key_env_var = config.get("api_key_env_var")
        load_env_file(storage_service.get_env_path())
        api_key = os.environ.get(api_key_env_var) if api_key_env_var else None

        if not provider:
            print("Stored config is missing the provider.")
            return False

        if not api_key and config.get("api_key"):
            api_key = config["api_key"]
            api_key_env_var = api_key_env_var or f"PROXAI_{provider.upper()}_API_KEY"
            store_api_key(api_key, api_key_env_var, storage_service.get_env_path())
            config.pop("api_key", None)
            config["api_key_env_var"] = api_key_env_var

        if not api_key:
            print(
                "Stored config found, but the API key is not available in the "
                f"{api_key_env_var} environment variable."
            )
            return False

        print("Stored config found. Validating config... Please wait.")
        try:
            models = validate_current_config_and_fetch_models(api_key, provider, saved_model)
        except AuthenticationError:
            print("Stored API key failed authentication.")
            return False
        except Exception as e:
            print(f"An error occurred while validating the stored config: {e}")
            return False

        if not models:
            print("Stored config validation failed.")
            return False

        default_model = saved_model if saved_model in models else None
        if saved_model and default_model:
            print(f"Default model from config: {saved_model}")
        elif saved_model:
            print(f"Stored model is no longer available: {saved_model}")

        selected_model = Inputs.getInputWithOptions(
            "Select your OpenAI model",
            models,
            default_model,
        )
        config["provider"] = provider
        config["model"] = selected_model
        storage_service.store_session_info(config)
        print(f"Using model: {selected_model}")
        return {
            "api_key": api_key,
            "provider": provider,
            "model": selected_model,
        }
