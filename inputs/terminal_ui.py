import base64
import itertools
import os
import re
import shutil
import subprocess
import sys
import termios
import textwrap
import threading
import time
import tty

RED = "\033[31m"
BRIGHT_RED = "\033[91m"
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
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
WARNING_BLOCK_RE = re.compile(r"\[\[([^\]]+)\]\]")
INLINE_STYLE_RE = re.compile(
    r"`([^`]+)`|\[\[([^\]]+)\]\]|\*\*([^*]+)\*\*|(?<!\*)\*([^*]+)\*(?!\*)"
)
LAST_CODE_BLOCKS = []
WRITE_CONFIRM_YES = "yes"
WRITE_CONFIRM_DENY = "deny"


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


def confirm_user_permission(
    action,
    details=None,
    yes_label="Yes",
    no_label="No",
    prompt="Allow this action?",
    info_actions=None,
):
    if details is None:
        details = {}
    if info_actions is None:
        info_actions = []

    while True:
        print(f"{BOLD}{YELLOW}{action}{RESET}")
        for label, value in details.items():
            print(f"{CYAN}{label}:{RESET} {value}")

        choice = _select_menu(
            [yes_label, *[label for label, _handler in info_actions], no_label],
            prompt=prompt,
        )

        if choice == 0:
            return WRITE_CONFIRM_YES

        info_index = choice - 1
        if 0 <= info_index < len(info_actions):
            _label, handler = info_actions[info_index]
            handler()
            continue

        return WRITE_CONFIRM_DENY


def confirm_write_to_file(file_path, content):
    full_path = os.path.abspath(file_path)
    return confirm_user_permission(
        action="Write file requested",
        details={
            "File": full_path,
            "Content": _content_summary(content),
        },
        yes_label="Yes, write file",
        no_label="No, deny write",
        prompt="Allow this write?",
        info_actions=[
            ("Show content", lambda: _show_write_content(content)),
            ("Explain content", lambda: print(_explain_write_content(full_path, content))),
        ],
    )


def select_menu(options, prompt):
    selected_index = _select_menu(options, prompt)
    return options[selected_index]


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
        wrapped = _wrap_styled_text(content, width - len(prefix), " " * len(prefix))
        return [
            f"{indent}{CYAN}{number}.{RESET} {wrapped[0]}",
            *wrapped[1:],
        ]

    unordered_match = UNORDERED_LIST_RE.match(line)
    if unordered_match:
        indent, content = unordered_match.groups()
        prefix = f"{indent}* "
        wrapped = _wrap_styled_text(content, width - len(prefix), " " * len(prefix))
        return [
            f"{indent}{CYAN}*{RESET} {wrapped[0]}",
            *wrapped[1:],
        ]

    if line.startswith(">"):
        wrapped = _wrap_text(line, width, "> ")
        return [f"{DIM}{line}{RESET}" for line in wrapped]

    return _wrap_styled_text(line, width, "")


def _select_menu(options, prompt):
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return _select_menu_fallback(options, prompt)

    selected_index = 0
    sys.stdout.write("\033[?25l")
    try:
        while True:
            _draw_menu(options, prompt, selected_index)
            key = _read_key()
            if key in ("\r", "\n"):
                _finish_menu(options, prompt)
                return selected_index
            if key == "\x1b[A":
                selected_index = (selected_index - 1) % len(options)
            elif key == "\x1b[B":
                selected_index = (selected_index + 1) % len(options)
            elif key in ("1", "y", "Y"):
                _finish_menu(options, prompt)
                return 0
            elif key in ("4", "n", "N"):
                _finish_menu(options, prompt)
                return len(options) - 1
    finally:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


def _draw_menu(options, prompt, selected_index):
    prompt_lines = 0
    if prompt:
        prompt_lines = 1
        sys.stdout.write(f"{CLEAR_LINE}{prompt}\n")
    for index, option in enumerate(options):
        marker = ">" if index == selected_index else " "
        color = GREEN if index == selected_index else DIM
        sys.stdout.write(f"{CLEAR_LINE}{color}{marker} {option}{RESET}\n")
    sys.stdout.write(f"\033[{len(options) + prompt_lines}A")
    sys.stdout.flush()


def _finish_menu(options, prompt):
    prompt_lines = 1 if prompt else 0
    sys.stdout.write(f"\033[{len(options) + prompt_lines}B\r")
    sys.stdout.flush()


def _read_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        first = sys.stdin.read(1)
        if first == "\x1b":
            rest = sys.stdin.read(2)
            return first + rest
        return first
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _select_menu_fallback(options, prompt):
    if prompt:
        print(prompt)
    for index, option in enumerate(options, start=1):
        default = " default" if index == 1 else ""
        print(f"{index}. {option}{default}")

    while True:
        answer = input("Choose option: ").strip()
        if answer == "":
            return 0

        try:
            selected = int(answer)
        except ValueError:
            print("Enter a number from the list.")
            continue

        if 1 <= selected <= len(options):
            return selected - 1

        print("Invalid option.")


