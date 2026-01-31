import argparse
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import tkinter as tk

def default_color_file() -> Path:
    return Path(__file__).resolve().parent / "color_window_indicator.txt"

def default_heartbeat_file() -> Path:
    return Path(__file__).resolve().parent / "color_window_indicator.heartbeat"

def default_quit_file() -> Path:
    return Path(__file__).resolve().parent / "color_window_indicator.quit"

def normalize_color(s: str) -> str:
    s = s.strip()
    if s.startswith("0x") and len(s) == 8:
        return "#" + s[2:].lower()
    if s.startswith("#") and len(s) == 7:
        return s.lower()
    return s  # allow "red", "green", etc.


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def write_color(color_file: Path, color: str) -> None:
    write_text_atomic(color_file, normalize_color(color))


def touch_heartbeat(heartbeat_file: Path) -> None:
    # Atomic "touch" by writing current time.
    write_text_atomic(heartbeat_file, str(time.time()))


def is_heartbeat_fresh(heartbeat_file: Path, max_age_s: float = 2.0) -> bool:
    try:
        age = time.time() - heartbeat_file.stat().st_mtime
        return age <= max_age_s
    except FileNotFoundError:
        return False
    except Exception:
        return False


def launch_background(
    color_file: Path,
    heartbeat_file: Path,
    quit_file: Path,
    poll_ms: int,
    initial_color: str
) -> None:
    """
    Launch the GUI in the background and return immediately.
    Works on Windows + Linux without extra dependencies.
    """
    args = [
        sys.executable,
        str(Path(__file__).resolve()),
        "run",
        "--file",
        str(color_file),
        "--heartbeat-file",
        str(heartbeat_file),
        "--quit-file",
        str(quit_file),
        "--poll-ms",
        str(poll_ms),
        "--color",
        initial_color,
    ]

    common = dict(
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )

    if sys.platform.startswith("win"):
        # Detached process on Windows
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        subprocess.Popen(
            args,
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            **common,
        )
    else:
        # Detach on Linux/macOS by starting a new session
        subprocess.Popen(args, start_new_session=True, **common)


class ColorWindow:
    def __init__(self, color_file: Path, heartbeat_file: Path, quit_file: Path, poll_ms: int, initial_color: str):
        self.color_file = color_file
        self.heartbeat_file = heartbeat_file
        self.quit_file = quit_file
        self.poll_ms = poll_ms

        self.root = tk.Tk()
        self.root.title("Color Indicator")

        self.canvas = tk.Canvas(self.root, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        self.current_color = normalize_color(initial_color)
        self._apply_color(self.current_color)

        self._last_mtime = None

        # Optional convenience: Esc sets black (does not close)
        self.root.bind("<Escape>", lambda e: self.set_color("#000000"))

        # Start polling + heartbeat
        self.root.after(self.poll_ms, self._tick)

    def _apply_color(self, color: str) -> None:
        self.canvas.configure(bg=color)
        self.root.configure(bg=color)

    def set_color(self, color: str) -> None:
        self.current_color = normalize_color(color)
        self._apply_color(self.current_color)

    def _tick(self) -> None:
        # Quit check first (so "quit" feels responsive even with slow polling)
        try:
            if self.quit_file.exists():
                try:
                    self.quit_file.unlink()
                except Exception:
                    pass
                self.root.destroy()
                return
        except Exception:
            pass

        # Heartbeat next (lets "set" know we're alive even if file reads fail briefly)
        try:
            touch_heartbeat(self.heartbeat_file)
        except Exception:
            pass

        try:
            if self.color_file.exists():
                mtime = self.color_file.stat().st_mtime
                if self._last_mtime is None or mtime != self._last_mtime:
                    self._last_mtime = mtime
                    content = self.color_file.read_text(encoding="utf-8").strip()
                    if content:
                        self.set_color(content)
        except Exception:
            # Ignore transient read/write timing issues
            pass
        finally:
            self.root.after(self.poll_ms, self._tick)

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normal window filled with a color, controlled via Python. `set` auto-starts the window."
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    p_run = sub.add_parser("run", help="Run the color indicator window (normally you won't need this).")
    p_run.add_argument("--file", type=Path, default=default_color_file())
    p_run.add_argument("--heartbeat-file", type=Path, default=default_heartbeat_file())
    p_run.add_argument("--quit-file", type=Path, default=default_quit_file())
    p_run.add_argument("--poll-ms", type=int, default=750)
    p_run.add_argument("--color", default="#00ff00")

    p_set = sub.add_parser("set", help="Set color. Auto-launches the window if it's not running.")
    p_set.add_argument("color")
    p_set.add_argument("--file", type=Path, default=default_color_file())
    p_set.add_argument("--heartbeat-file", type=Path, default=default_heartbeat_file())
    p_set.add_argument("--quit-file", type=Path, default=default_quit_file())
    p_set.add_argument("--poll-ms", type=int, default=1000)
    p_set.add_argument("--start-color", default="#000000", help="Initial color used only when auto-starting the window.")

    args = parser.parse_args()

    if args.mode == "run":
        if not args.file.exists():
            write_color(args.file, args.color)
            print("\nColor window is running.")
            print(f"Color file:      {args.file}")
            print(f"Heartbeat file:  {args.heartbeat_file}")
            print(f"Quit file:       {args.quit_file}")
            print("\nSet a color from any terminal like:")
            print(f'  {sys.executable} "{Path(__file__).resolve()}" set red')
            print(f'  {sys.executable} "{Path(__file__).resolve()}" set "#00ff00"')
            print(f'  {sys.executable} "{Path(__file__).resolve()}" set quit\n')
            print("Close the window to exit, or send `set quit`.\n")

        app = ColorWindow(
            color_file=args.file,
            heartbeat_file=args.heartbeat_file,
            quit_file=args.quit_file,
            poll_ms=args.poll_ms,
            initial_color=args.color,
        )
        app.run()
        return 0

    if args.mode == "set":
        # Optional "kill" command
        if args.color.strip().lower() in ("quit", "exit", "kill"):
            write_text_atomic(args.quit_file, "1")
            return 0

        # Ensure window is running (or start it)
        if not is_heartbeat_fresh(args.heartbeat_file, max_age_s=9.0):  # Determines if we need to open a new window or not.
            # Start in background and return immediately (no terminal lock-up)
            launch_background(args.file, args.heartbeat_file, args.quit_file, args.poll_ms, args.start_color)

        # Set the requested color (window will pick it up on next poll)
        write_color(args.file, args.color)
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
