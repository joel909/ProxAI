from pathlib import Path

from var_files import GITHUB_REPOS_DIR


def fetch_pre_cloned_repos(clone_root=None):
    root = Path(clone_root) if clone_root is not None else GITHUB_REPOS_DIR
    if not root.is_dir():
        return []

    repos = []
    for path in sorted(root.iterdir(), key=lambda item: item.name.casefold()):
        if path.is_dir() and (path / ".git").exists():
            repos.append({
                "name": path.name,
                "path": str(path.resolve()),
            })
    return repos
