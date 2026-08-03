import requests

from inputs import GREEN, RESET, LoadingSpinner


def _describe_pat(PAT):
    token = PAT.strip() if isinstance(PAT, str) else ""

    if token.startswith("github_pat_"):
        return (
            "Using a fine-grained GitHub PAT (github_pat_). "
            "Repository access is limited to repositories granted to this token."
        )
    if token.startswith("ghp_"):
        return (
            "Using GitHub's classic PAT (ghp_). "
            "It should have public repository access if enabled by the token's scopes."
        )
    return "GitHub PAT type could not be identified from its prefix."


def fetch_repos(PAT, repo_type=None):
    if repo_type == "private":
        spinner = LoadingSpinner("Fetching list of Private Repos")
    elif repo_type == "public":
        spinner = LoadingSpinner("Fetching list of Public Repos")
    else:
        spinner = LoadingSpinner("Fetching list of All Repos")

    try:
        print(f"{GREEN}{_describe_pat(PAT)}{RESET}")
        spinner.start()
        if repo_type is None:
            response = requests.get(
                "https://api.github.com/user/repos",
                headers={"Authorization": f"token {PAT}"}
                )
        else:
            response = requests.get(
                "https://api.github.com/user/repos",
                headers={"Authorization": f"token {PAT}"},
                params={"type": repo_type, "per_page": 10},
            )
        if response.status_code != 200:
            raise RuntimeError(
                "Failed to fetch repositories. Please check your token and permissions. "
                f"Status code: {response.status_code}"
            )
        return response.json()
    finally:
        spinner.stop()
