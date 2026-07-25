from inputs import RED, RESET
from inputs.service import Inputs
from inputs.terminal_ui import CYAN, GREEN
from storage.tool_credentials import save_tool_api_key
from tools.setup_tools.validate_github_pull_with_PAT import validate_github_pull_with_PAT


def show_github_pat_setup_instructions():
    print(
        f"GitHub setup: use a {RED}personal access token (classic){RESET} (PAT).\n"
        "1. Open GitHub → profile picture → Settings → Developer settings → "
        f"Personal access tokens → {RED}Tokens (classic){RESET}.\n"
        "2. Select Generate new token → Generate new token (classic), then give "
        "it a descriptive name.\n"
        f"3. Select the repo scope to enable access to {RED}private repositories{RESET}.\n"
        f"4. Keep the {RED}expiration date{RESET} in mind: the token will stop working when it "
        "expires, so renew or update it here before that date.\n"
        "Create the token at: https://github.com/settings/personal-access-tokens/new"
    )
    PAT = Inputs.getInput(
        f"{CYAN}Enter your GitHub personal access token (classic){RESET}",
        result_type=str,
    )
    try:
        github_setup_status = validate_github_pull_with_PAT(PAT)
        if github_setup_status is None or github_setup_status == False:
            print(f"{RED}GitHub PAT validation failed.{RESET}")
            return False
        else:
            save_tool_api_key("github", PAT)
            print(f"{GREEN}GitHub PAT token saved.{RESET}")
            return True

    except Exception as e:
        print(f"{RED}itHub PAT validation failed. {str(e)}{RESET}")
        return False
    # print(f"{GREEN}GitHub PAT token saved.{RESET}")
