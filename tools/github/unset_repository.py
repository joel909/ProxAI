from var_files import unset_active_repository_path


def unset_repository():
    """Clear the repository used as the default shell working directory."""
    previous_path = unset_active_repository_path()
    return {
        "success": True,
        "previous_path": str(previous_path) if previous_path is not None else None,
        "message": "Active repository path unset.",
    }
