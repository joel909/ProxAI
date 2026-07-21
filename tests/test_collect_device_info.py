import importlib
import os
import unittest
from unittest.mock import Mock, patch


class CollectDeviceInfoTests(unittest.TestCase):
    def test_recovery_prompt_includes_current_manifest_generator_source(self):
        module = importlib.import_module("server_info_collector.build_input_messages")

        messages = module.build_input_messages("Please repair the failed manifest generator.")
        contents = [message["content"] for message in messages]

        self.assertTrue(any("def build_manifest():" in content for content in contents))
        self.assertTrue(any("edit_manifest_code" in content for content in contents))

    def test_manifest_failure_hook_is_opt_in(self):
        module = importlib.import_module("setup_flow.generate_manifest")

        with (
            patch.dict(os.environ, {"PROXAI_TEST_MANIFEST_FAILURE": "1"}),
            patch.object(module, "_TEST_FAILURE_TRIGGERED", False),
        ):
            self.assertTrue(module.is_manifest_failure_test_pending())
            with self.assertRaisesRegex(RuntimeError, "Intentional manifest-generation"):
                module.generate_manifests()
            self.assertFalse(module.is_manifest_failure_test_pending())

    def test_successful_manifest_generation_does_not_start_ai_repair(self):
        module = importlib.import_module("setup_flow.collect_device_info")
        spinner = Mock()

        with (
            patch.object(module, "LoadingSpinner", return_value=spinner),
            patch.object(module, "generate_manifests") as generate_manifests,
            patch.object(module, "generate_new_manifest_generating_code") as repair,
            patch.object(module, "select_menu") as select_menu,
        ):
            module.collect_device_info(Mock(), lambda: True)

        generate_manifests.assert_called_once()
        repair.assert_not_called()
        select_menu.assert_not_called()

    def test_exit_after_manifest_failure_does_not_start_ai_repair(self):
        module = importlib.import_module("setup_flow.collect_device_info")
        spinner = Mock()

        with (
            patch.object(module, "LoadingSpinner", return_value=spinner),
            patch.object(
                module,
                "generate_manifests",
                side_effect=RuntimeError("intentional test failure"),
            ),
            patch.object(module, "generate_new_manifest_generating_code") as repair,
            patch.object(module, "select_menu", return_value="Exit"),
        ):
            module.collect_device_info(Mock(), lambda: False)

        spinner.stop.assert_called_once()
        repair.assert_not_called()


if __name__ == "__main__":
    unittest.main()
