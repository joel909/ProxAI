from pathlib import Path

from var_files import GITHUB_REPOS_DIR, set_active_repository_path


def explore_repository(repo_name, clone_root=None):
    if not isinstance(repo_name, str) or not repo_name.strip():
        return {"success": False, "error": "repo_name must be a non-empty repository name."}

    repo_name = repo_name.strip()
    if Path(repo_name).name != repo_name or repo_name in {".", ".."}:
        return {
            "success": False,
            "repo_name": repo_name,
            "error": "repo_name must be a repository name, not a path.",
        }

    root = (
        Path(clone_root).expanduser().resolve()
        if clone_root is not None
        else GITHUB_REPOS_DIR.resolve()
    )
    repo_path = (root / repo_name).resolve()

    if not repo_path.is_dir() or not (repo_path / ".git").exists():
        return {
            "success": False,
            "repo_name": repo_name,
            "error": f"Repository '{repo_name}' is not cloned under {root}.",
        }

    active_path = set_active_repository_path(repo_path)
    return {
        "success": True,
        "repo_name": repo_name,
        "path": str(active_path),
    }
