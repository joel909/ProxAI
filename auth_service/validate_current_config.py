from openAI_manager import OpenAIManager


def validate_current_config_and_fetch_models(api_key, provider, model=None):
    # Implement your validation logic here
    # For example, you can check if required fields are present and valid
    if not api_key or not provider:
        return False

    if provider == "OpenAI":
        openai_manager = OpenAIManager(api_key, model)
        models = openai_manager.validate_current_config_by_fetch_models()
        # This returns the list of models if the config is valid.
        return models

    return False
