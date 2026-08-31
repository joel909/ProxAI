import unittest
from unittest import mock

from inputs.terminal_ui import (
    WRITE_CONFIRM_DENY,
    WRITE_CONFIRM_YES,
    reset_permission_handler,
    set_permission_handler,
)
from openAI_manager.warn_token_limit import warn_token_limit


class WarnTokenLimitTests(unittest.TestCase):
    def test_under_limit_does_not_request_input(self):
        with mock.patch(
            "openAI_manager.warn_token_limit.confirm_user_permission"
        ) as confirm:
            self.assertTrue(warn_token_limit(99, 100))
        confirm.assert_not_called()

    def test_dashboard_handler_automatically_continues_over_limit(self):
        token = set_permission_handler(lambda **_kwargs: WRITE_CONFIRM_YES)
        try:
            self.assertTrue(warn_token_limit(150, 100))
        finally:
            reset_permission_handler(token)

    def test_denied_warning_cancels_request(self):
        token = set_permission_handler(lambda **_kwargs: WRITE_CONFIRM_DENY)
        try:
            self.assertFalse(warn_token_limit(150, 100))
        finally:
            reset_permission_handler(token)


if __name__ == "__main__":
    unittest.main()
