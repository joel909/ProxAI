from inputs import RED, RESET


def show_github_pat_setup_instructions():
    print(
        "GitHub setup: use a fine-grained personal access token (PAT).\n"
        "1. Open GitHub → profile picture → Settings → Developer settings → "
        "Personal access tokens → Fine-grained tokens.\n"
        "2. Select Generate new token, give it a name, and choose the correct "
        "resource owner.\n"
        f"3. Under Repository access, choose {RED}All repositories{RESET} if this tool needs "
        "access to your private repositories; otherwise select only the repositories "
        "it needs.\n"
        f"4. Keep the {RED}expiration date{RESET} in mind: the token will stop working when it "
        "expires, so renew or update it here before that date.\n"
        "Create the token at: https://github.com/settings/personal-access-tokens/new"
    )
