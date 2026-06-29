import queue
import shutil
import subprocess
import sys
import threading
import time


def run_shell_command(command):
    stdout_lines = []
    stderr_lines = []

    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        display = _LiveCommandDisplay(command)
        display.start()
        events = queue.Queue()
        threads = [
            threading.Thread(
                target=_read_stream,
                args=(process.stdout, stdout_lines, events, "stdout"),
                daemon=True,
            ),
            threading.Thread(
                target=_read_stream,
                args=(process.stderr, stderr_lines, events, "stderr"),
                daemon=True,
            ),
        ]

        for thread in threads:
            thread.start()

        while process.poll() is None or any(thread.is_alive() for thread in threads) or not events.empty():
            try:
                stream_name, line = events.get(timeout=0.05)
            except queue.Empty:
                time.sleep(0.01)
                continue

            display.append(stream_name, line)

        for thread in threads:
            thread.join()
        process.wait()
        display.clear()

        output = "".join(stdout_lines).strip()
        error = "".join(stderr_lines).strip()
        if process.returncode == 0:
            return {"output": output, "error": None}

        return {"output": output or None, "error": error or f"Command exited with status {process.returncode}."}
    except subprocess.CalledProcessError as e:
        return {"output": None, "error": e.stderr.strip()}
    except Exception as e:
        return {"output": None, "error": str(e)}


def _read_stream(stream, sink, events, stream_name):
    if stream is None:
        return

    try:
        for line in iter(stream.readline, ""):
            sink.append(line)
            events.put((stream_name, line))
    finally:
        stream.close()


class _LiveCommandDisplay:
    def __init__(self, command):
        self.command = command
        self.enabled = sys.stdout.isatty()
        self.lines = []
        self.drawn_lines = 0

    def start(self):
        if not self.enabled:
            return

        self._redraw()

    def append(self, stream_name, line):
        if not self.enabled:
            return

        self.lines.append((stream_name, line))
        self._redraw()

    def clear(self):
        if not self.enabled or self.drawn_lines == 0:
            return

        self._erase_drawn_lines()
        self.drawn_lines = 0

    def _redraw(self):
        self._erase_drawn_lines()
        rendered = self._render()
        sys.stdout.write("\n".join(rendered))
        sys.stdout.write("\n")
        sys.stdout.flush()
        self.drawn_lines = len(rendered)

    def _erase_drawn_lines(self):
        if self.drawn_lines == 0:
            return

        sys.stdout.write(f"\033[{self.drawn_lines}A")
        for _ in range(self.drawn_lines):
            sys.stdout.write("\r\033[K\033[1B")
        sys.stdout.write(f"\033[{self.drawn_lines}A")

    def _render(self):
        width, height = shutil.get_terminal_size(fallback=(80, 24))
        max_output_lines = max(4, min(height - 6, 16))
        visible_lines = self.lines[-max_output_lines:]
        rendered = [
            f"\033[2mRunning command: {self._fit(self.command, width)}\033[0m",
            "\033[2m" + "-" * min(width, 72) + "\033[0m",
        ]

        if not visible_lines:
            rendered.append("\033[2mWaiting for output...\033[0m")

        for stream_name, line in visible_lines:
            prefix = "err " if stream_name == "stderr" else "out "
            text = self._fit(prefix + line.rstrip("\n"), width)
            if stream_name == "stderr":
                rendered.append(f"\033[31m{text}\033[0m")
            else:
                rendered.append(text)

        return rendered

    def _fit(self, text, width):
        text = text.replace("\r", "").replace("\t", "    ")
        if len(text) <= width:
            return text

        return text[: max(0, width - 3)] + "..."
