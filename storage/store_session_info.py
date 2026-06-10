from .store_info import store_info
def store_session_info(session_data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Here you can implement the logic to store session information
    # For example, you can store it in a file or a database
    # This is just a placeholder implementation
    store_info(path, session_data)
