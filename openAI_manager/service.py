import re
from .check_for_tool_calling import check_for_tool_calling
from openai import OpenAI
from .reply_flow import request_reply_with_tool_loop

GPT_MODEL_PATTERN = re.compile(r"^gpt-5")
DEFAULT_WARNING_TOKEN_LIMIT = 100000


class OpenAIManager:
    def __init__(
        self,
        api_key,
        chat_history_manager,
        model=None,
        warning_token_limit=DEFAULT_WARNING_TOKEN_LIMIT,
    ):
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        self.chat_history_manager = chat_history_manager
        self.warning_token_limit = warning_token_limit or DEFAULT_WARNING_TOKEN_LIMIT

    def validate_current_config_by_fetch_models(self):
        models = self.client.models.list()
        return sorted(
            model.id
            for model in models.data
            if GPT_MODEL_PATTERN.match(model.id)
        )

    def request_llm_reply(self, prompt, on_tool_call=None,custom_build_input_messages_function=None,custom_available_tools=None):
        if custom_build_input_messages_function is None and custom_available_tools is None:
            return request_reply_with_tool_loop(
                prompt,
                self.client,
                self.model,
                self.chat_history_manager,
                self.warning_token_limit,
                on_tool_call,
            )
        else:
            return request_reply_with_tool_loop(
                prompt,
                self.client,
                self.model,
                self.chat_history_manager,
                self.warning_token_limit,
                on_tool_call,
                build_input_messages_function=custom_build_input_messages_function,
                custom_available_tools=custom_available_tools,
            )

    def evaluate_llm_reply(self, llm_reply):
        return check_for_tool_calling(llm_reply, self.chat_history_manager)
