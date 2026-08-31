from inputs.terminal_ui import WRITE_CONFIRM_YES, confirm_user_permission


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

    permission = confirm_user_permission(
        action="Token usage warning",
        details={
            "Configured limit": limit,
            "Estimated tokens": estimated_tokens,
            "Over limit by": over_by,
        },
        yes_label="Yes, continue",
        no_label="No, cancel",
        prompt="Continue with this request?",
    )

    return permission == WRITE_CONFIRM_YES
