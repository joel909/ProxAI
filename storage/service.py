from pathlib import Path
from .store_info import store_info
from .store_session_info import store_session_info
class StorageService:
    def __init__(self):
        pass

    def store_session_info(self, info):
        path = self.get_config_path()
        store_session_info(info, path)

    def get_config_path(self, app_name="ProxAI"):
        return Path.cwd() / f".{app_name}" / "config.json"
