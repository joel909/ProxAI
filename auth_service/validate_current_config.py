from openAI_manager import OpenAIManager
def validate_current_config(api_key, provider):
    # Implement your validation logic here
    # For example, you can check if required fields are present and valid
    if not api_key or not provider:
        return False
    if provider == "OpenAI":
        openai_manager = OpenAIManager(api_key)
        return openai_manager.validate_config()
    return False
