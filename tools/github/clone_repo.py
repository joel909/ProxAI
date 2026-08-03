import subprocess

from inputs.terminal_ui import GREEN, RED, RESET


def normalize_github_repo(repo_url):
    repo = repo_url.strip().rstrip("/").removesuffix(".git")
    for prefix in (
        "https://github.com/",
        "http://github.com/",
        "ssh://git@github.com/",
        "git@github.com:",
    ):
        if repo.startswith(prefix):
            repo = repo.removeprefix(prefix)
            break

    parts = repo.split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError("Repository must be a GitHub URL or an owner/repository name.")
    return repo


def clone_github_repo(PAT_token, repo_name, destination_path):
    repo_name = normalize_github_repo(repo_name)
    clone_url = f"https://{PAT_token}@github.com/{repo_name}.git"
    result = subprocess.run(
                    ["git", "clone", clone_url, destination_path],
                    capture_output=True,
                    text=True,
                )
    if result.returncode == 0:
        print(f"{GREEN}Cloned {repo_name} From Github in {destination_path}.{RESET}")

        return True
    else:
        print(f"{RED}Clone failed. Check token scope and permissions and token expiration.{RESET}")
        raise Exception(f"Clone failed. Check token scope and permissions and token expiration. Error: {result.stderr}")
