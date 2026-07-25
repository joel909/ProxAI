import os
import shutil

from inputs import GREEN, RED, RESET
from inputs.terminal_ui import select_menu
from tools.github.fetch_repos import fetch_repos
from tools.github.clone_repo import clone_github_repo


def validate_github_pull_with_PAT(PAT_token):
    private_repo_access = False
    test_clone_repo_path = "test-clone"
    if os.path.exists(test_clone_repo_path):
        shutil.rmtree(test_clone_repo_path)
    try:
        try:
            try:
                repos = fetch_repos(PAT_token)
            except Exception as e:
                print(
                    f"{RED}Invalid API token. Please check your token and permissions, "
                    f"and make sure it is a PAT (classic). eror is {str(e)}{RESET}"
                )
                return
            repos = fetch_repos(PAT_token, repo_type="private")
            private_repo_access = bool(repos)
        except Exception as e:
            private_repo_access = False

        if private_repo_access == False:
            print(
                f"{RED}No Private repositories found. Check that your PAT has the repo scope "
                "enabled for private repositories. If you do not have private repositories, "
                f"you can ignore this message.{RESET}"
            )
            public_repo_action = select_menu(
                ["Exit", "Continue with public repositories only"],
                f"{RED}You will not be able to pull any private repositories in your "
                f"account.{RESET}\nChoose how to continue:",
            )
            if public_repo_action == "Exit":
                return
            else:
                #fetch Repo code
                repos = fetch_repos(PAT_token, repo_type="public")
                if not repos:
                    print(f"{RED}No public repositories found on your account. If this is false please check token permissions{RESET}")
                    return
                else:
                    sample_repo_name = repos[0]["full_name"]
                    try:
                        clone_status = clone_github_repo(PAT_token, sample_repo_name, test_clone_repo_path)
                        try:
                            if os.path.exists(test_clone_repo_path):
                                shutil.rmtree(test_clone_repo_path)
                                print(f"{GREEN}Test clone repository removed successfully.{RESET}")
                        except Exception as e:
                            print(f"{RED}Error occurred while removing test clone repository: {str(e)}{RESET}")
                            print(f"{RED}Please manually remove the test clone repository at {test_clone_repo_path}.{RESET}")
                        if clone_status == False:
                            print(f"{RED}Clone failed. Check token scope and permissions and token expiration.{RESET}")
                            return
                    except Exception as e:
                        print(f"{RED}Error occurred while cloning public repository: {str(e)}{RESET}")
                        return
        else:       
            sample_repo_name = repos[0]["full_name"]
            try:
                clone_status = clone_github_repo(PAT_token, sample_repo_name, test_clone_repo_path)
                ## code to remove file where repo was cloned
                try:
                    if os.path.exists(test_clone_repo_path):
                        shutil.rmtree(test_clone_repo_path)
                        print(f"{GREEN}Test clone repository removed successfully.{RESET}")
                except Exception as e:
                    print(f"{RED}Error occurred while removing test clone repository: {str(e)}{RESET}")
                    print(f"{RED}Please manually remove the test clone repository at {test_clone_repo_path}.{RESET}")
                if clone_status == False:
                    print(f"{RED}Clone failed. Check token scope and permissions and token expiration.{RESET}")
                    return
            except Exception as e:
                print(f"{RED}Error occurred while cloning private repository: {str(e)}{RESET}")
                return
        return True
    except Exception as e:
        print(f"{RED}Error occurred while validating GitHub PAT :  {str(e)}{RESET}")
