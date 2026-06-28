import base64
import itertools
import re
import shutil
import subprocess
import sys
import textwrap
import threading
import time

RED = "\033[31m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"
CLEAR_LINE = "\r\033[K"

CODE_FENCE_RE = re.compile(r"^```(\w+)?\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
ORDERED_LIST_RE = re.compile(r"^(\s*)(\d+)\.\s+(.+)$")
UNORDERED_LIST_RE = re.compile(r"^(\s*)[-*]\s+(.+)$")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
LAST_CODE_BLOCKS = []


class LoadingSpinner:
    def __init__(self, text="Thinking"):
        self.text = text
        self._frames = itertools.cycle("|/-\\")
        self._stop_event = threading.Event()
        self._thread = None

    def _spin(self):
        while not self._stop_event.is_set():
            frame = next(self._frames)
            sys.stdout.write(f"\r{frame} {self.text}...")
            sys.stdout.flush()
            time.sleep(0.1)

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join()
        sys.stdout.write(CLEAR_LINE)
        sys.stdout.flush()


def render_assistant_response(text):
    if not text:
        return ""

    LAST_CODE_BLOCKS.clear()
    width = _terminal_width()
    lines = text.splitlines()
    rendered_lines = []
    in_code_block = False
    code_language = ""
    code_lines = []

    for line in lines:
        fence_match = CODE_FENCE_RE.match(line)
        if fence_match:
            if in_code_block:
                rendered_lines.extend(_render_code_block(code_lines, code_language, width))
                code_lines = []
                code_language = ""
                in_code_block = False
            else:
                in_code_block = True
                code_language = fence_match.group(1) or ""
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        rendered_lines.extend(_render_markdown_line(line, width))

    if in_code_block:
        rendered_lines.extend(_render_code_block(code_lines, code_language, width))

    return "\n".join(rendered_lines)


def print_assistant_response(text):
    print(render_assistant_response(text))


def copy_code_block(index):
    if not LAST_CODE_BLOCKS:
        return False, "No code blocks available to copy."

    if index < 1 or index > len(LAST_CODE_BLOCKS):
        return False, f"No code block #{index}. Available: 1-{len(LAST_CODE_BLOCKS)}."

    code = LAST_CODE_BLOCKS[index - 1]
    clipboard_command = _clipboard_command()
    if clipboard_command is None:
        _copy_with_osc52(code)
        return True, f"Sent code block #{index} to the terminal clipboard."

    try:
        subprocess.run(
            clipboard_command,
            input=code,
            text=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        return False, f"Could not copy code block #{index}: {e}"

    return True, f"Copied code block #{index}."


def _render_markdown_line(line, width):
    if line == "":
        return [""]

    heading_match = HEADING_RE.match(line)
    if heading_match:
        level = len(heading_match.group(1))
        heading = heading_match.group(2).strip()
        if level == 1:
            return ["", f"{BOLD}{MAGENTA}{heading.upper()}{RESET}", f"{MAGENTA}{'=' * len(heading)}{RESET}"]
        if level == 2:
            return ["", f"{BOLD}{CYAN}{heading}{RESET}", f"{CYAN}{'-' * len(heading)}{RESET}"]
        return [f"{BOLD}{YELLOW}{heading}{RESET}"]

    ordered_match = ORDERED_LIST_RE.match(line)
    if ordered_match:
        indent, number, content = ordered_match.groups()
        prefix = f"{indent}{number}. "
        wrapped = _wrap_text(content, width - len(prefix), " " * len(prefix))
        return [
            f"{indent}{CYAN}{number}.{RESET} {_style_inline(wrapped[0])}",
            *[_style_inline(line) for line in wrapped[1:]],
        ]

    unordered_match = UNORDERED_LIST_RE.match(line)
    if unordered_match:
        indent, content = unordered_match.groups()
        prefix = f"{indent}* "
        wrapped = _wrap_text(content, width - len(prefix), " " * len(prefix))
        return [
            f"{indent}{CYAN}*{RESET} {_style_inline(wrapped[0])}",
            *[_style_inline(line) for line in wrapped[1:]],
        ]

    if line.startswith(">"):
        wrapped = _wrap_text(line, width, "> ")
        return [f"{DIM}{line}{RESET}" for line in wrapped]

    return [_style_inline(line) for line in _wrap_text(line, width, "")]


def _render_code_block(lines, language, terminal_width):
    if not lines:
        lines = [""]

    LAST_CODE_BLOCKS.append("\n".join(lines))
    block_number = len(LAST_CODE_BLOCKS)
    content_width = max(len(_strip_ansi(line)) for line in lines)
    label_name = language or "code"
    label = f" {label_name}  [copy: /copy {block_number}] "
    max_box_width = max(24, terminal_width - 4)
    if len(label) > max_box_width:
        label = f" code #{block_number} "
    box_width = min(max(content_width, len(label), 24), max_box_width)
    top = f"{DIM}+{label}{'-' * max(0, box_width - len(label))}+{RESET}"
    bottom = f"{DIM}+{'-' * box_width}+{RESET}"
    rendered = ["", top]

    for line in lines:
        for part in _wrap_code_line(line, box_width):
            padding = " " * (box_width - len(part))
            rendered.append(f"{DIM}|{RESET}{GREEN}{part}{padding}{RESET}{DIM}|{RESET}")

    rendered.append(bottom)
    return rendered


def _wrap_code_line(line, width):
    if len(line) <= width:
        return [line]

    return [line[index : index + width] for index in range(0, len(line), width)]


def _style_inline(line):
    return INLINE_CODE_RE.sub(lambda match: f"{GREEN}{match.group(1)}{RESET}", line)


def _wrap_text(text, width, subsequent_indent):
    width = max(24, width)
    return textwrap.wrap(
        text,
        width=width,
        subsequent_indent=subsequent_indent,
        break_long_words=False,
        break_on_hyphens=False,
    ) or [""]


def _terminal_width():
    return shutil.get_terminal_size(fallback=(80, 24)).columns


def _strip_ansi(text):
    return re.sub(r"\033\[[0-9;]*m", "", text)


def _clipboard_command():
    if shutil.which("wl-copy"):
        return ["wl-copy"]
    if shutil.which("xclip"):
        return ["xclip", "-selection", "clipboard"]
    if shutil.which("xsel"):
        return ["xsel", "--clipboard", "--input"]
    if shutil.which("pbcopy"):
        return ["pbcopy"]
    if shutil.which("clip.exe"):
        return ["clip.exe"]

    return None


def _copy_with_osc52(text):
    encoded = base64.b64encode(text.encode()).decode()
    sys.stdout.write(f"\033]52;c;{encoded}\a")
    sys.stdout.flush()
