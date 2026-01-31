# Color Window Indicator (Python)

A tiny cross-platform **color indicator window** (normal resizable window with title bar) whose background color is controlled from the command line using Python.

You only need to remember one command:

```bash
python color_window.py set <color>
```

If the window is not running, `set` will **auto-start it in the background**, then apply the color.

---

## What it does

- Opens a normal application window filled with a solid color
- Lets you change that color from any terminal by running `set`
- Runs on **Windows** and **Linux** without changing the code
- Stores state in two files next to `color_window.py`:
  - `color_window_indicator.txt` (the requested color)
  - `color_window_indicator.heartbeat` (used to detect if the window is already running)

---

## Requirements

- Python 3.8+ (tested by you on Python 3.13)
- Tkinter (usually included with standard Python installs)

---

## Files

- `color_window.py` — the program
- `README.md` — this file
- `color_window_indicator.txt` — created at runtime (next to the script)
- `color_window_indicator.heartbeat` — created at runtime (next to the script)

---

## Usage

### Set a color (auto-starts the window if needed)

```bash
python color_window.py set red
python color_window.py set "#00ff00"
python color_window.py set 0x3366ff
```

Supported color formats:
- CSS-ish color names like `red`, `green`, `navy`
- Hex `#RRGGBB`
- Hex `0xRRGGBB` (will be normalized to `#RRGGBB`)

## Quitting the window from the command line

You can close the window normally (click **X**) or send a quit command from any terminal:

```bash
python color_window.py set quit
python color_window.py set exit
python color_window.py set kill
```
Internally this creates a small color_window_indicator.quit file next to color_window.py; the running window checks for it periodically and exits cleanly when it appears.

### Run manually (optional)

You normally don't need this, because `set` auto-starts the window.

```bash
python color_window.py run
```

When run manually, the script prints the call spec (how to use `set`) and the file locations.

---

## Performance / polling rate

The window checks for color changes on a timer (`poll-ms`).

To reduce how often it checks:

- In the code, change the default values of `--poll-ms` in the argparse section (e.g. from `100` to `500` or `1000`).
- If you increase `--poll-ms`, also increase the heartbeat freshness threshold used by `set`:
  - Look for: `max_age_s=...`
  - Rule of thumb: set `max_age_s` to about **5×** the poll interval (in seconds).

Example:
- `poll-ms = 1000` (1 Hz)
- `max_age_s ≈ 10`

---

## Safety notes

- This is a normal window with edges/title bar — you can always move/minimize/close it like any app.
- Closing the window ends the GUI process immediately.
- The next `set <color>` call will re-launch it if it isn't running.

---

## Common troubleshooting

### Nothing happens when I run `set`
- Make sure you're using the same Python environment for both `set` and `run` (if you launched `run` manually).
- Check that `color_window_indicator.txt` is being created next to `color_window.py`.

### Multiple windows appear
- Your poll rate is likely high but the heartbeat threshold is too strict.
- Increase `max_age_s` (see **Performance / polling rate**).

---

## License

Do whatever you want with it.
