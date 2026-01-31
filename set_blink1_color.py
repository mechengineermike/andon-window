import argparse
import time
from blink1.blink1 import Blink1

def main() -> None:
    parser = argparse.ArgumentParser(description="Set blink(1) color")
    parser.add_argument("color", help="Color name (e.g. 'red') or hex (e.g. '#00ff00')")
    parser.add_argument("--fade-ms", type=int, default=150, help="Fade time in milliseconds")
    parser.add_argument("--led", type=int, default=0, help="0=all, 1=LED A, 2=LED B (mk2/mk3)")
    parser.add_argument("--hold-s", type=float, default=0.0, help="Keep script alive this many seconds")
    parser.add_argument("--off-after", action="store_true", help="Turn off after hold")
    args = parser.parse_args()

    b1 = Blink1()  # first blink(1) found
    try:
        b1.fade_to_color(args.fade_ms, args.color, ledn=args.led)
        if args.hold_s > 0:
            time.sleep(args.hold_s)
        if args.off_after:
            b1.off()
    finally:
        b1.close()

if __name__ == "__main__":
    main()
