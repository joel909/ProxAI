from .create_config import create_config
class AuthService:
    def __init__(self):
        self.users = {}  # In-memory user store

    def create_config(self):
        try:
            create_config()
        except Exception as e:
            print(f"Error occurred while creating config: {e}")

    # This function will be used to fetch the user config and validate it against the stored config
    def is_user_config_validated(self):
        return False
