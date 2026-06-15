import re
from .evaluate_llm_reply import check_for_tool_calling
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
    def request_llm_reply(self, prompt, on_tool_call=None):
        if self.chat_history_file is None:
            self.chat_history_file = self.storage_service.create_temp_chat_history_file()

        original_prompt = prompt
        tool_result = None

        while True:
            response_object, response_text = request_reply(
                original_prompt,
                self.client,
                self.model,
                tool_result,
            )

            tool_calls = [
                output
                for output in response_object
                if output.type == "function_call"
            ]

            for tool_call in tool_calls:
                if on_tool_call is not None:
                    on_tool_call(tool_call.name)

            read_memory_requested = any(
                tool_call.name == "read_memory"
                for tool_call in tool_calls
            )

            if read_memory_requested:
                tool_result = self.storage_service.read_chat_history(
                    self.chat_history_file
                )
                continue

            self.storage_service.record_chat_history(
                self.chat_history_file,
                "user",
                original_prompt,
            )
            self.storage_service.record_chat_history(
                self.chat_history_file,
                "assistant",
                response_text,
            )
            return response_text
                        
    def evaluate_llm_reply(self,llm_reply):
        return check_for_tool_calling(llm_reply,self.chat_history_file)
