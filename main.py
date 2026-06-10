import sys
from auth_service import AuthService

def main():
    print("Welcome to ProxAI CLI!")
    auth_service = AuthService()
    if auth_service.is_user_config_validated():
        print("User config validated. Proceeding with the application...")
    else:
        print("User config not validated. Follow below steps to validate it:")
        auth_service.create_config()
if __name__ == "__main__":
    main()
