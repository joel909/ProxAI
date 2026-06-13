from pathlib import Path
import json
import tempfile

from .store_info import store_info
from .store_session_info import store_session_info

USER_CHAT_TAG = "<----user---->"
MODEL_CHAT_TAG = "<----model---->"


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
        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            prefix="proxai_chat_",
            suffix=".txt",
            delete=False,
        )
        temp_file.close()
        return temp_file.name

    def record_chat_hisotry(self, temp_file_name, operator, data):
        record_chat_hisotry(temp_file_name, operator, data)


def record_chat_hisotry(temp_file_name, operator, data):
    operator_tags = {
        "user": USER_CHAT_TAG,
        "model": MODEL_CHAT_TAG,
    }
    operator_key = operator.lower()
    if operator_key not in operator_tags:
        raise ValueError("operator must be 'user' or 'model'")

    temp_file_path = Path(temp_file_name)
    temp_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_file_path, "a") as f:
        f.write(f"{operator_tags[operator_key]}\n")
        f.write(f"{data}\n\n")
