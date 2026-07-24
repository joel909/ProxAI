import os
import re

from inputs.terminal_ui import BOLD, BRIGHT_RED, RESET, WRITE_CONFIRM_YES, confirm_user_permission
from tools.destop_tools.run_shell import run_shell_command
from .read_file import read_file
from .write_file import write_file


SYSTEM_RISK_WARNING = "[[running this code might break system]]"
SYSTEM_RISK_COMMAND_RE = re.compile(
    r"(^|\s)(sudo|su|doas|pkexec|"
    r"rm\s+-[^\n;|&]*[rf][^\n;|&]*(\s+/|\s+\*|\s+~)|"
    r"chmod\s+[-+0-7a-zA-Z,]+\s+(/|~)|"
    r"chown\s+[-:_.a-zA-Z0-9]+\s+(/|~)|"
    r"mkfs(\.|$)|dd\s+|fdisk|parted|mount\s+|umount\s+|"
    r"systemctl\s+(start|stop|restart|reload|disable|enable)|"
    r"service\s+\S+\s+(start|stop|restart|reload)|"
    r"apt(-get)?\s+(install|remove|purge|upgrade|dist-upgrade)|"
    r"dnf\s+(install|remove|upgrade)|yum\s+(install|remove|upgrade)|"
    r"pacman\s+-S|brew\s+(install|uninstall|upgrade)|"
    r"curl\b[^\n]*\|\s*(sh|bash)|wget\b[^\n]*\|\s*(sh|bash)|"
    r">+\s*/(etc|usr|bin|sbin|lib|boot|var)/)",
    re.IGNORECASE,
)


class DesktopTools:
    def read_file(self, filePath):
        try:
            content = read_file(filePath)
            return {
                "status": "read",
                "file_path": filePath,
                "content": content,
            }
        except Exception as e:
            return {
                "status": "error",
                "file_path": filePath,
                "message": f"Error occurred while reading file: {str(e)}",
            }

    def write_to_file(self, filePath, content, filename):
        full_path = os.path.join(filePath, filename)
        permission = confirm_user_permission(
            action="Write file requested",
            details={
                "File": os.path.abspath(full_path),
                "Content": f"{len(str(content).splitlines()) or 1} line(s), {len(str(content).encode())} byte(s)",
            },
            yes_label="Yes, write file",
            no_label="No, deny write",
            prompt="Allow this write?",
        )
        if permission != WRITE_CONFIRM_YES:
            return {
                "status": "denied",
                "file_path": full_path,
                "message": "User denied the file write.",
            }
        try:
            written_path = write_file(filePath, content, filename)
            return {
                "status": "written",
                "file_path": written_path,
                "message": "File written successfully.",
            }
        except Exception as e:
            return {
                "status": "error",
                "file_path": full_path,
                "message": f"Error occurred while writing file: {str(e)}",
            }
        
    def check_and_run_shell_command(self, command):
        details = {
            "Command": command,
        }
        if _command_might_affect_system(command):
            details["Warning"] = f"{BOLD}{BRIGHT_RED}{SYSTEM_RISK_WARNING}{RESET}"

        permission = confirm_user_permission(
            action="Run shell command",
            details=details,
            yes_label="Yes, run command",
            no_label="No, deny command",
            prompt="Allow this command?",
        )
        if permission == WRITE_CONFIRM_YES:
            return run_shell_command(command)
        else:
            return {"output": None, "error": "User denied the command."}


def _command_might_affect_system(command):
    return bool(SYSTEM_RISK_COMMAND_RE.search(command))
