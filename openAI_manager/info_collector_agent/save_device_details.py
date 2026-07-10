import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_FILE = PROJECT_ROOT / "manifest.json"


def save_device_details(data):
    if isinstance(data, str):
        try:
            manifest_data = json.loads(data)
        except json.JSONDecodeError:
            return "error failed invalid type input is not json please try again"
    elif isinstance(data, (dict, list)):
        manifest_data = data
    else:
        return "error failed invalid type input is not json please try again"

    try:
        manifest_content = json.dumps(manifest_data, indent=2)
    except TypeError:
        return "error failed invalid type input is not json please try again"

    with MANIFEST_FILE.open("w", encoding="utf-8") as manifest:
        manifest.write(manifest_content)
        manifest.write("\n")

    return "success manifest.json saved successfully, setup worked"
