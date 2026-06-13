import re

from openai import OpenAI
from .request_llm_reply import request_reply
from storage.service import StorageService

GPT_MODEL_PATTERN = re.compile(r"^gpt-5")


class OpenAIManager:
    def __init__(self, api_key, model=None, chat_history_file=None):
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        self.storage_service = StorageService()
        self.chat_history_file = chat_history_file

    def validate_current_config_by_fetch_models(self):
        models = self.client.models.list()
        return sorted(
            model.id
            for model in models.data
            if GPT_MODEL_PATTERN.match(model.id)
        )
    def request_llm_reply(self, prompt):
        if self.chat_history_file is None:
            self.chat_history_file = self.storage_service.create_temp_chat_history_file()

        self.storage_service.record_chat_hisotry(
            self.chat_history_file,
            "user",
            prompt,
        )
        response = request_reply(prompt, self.client, self.model)
        self.storage_service.record_chat_hisotry(
            self.chat_history_file,
            "model",
            response,
        )
        return response
