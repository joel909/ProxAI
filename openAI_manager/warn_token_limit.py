from inputs.terminal_ui import select_menu


RED = "\033[31m"
RESET = "\033[0m"


def warn_token_limit(estimated_tokens, limit):
    """
    Warn the user when the estimated token usage is over the configured limit.

    Returns True if the request should continue, False otherwise.
    """
    if estimated_tokens <= limit:
        return True

    over_by = estimated_tokens - limit

    print(
        f"{RED}Warning: estimated token usage is over {limit}. "
        f"This request is estimated to consume {estimated_tokens} tokens "
        f"({over_by} over the limit).{RESET}"
    )

    selected_option = select_menu(
        ["Yes", "No"],
        "Continue with this request?",
    )

    return selected_option == "Yes"
