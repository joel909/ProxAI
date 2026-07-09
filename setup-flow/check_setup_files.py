from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MANIFEST_FILE = ROOT_DIR / "manifest.json"
MISSPELLED_MANIFEST_FILE = ROOT_DIR / "maniefest.json"


def check_setup_files(root_dir: Path | None = None, verbose: bool = True) -> bool:
    root_path = root_dir or ROOT_DIR
    manifest_file = root_path / "manifest.json"
    misspelled_manifest_file = root_path / "maniefest.json"

    if manifest_file.exists():
        if verbose:
            print("OK: manifest.json exists.")
        return True

    if misspelled_manifest_file.exists():
        if verbose:
            print("ERROR: Found maniefest.json, but the correct filename is manifest.json.")
            print("Rename maniefest.json to manifest.json.")
        return False

    if verbose:
        print("ERROR: manifest.json is missing.")
        print("Expected file: manifest.json")
        print("Common typo to avoid: maniefest.json")
    return False


def main() -> int:
    return 0 if check_setup_files() else 1


if __name__ == "__main__":
    raise SystemExit(main())
