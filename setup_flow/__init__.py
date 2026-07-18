from .check_setup_files import check_setup_files
from .collect_device_info import collect_device_info
from .generate_manifest import generate_manifest

class SetupFlow():
    def __init__(self,llm_manager) -> None:
        pass
        self.llm_manager = llm_manager

    def check_setup_files(self) -> bool:
        return check_setup_files()

    def is_setup_completed(self) -> bool:
        return self.check_setup_files()

    def begin_setup_flow(self):
        if self.is_setup_completed():
                print("Setup is complete. You can now use the application.")
        else:
            # print("Setup is not complete. Please follow the prompts to complete the setup.")
            collect_device_info(self.llm_manager, self.is_setup_completed)
