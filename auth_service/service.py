import os

from openai import AuthenticationError

from inputs import Inputs, LoadingSpinner
# from storage.service import StorageService
# from storage.store_api_key import load_env_file, save_provider_key, store_api_key
from .create_config import create_config
# from .validate_current_config import validate_current_config_and_fetch_models
from .get_and_select_provider_config import get_and_select_provider_config

class AuthService:
    def __init__(self):
        self.users = {}  # In-memory user store

    def create_config(self):
        try:
            create_config()
        except Exception as e:
            print(f"Error occurred while creating config: {e}")

    # This function will be used to fetch the user config and validate it against the stored config
    def is_llm_config_validated(self):
        provider_config = get_and_select_provider_config()
        return provider_config
        
