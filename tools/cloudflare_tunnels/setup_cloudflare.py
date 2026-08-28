import subprocess
import re
from pathlib import Path

from inputs import CYAN, GREEN, Inputs, RED, RESET, YELLOW, select_menu
from storage.tool_credentials import save_tool_api_key

from .validate_cloudflare_token import (
    validate_cloudflare_edit_permissions,
    validate_cloudflare_token,
)


CLOUDFLARE_API_TOKENS_URL = "https://dash.cloudflare.com/profile/api-tokens"
PERMISSION_GUIDE_IMAGE = (
    Path(__file__).resolve().parents[2]
    / "assets"
    / "cloudflare-token-permissions.png"
)
PERMISSION_FAILURE_STAGES = {
    "zone_access",
    "dns_access",
    "tunnel_access",
    "dns_edit",
    "tunnel_edit",
}


def show_cloudflare_permission_guide():
    print(
        f"{CYAN}Open Cloudflare Profile > API Tokens:{RESET}\n"
        f"{CLOUDFLARE_API_TOKENS_URL}\n\n"
        "Create or edit a custom token so its permissions match:\n"
        "  Account > Cloudflare Tunnel > Edit\n"
        "  Zone > DNS > Edit\n"
        "Also assign the intended account and zone resources.\n"
        f"Permission screenshot: {PERMISSION_GUIDE_IMAGE}"
    )

    if not PERMISSION_GUIDE_IMAGE.is_file():
        print(f"{RED}Permission screenshot is missing.{RESET}")
        return False

    try:
        subprocess.Popen(
            ["xdg-open", str(PERMISSION_GUIDE_IMAGE)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        print(f"{RED}Could not open the screenshot automatically: {exc}{RESET}")
        return False

    return True


def _select_item(items, prompt):
    if len(items) == 1:
        return items[0]

    labels = [f'{item["name"]} ({item["id"]})' for item in items]
    selected_label = select_menu(labels, prompt)
    return items[labels.index(selected_label)]


def _request_cloudflare_account_id():
    while True:
        account_id = Inputs.getInput(
            f"{CYAN}Enter your 32-character Cloudflare Account ID{RESET}",
            result_type=str,
        ).strip()
        if re.fullmatch(r"[0-9a-fA-F]{32}", account_id):
            return account_id.lower()

        print(f"{RED}Cloudflare Account ID must contain 32 hexadecimal characters.{RESET}")


def setup_cloudflare_token():
    """Validate, explain failures, and save a working Cloudflare token."""
    api_token = Inputs.getInput(
        f"{CYAN}Enter your Cloudflare API token{RESET}",
        result_type=str,
    ).strip()

    validation = validate_cloudflare_token(api_token)
    if not validation["valid"]:
        stage = validation["stage"].replace("_", " ")
        error = validation["error"]
        print(f"{RED}Cloudflare setup failed during {stage}: {error}{RESET}")
        if validation["stage"] in PERMISSION_FAILURE_STAGES:
            show_cloudflare_permission_guide()
        return {
            "success": False,
            "stage": validation["stage"],
            "error": error,
        }

    use_default_domain = not validation["zones"]
    if use_default_domain:
        print(
            f"{YELLOW}No Cloudflare domain found. Enter your Account ID to "
            f"continue. Deployment will use its default domain.{RESET}"
        )
        account_id = _request_cloudflare_account_id()
        account = {"id": account_id, "name": "Cloudflare account"}
        zone = None
    else:
        account = _select_item(
            validation["accounts"],
            "Select a Cloudflare account",
        )
        account_zones = [
            zone
            for zone in validation["zones"]
            if zone["account_id"] == account["id"]
        ]
        zone = _select_item(account_zones, "Select a Cloudflare zone")

    edit_validation = validate_cloudflare_edit_permissions(
        api_token,
        account["id"],
        zone["id"] if zone else None,
        zone["name"] if zone else None,
    )
    if not edit_validation["valid"]:
        stage = edit_validation["stage"].replace("_", " ")
        error = edit_validation["error"]
        print(f"{RED}Cloudflare setup failed during {stage}: {error}{RESET}")
        if edit_validation["stage"] in PERMISSION_FAILURE_STAGES:
            show_cloudflare_permission_guide()
        return {
            "success": False,
            "stage": edit_validation["stage"],
            "error": error,
        }

    save_tool_api_key(
        "Cloudflare",
        api_token,
        config={
            "account_id": account["id"],
            "account_name": account["name"],
            "zone_id": zone["id"] if zone else None,
            "zone_name": zone["name"] if zone else None,
            "use_default_domain": use_default_domain,
        },
    )
    if use_default_domain:
        message = (
            f'Cloudflare API token saved for account {account["id"]}. '
            "Deployment will use its default domain."
        )
    else:
        message = (
            f'Cloudflare API token saved for account {account["name"]} '
            f'and zone {zone["name"]}.'
        )
    print(f"{GREEN}{message}{RESET}")
    return {
        "success": True,
        "message": message,
        "account_id": account["id"],
        "account_name": account["name"],
        "zone_id": zone["id"] if zone else None,
        "zone_name": zone["name"] if zone else None,
        "use_default_domain": use_default_domain,
        "permissions": {
            **validation["permissions"],
            **edit_validation["permissions"],
        },
    }
