import io
import sys
import unittest
from unittest import mock

from inputs import terminal_ui


class TerminalMenuRenderingTests(unittest.TestCase):
    def test_long_prompt_counts_wrapped_rows(self):
        prompt = (
            "Is this machine intentionally reachable from the public internet, "
            "for example via router port forwarding, IPv6 firewall allow-rules, "
            "VPN tunnel, or a reverse proxy/tunnel?"
        )
        options = [
            "No, private home network only",
            "Yes, via router port forwarding",
            "Yes, via public IPv6",
            "Yes, via tunnel/reverse proxy/VPN",
            "Not sure",
        ]

        with mock.patch.object(terminal_ui, "_terminal_width", return_value=40):
            with mock.patch.object(sys, "stdout", new=io.StringIO()) as stdout:
                line_count = terminal_ui._draw_menu(options, prompt, 0)

        self.assertGreater(line_count, len(options) + 1)
        self.assertIn(f"\033[{line_count}A", stdout.getvalue())

    def test_redraw_clears_previous_wrapped_frame(self):
        previous_line_count = 7

        with mock.patch.object(terminal_ui, "_terminal_width", return_value=40):
            with mock.patch.object(sys, "stdout", new=io.StringIO()) as stdout:
                terminal_ui._draw_menu(
                    ["First", "Second"],
                    "A prompt that is long enough to wrap across rows",
                    1,
                    previous_line_count=previous_line_count,
                )

        self.assertGreaterEqual(
            stdout.getvalue().count(terminal_ui.CLEAR_LINE),
            previous_line_count,
        )


if __name__ == "__main__":
    unittest.main()
