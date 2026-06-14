from ast import While
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
    def request_llm_reply(self, prompt):
        if self.chat_history_file is None:
            self.chat_history_file = self.storage_service.create_temp_chat_history_file()

        should_continue = False
        i = 1
        while True:
            responseObject,response_text = request_reply(prompt, self.client, self.model)
            for object in responseObject:
                if object.type == "function_call":
                    if object.name == "read_memory":
                        should_continue = True
                        message_history = self.storage_service.read_chat_history(self.chat_history_file)
                        prompt = f"{prompt}\n\nHere is the relevant memory:\n{message_history}\n\nBased on this memory, please provide an updated response to the next prompt. \n <----user---->\n {prompt}"
                        # self.storage_service.record_chat_history(self.chat_history_file,"user",prompt)
                        # responseObject,response_text = request_reply(new_prompt, self.client, self.model)
            if should_continue:
                should_continue = False
                continue
            # self.storage_service.record_chat_history(self.chat_history_file,"user",prompt)
            if not should_continue:    
                self.storage_service.record_chat_history(
                    self.chat_history_file,
                    "user",
                    prompt,
                )
            self.storage_service.record_chat_history(self.chat_history_file,"assistant",response_text)
            return response_text
                        
    def evaluate_llm_reply(self,llm_reply):
        return check_for_tool_calling(llm_reply,self.chat_history_file)
