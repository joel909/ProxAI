import importlib.util
from pathlib import Path


CHECK_SETUP_FILES_PATH = Path(__file__).with_name("check_setup_files.py")
CHECK_SETUP_FILES_SPEC = importlib.util.spec_from_file_location(
    "check_setup_files",
    CHECK_SETUP_FILES_PATH,
)

if CHECK_SETUP_FILES_SPEC is None or CHECK_SETUP_FILES_SPEC.loader is None:
    raise ImportError("Could not load check_setup_files.py")

check_setup_files_module = importlib.util.module_from_spec(CHECK_SETUP_FILES_SPEC)
CHECK_SETUP_FILES_SPEC.loader.exec_module(check_setup_files_module)
check_setup_files = check_setup_files_module.check_setup_files


class SetupFlow():
    def __init__(self,llm_manager,chat_history_manager) -> None:
        pass
        self.llm_manager = llm_manager
        self.chat_history_manager = chat_history_manager

    def is_steup_compleated(self) -> bool:
        return check_setup_files(verbose=False)
    def begin_setup_flow(self):
        if self.is_steup_compleated():
                print("Setup is complete. You can now use the application.")
        while True:
                print("Setup is not complete. Please follow the prompts to complete the setup.")
                check_setup_files(verbose=True)
