import os
import re
import subprocess
from pathlib import Path

from var_files import GITHUB_REPOS_DIR


_CREDENTIAL_PATTERN = re.compile(r"(https?://)[^/@\s]+@", re.IGNORECASE)


def _redact_credentials(value):
    return _CREDENTIAL_PATTERN.sub(r"\1***@", value or "")


def _run_git(repo_path, *arguments):
    environment = os.environ.copy()
    environment["GIT_TERMINAL_PROMPT"] = "0"

    result = subprocess.run(
        ["git", "-C", str(repo_path), *arguments],
        capture_output=True,
        text=True,
        timeout=120,
        env=environment,
    )

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "Git command failed."
        raise RuntimeError(_redact_credentials(message))

    return _redact_credentials(result.stdout.strip())


def pull_github_repo(repo_name, clone_root=None):
    """Fast-forward an existing repository under the ProxAI clone directory."""
    if not isinstance(repo_name, str) or not repo_name.strip():
        raise ValueError("repo_name must be a non-empty local repository name.")

    repo_name = repo_name.strip()
    if Path(repo_name).name != repo_name or repo_name in {".", ".."}:
        raise ValueError("repo_name must be a local repository name, not a path.")

    root = (
        Path(clone_root).expanduser().resolve()
        if clone_root is not None
        else GITHUB_REPOS_DIR.resolve()
    )
    repo_path = (root / repo_name).resolve()

    if not repo_path.is_relative_to(root):
        raise ValueError("Repository path escapes the GitHub repository directory.")

    if not repo_path.is_dir() or not (repo_path / ".git").exists():
        raise FileNotFoundError(
            f"Repository '{repo_name}' is not cloned under {root}."
        )

    if _run_git(repo_path, "status", "--porcelain"):
        return {
            "success": False,
            "repo": repo_name,
            "path": str(repo_path),
            "error": "Repository has uncommitted changes; pull was not attempted.",
        }

    branch = _run_git(repo_path, "branch", "--show-current")
    if not branch:
        return {
            "success": False,
            "repo": repo_name,
            "path": str(repo_path),
            "error": "Repository has a detached HEAD; pull was not attempted.",
        }

    before_commit = _run_git(repo_path, "rev-parse", "HEAD")
    output = _run_git(repo_path, "pull", "--ff-only")
    after_commit = _run_git(repo_path, "rev-parse", "HEAD")

    return {
        "success": True,
        "repo": repo_name,
        "path": str(repo_path),
        "branch": branch,
        "before_commit": before_commit,
        "after_commit": after_commit,
        "updated": before_commit != after_commit,
        "output": output,
    }