def _render_code_block(lines, language, terminal_width, remember=True):
    if not lines:
        lines = [""]

    if remember:
        LAST_CODE_BLOCKS.append("\n".join(lines))
        block_number = len(LAST_CODE_BLOCKS)
    else:
        block_number = None

    content_width = max(len(_strip_ansi(line)) for line in lines)
    label_name = language or "code"
    label = f" {label_name} "
    if block_number is not None:
        label = f" {label_name}  [copy: /copy {block_number}] "
    max_box_width = max(24, terminal_width - 4)
    if len(label) > max_box_width:
        label = f" code #{block_number} " if block_number is not None else " code "
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


def _content_summary(content):
    text = str(content)
    byte_count = len(text.encode())
    line_count = len(text.splitlines()) or 1
    return f"{line_count} line(s), {byte_count} byte(s)"


def _show_write_content(content):
    print(
        "\n".join(
            _render_code_block(
                str(content).splitlines(),
                "content",
                _terminal_width(),
                remember=False,
            )
        )
    )


def _explain_write_content(file_path, content):
    text = str(content)
    lines = text.splitlines()
    preview = "\n".join(lines[:8])
    if len(lines) > 8:
        preview += f"\n... {len(lines) - 8} more line(s)"

    return "\n".join(
        [
            f"{BOLD}{CYAN}WRITE EXPLANATION{RESET}",
            f"{CYAN}Target:{RESET} {file_path}",
            f"{CYAN}Size:{RESET} {_content_summary(text)}",
            f"{CYAN}Action:{RESET} create or overwrite this file with the requested content.",
            f"{CYAN}Preview:{RESET}",
            "\n".join(
                _render_code_block(
                    preview.splitlines(),
                    "text",
                    _terminal_width(),
                    remember=False,
                )
            ),
        ]
    )


def _wrap_code_line(line, width):
    if len(line) <= width:
        return [line]

    return [line[index : index + width] for index in range(0, len(line), width)]


def _style_inline(line):
    line = INLINE_CODE_RE.sub(lambda match: f"{GREEN}{match.group(1)}{RESET}", line)
    line = BOLD_RE.sub(lambda match: f"{BOLD}{match.group(1)}{RESET}", line)
    line = ITALIC_RE.sub(lambda match: f"{DIM}{match.group(1)}{RESET}", line)
    return WARNING_BLOCK_RE.sub(lambda match: f"{BOLD}{BRIGHT_RED}[[{match.group(1)}]]{RESET}", line)


def _wrap_styled_text(text, width, subsequent_indent):
    width = max(24, width)
    lines = [""]
    line_lengths = [0]
    subsequent_width = max(24, width)

    def current_width():
        return width if len(lines) == 1 else subsequent_width

    def new_line():
        lines[-1] = lines[-1].rstrip()
        lines.append(subsequent_indent)
        line_lengths.append(len(subsequent_indent))

    def append_word(word, style):
        if not word:
            return

        styled_word = _apply_inline_style(word, style)
        word_length = len(word)
        if line_lengths[-1] > len(subsequent_indent) and (
            line_lengths[-1] + word_length > current_width()
        ):
            new_line()

        lines[-1] += styled_word
        line_lengths[-1] += word_length

    def append_space():
        if not lines[-1] or lines[-1].endswith(" "):
            return
        if line_lengths[-1] + 1 > current_width():
            new_line()
            return
        lines[-1] += " "
        line_lengths[-1] += 1

    for segment, style in _inline_segments(text):
        for token in re.findall(r"\S+|\s+", segment):
            if token.isspace():
                append_space()
            else:
                append_word(token, style)

    return [line.rstrip() for line in lines] or [""]


def _inline_segments(text):
    segments = []
    position = 0
    for match in INLINE_STYLE_RE.finditer(text):
        if match.start() > position:
            segments.append((text[position : match.start()], None))

        if match.group(1) is not None:
            segments.append((match.group(1), "code"))
        elif match.group(2) is not None:
            segments.append((f"[[{match.group(2)}]]", "warning"))
        elif match.group(3) is not None:
            segments.append((match.group(3), "bold"))
        elif match.group(4) is not None:
            segments.append((match.group(4), "italic"))

        position = match.end()

    if position < len(text):
        segments.append((text[position:], None))

    return segments


def _apply_inline_style(text, style):
    if style == "code":
        return f"{GREEN}{text}{RESET}"
    if style == "warning":
        return f"{BOLD}{BRIGHT_RED}{text}{RESET}"
    if style == "bold":
        return f"{BOLD}{text}{RESET}"
    if style == "italic":
        return f"{DIM}{text}{RESET}"
    return text


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
