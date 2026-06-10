from inputs import Inputs
from storage.service import StorageService
from .validate_current_config import validate_current_config
def create_config():
    api_key = Inputs.getInput("Enter your API key", None, str)
    provider = Inputs.getInputWithOptions(
        "Select your provider",
        ["OpenAI", "HackclubAI"],
        None,
    )
    #pass values to storage

    print(f"API Key: {api_key}, Provider: {provider}")
    config = {
        "api_key": api_key,
        "provider": provider
    }
    print("Validating config... Please wait.")
    validate_current_config(api_key, provider)
    if validate_current_config(api_key, provider):
        print("Config validated successfully!")
    else:
        print("Config validation failed. Please check your API key and provider.")
        return
    #test print
    # storage_service = StorageService()
    # storage_service.store_session_info(config)
    print("Config created and Validated successfully!")
