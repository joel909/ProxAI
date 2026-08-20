from pathlib import Path


HOME_DIR = Path.home()
PROXAI_HOME_DIR = HOME_DIR / "ProxAI"
GITHUB_REPOS_DIR = PROXAI_HOME_DIR / "github-repos"

_active_repository_path = None


def set_active_repository_path(repo_path):
    global _active_repository_path
    _active_repository_path = Path(repo_path).expanduser().resolve()
    return _active_repository_path


def get_active_repository_path():
    return _active_repository_path


def unset_active_repository_path():
    global _active_repository_path
    previous_path = _active_repository_path
    _active_repository_path = None
    return previous_path
