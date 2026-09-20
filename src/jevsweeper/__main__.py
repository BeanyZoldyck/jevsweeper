from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from jevsweeper.loop import DEFAULT_EXE, once, play


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(
        prog="python -m jevsweeper",
        description="Play XP Minesweeper with TypeSafe Jev.",
    )
    parser.add_argument(
        "--exe",
        type=Path,
        default=DEFAULT_EXE,
        help="Path to WINMINE.EXE",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Read the current board, print the next square, and exit without clicking",
    )
    parser.add_argument("--mines", type=int, default=None, help="Mine count (inferred from size if omitted)")
    parser.add_argument("--delay", type=float, default=0.2, help="Seconds to wait after each click")
    args = parser.parse_args()

    if args.once:
        once(args.exe, mines=args.mines, click=False)
    else:
        result = play(args.exe, mines=args.mines, delay=args.delay)
        print(f"finished: {result}")


if __name__ == "__main__":
    main()
