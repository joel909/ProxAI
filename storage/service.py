from pathlib import Path
import json

from .create_temp_chat_history_file import create_temp_chat_history_file
from .read_chat_history import read_chat_history
from .store_session_info import store_session_info

class StorageService:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[1]

    def store_session_info(self, info):
        path = self.get_config_path()
        store_session_info(info, path)

    def get_session_info(self):
        path = self.get_config_path()
        if not path.exists():
            return None

        with open(path) as f:
            return json.load(f)

    def get_config_path(self, app_name="ProxAI"):
        return self.get_app_path(app_name) / "config.json"

    def get_env_path(self, app_name="ProxAI"):
        return self.get_app_path(app_name) / ".env"

    def get_app_path(self, app_name="ProxAI"):
        return self.project_root / f".{app_name}"

    def create_temp_chat_history_file(self):
        return create_temp_chat_history_file()

    def read_chat_history(self, temp_file_name):
        return read_chat_history(temp_file_name)

    def record_chat_history(self, temp_file_name, operator, data):
        record_chat_history(temp_file_name, operator, data)

    def record_chat_hisotry(self, temp_file_name, operator, data):
        record_chat_history(temp_file_name, operator, data)


def record_chat_history(temp_file_name, operator, data):
    operator_roles = {
        "user": "user",
        "assistant": "assistant",
        "model": "assistant",
        "tool_response": "tool_response",
    }
    operator_key = operator.lower()
    if operator_key not in operator_roles:
        raise ValueError("operator must be 'user', 'assistant', 'model', or 'tool_response'")

    temp_file_path = Path(temp_file_name)
    temp_file_path.parent.mkdir(parents=True, exist_ok=True)

    if temp_file_path.exists():
        file_contents = temp_file_path.read_text().strip()
    else:
        file_contents = ""

    if file_contents:
        try:
            chat_history = json.loads(file_contents)
        except json.JSONDecodeError:
            chat_history = {
                "messages": [
                    {
                        "role": "legacy",
                        "content": file_contents,
                    }
                ]
            }
    else:
        chat_history = {"messages": []}

    if isinstance(chat_history, list):
        chat_history = {"messages": chat_history}
    elif "messages" not in chat_history:
        chat_history = {"messages": []}

    chat_history["messages"].append(
        {
            "role": operator_roles[operator_key],
            "content": data,
        }
    )

    with open(temp_file_path, "w") as f:
        json.dump(chat_history, f, indent=2)
        f.write("\n")


def record_chat_hisotry(temp_file_name, operator, data):
    record_chat_history(temp_file_name, operator, data)
