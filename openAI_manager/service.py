import re
from .evaluate_llm_reply import check_for_tool_calling
from openai import OpenAI
from .reply_flow import request_reply_with_tool_loop
from storage.service import StorageService

GPT_MODEL_PATTERN = re.compile(r"^gpt-5")


class OpenAIManager:
    def __init__(self, api_key, chat_history_manager,model=None):
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        self.chat_history_manager = chat_history_manager

    def validate_current_config_by_fetch_models(self):
        models = self.client.models.list()
        return sorted(
            model.id
            for model in models.data
            if GPT_MODEL_PATTERN.match(model.id)
        )

    def request_llm_reply(self, prompt, on_tool_call=None):

        return request_reply_with_tool_loop(
            prompt,
            self.client,
            self.model,
            self.chat_history_manager,
            on_tool_call,
        )

    def evaluate_llm_reply(self, llm_reply):
        return check_for_tool_calling(llm_reply, self.chat_history_manager)
