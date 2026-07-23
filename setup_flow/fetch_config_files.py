from pathlib import Path
from .check_setup_files import check_setup_files

def fetch_config_file():
    ROOT_DIR = Path(__file__).resolve().parents[1]
    root_path =  ROOT_DIR
    manifest_path = root_path / "manifest.json"
    try:
        if check_setup_files():
            content = manifest_path.read_text()
            return (content)
        else:
            return "COULD NOT FIND SETUP FILES"
    except Exception as e :
        return f"COULD NOT FIND SETUP FILES BACAUSE \n {e}" 