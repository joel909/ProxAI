import os
import unittest
from unittest import mock

from inputs.terminal_ui import (
    WRITE_CONFIRM_DENY,
    WRITE_CONFIRM_YES,
    confirm_user_permission,
    reset_permission_handler,
    set_permission_handler,
)


class DashboardPermissionTests(unittest.TestCase):
    def test_request_local_handler_can_approve(self):
        token = set_permission_handler(lambda **_kwargs: WRITE_CONFIRM_YES)
        try:
            self.assertEqual(confirm_user_permission("Run"), WRITE_CONFIRM_YES)
        finally:
            reset_permission_handler(token)


class ConversationHistoryTests(unittest.TestCase):
    def test_manager_can_resume_an_existing_conversation_id(self):
        from storage import ChatHistoryManager

        manager = ChatHistoryManager(conversation_id="existing-conversation")
        self.assertEqual(manager.conversation_id, "existing-conversation")

    def test_request_local_handler_can_deny(self):
        token = set_permission_handler(lambda **_kwargs: WRITE_CONFIRM_DENY)
        try:
            self.assertEqual(confirm_user_permission("Run"), WRITE_CONFIRM_DENY)
        finally:
            reset_permission_handler(token)


try:
    from dashboard.app import access_denial
except ModuleNotFoundError:
    access_denial = None


@unittest.skipIf(access_denial is None, "dashboard dependencies are not installed")
class DashboardAccessTests(unittest.TestCase):
    def test_access_jwt_can_be_required(self):
        with mock.patch.dict(
            os.environ,
            {"PROXAI_REQUIRE_CLOUDFLARE_ACCESS": "true"},
            clear=False,
        ):
            self.assertIn("required", access_denial({}))
            self.assertIsNone(
                access_denial({"cf-access-jwt-assertion": "token"})
            )


if __name__ == "__main__":
    unittest.main()
