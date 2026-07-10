from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MANIFEST_FILE = ROOT_DIR / "manifest.json"
MISSPELLED_MANIFEST_FILE = ROOT_DIR / "maniefest.json"


def check_setup_files(root_dir: Path | None = None) -> bool:
    root_path = root_dir or ROOT_DIR
    manifest_file = root_path / "manifest.json"
    misspelled_manifest_file = root_path / "maniefest.json"

    if manifest_file.exists():
        return True

    if misspelled_manifest_file.exists():
        return False

    return False

