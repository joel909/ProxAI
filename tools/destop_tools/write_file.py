import os


def write_file(file_path, content, filename):
    os.makedirs(file_path, exist_ok=True)
    full_path = os.path.join(file_path, filename)

    with open(full_path, "w") as f:
        f.write(str(content))

    return full_path
