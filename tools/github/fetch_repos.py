import requests

from inputs import LoadingSpinner


def fetch_repos(PAT, repo_type=None):
    if repo_type == "private":
        spinner = LoadingSpinner("Fetching list of Private Repos")
    elif repo_type == "public":
        spinner = LoadingSpinner("Fetching list of Public Repos")
    else:
        spinner = LoadingSpinner("Fetching list of All Repos")

    try:
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
