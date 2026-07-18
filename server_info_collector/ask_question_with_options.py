from inputs import CYAN, RESET, select_menu


def ask_question_with_options(question, options):
    if not options:
        raise ValueError("ask_question_with_options requires at least one option.")
    return select_menu(
        options,
        f"{CYAN}{question}{RESET}",
    )
