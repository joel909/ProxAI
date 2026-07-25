import subprocess
from inputs.terminal_ui import GREEN, RESET,RED
def clone_github_repo(PAT_token, repo_name, destination_path):
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
