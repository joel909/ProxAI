import os
def read_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError("File not found")

    with open(file_path, "r") as f:
        return f.read()


