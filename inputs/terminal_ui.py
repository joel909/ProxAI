import itertools
import sys
import threading
import time

RED = "\033[31m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
RESET = "\033[0m"


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
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()
