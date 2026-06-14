from pathlib import Path


def read_chat_history(temp_file_name):
    temp_file_path = Path(temp_file_name)
    if not temp_file_path.exists():
        return ""

    return temp_file_path.read_text()
