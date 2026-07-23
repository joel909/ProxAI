from .check_setup_files import check_setup_files
from .collect_device_info import collect_device_info
from .generate_manifest import (
    generate_manifests,
    is_manifest_failure_test_pending,
    run_all,
)
from .fetch_config_files import fetch_config_file
class SetupFlow():
    def __init__(self,llm_manager) -> None:
        pass
        self.llm_manager = llm_manager

    def check_setup_files(self) -> bool:
        return check_setup_files()

    def is_setup_completed(self) -> bool:
        if is_manifest_failure_test_pending():
            return False
        return self.check_setup_files()

    def begin_setup_flow(self):
        # print("Setup is not complete. Please follow the prompts to complete the setup.")
        collect_device_info(self.llm_manager, self.is_setup_completed)
    def fetch_config_files(self):
        return fetch_config_file()

