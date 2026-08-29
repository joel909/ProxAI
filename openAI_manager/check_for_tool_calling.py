"""Backward-compatible alias for the renamed tool-calling module."""

import sys

from . import tool_calling_logic as _tool_calling_logic


sys.modules[__name__] = _tool_calling_logic
