import os


def store_api_key(api_key, key_name, env_path=None):
    os.environ[key_name] = api_key

    if env_path is None:
        return

    env_path.parent.mkdir(parents=True, exist_ok=True)
    existing_lines = []
    if env_path.exists():
        existing_lines = env_path.read_text().splitlines()

    updated = False
    next_lines = []
    for line in existing_lines:
        if line.startswith(f"{key_name}="):
            next_lines.append(f"{key_name}={api_key}")
            updated = True
        else:
            next_lines.append(line)

    if not updated:
        next_lines.append(f"{key_name}={api_key}")

    env_path.write_text("\n".join(next_lines) + "\n")


def load_env_file(env_path):
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())
