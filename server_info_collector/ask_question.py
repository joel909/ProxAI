from inputs import CYAN, Inputs, RED, RESET, YELLOW, select_menu

def ask_question(question: str) -> str:
    result = Inputs.getInput(f"{CYAN}{question}{RESET}", result_type=str)
    return result