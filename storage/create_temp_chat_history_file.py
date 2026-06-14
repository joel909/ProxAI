import tempfile


def create_temp_chat_history_file():
    temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        prefix="proxai_chat_",
        suffix=".txt",
        delete=False,
    )
    temp_file.close()
    return temp_file.name
