from openai import  OpenAI,AuthenticationError
class OpenAIManager:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key)

    def validate_config(self):
        try:
            self.client.models.list()
            return True
        except AuthenticationError:
            return False
        except Exception as e:
            print(f"An error occurred while validating the config: {e}")
            return False
        