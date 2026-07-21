def edit_manifest_generating_code(new_code: str):
    """Replace the existing manifest generator with new code."""
    from setup_flow.generate_manifest import GENERATOR_FILE_PATH
    try:
        with open(GENERATOR_FILE_PATH, "w") as f:
            f.write(new_code)
        print(f"Successfully updated {GENERATOR_FILE_PATH}.")
    except Exception as e:
        print(f"Failed to update {GENERATOR_FILE_PATH}: {e}")