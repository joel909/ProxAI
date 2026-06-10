class Inputs:
    @staticmethod
    def getInput(question, default=None, result_type=str):
        while True:
            raw = input(f"{question} (default: {default}): ").strip()

            if raw == "":
                if default is not None:
                    return default
                print("This field is required. Try again.")
                continue

            try:
                if result_type is bool:
                    lowered = raw.lower()
                    if lowered in ("true", "t", "yes", "y", "1"):
                        return True
                    if lowered in ("false", "f", "no", "n", "0"):
                        return False
                    raise ValueError

                value = result_type(raw)
                if not isinstance(value, result_type):
                    raise TypeError
                return value
            except (ValueError, TypeError):
                print(f"Invalid input type. Expected {result_type.__name__}. Try again.")

    def getInputWithOptions(question, options, default=None):
        while True:
            print(f"{question}")
            for i, option in enumerate(options, start=1):
                print(f"{i}. {option}")

            raw = input(f"Enter your choice (default: {default}): ").strip()

            if raw == "" and default is not None:
                return default

            try:
                choice = int(raw)
            except ValueError:
                print("Invalid choice. Enter a number from the list.")
                continue

            if 1 <= choice <= len(options):
                return options[choice - 1]

            print("Invalid choice. Try again.")
