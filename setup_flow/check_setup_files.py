from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def check_setup_files(root_dir: Path | None = None) -> bool:
    root_path = root_dir or ROOT_DIR
    return (root_path / "manifest.json").exists()
