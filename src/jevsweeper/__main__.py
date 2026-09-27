from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv
from typesafe_sdk import TypeSafeAPIConnectionError, TypeSafeAPITimeoutError, TypeSafeError

from jevsweeper.client import DEFAULT_BASE_URL
from jevsweeper.loop import DEFAULT_EXE, once, play


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(
        prog="python -m jevsweeper",
        description="Play XP Minesweeper with a local-jev server.",
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
        help="Read the current board, move the mouse to the next square, and exit without clicking",
    )
    parser.add_argument("--mines", type=int, default=None, help="Mine count (inferred from size if omitted)")
    parser.add_argument("--delay", type=float, default=0.2, help="Seconds to wait after each click")
    parser.add_argument(
        "--url",
        default=None,
        help=f"local-jev base URL (default {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="local-jev model name, e.g. llm-qwen3.5-4b (server default if omitted)",
    )
    args = parser.parse_args()

    try:
        if args.once:
            once(args.exe, mines=args.mines, click=False, base_url=args.url, model=args.model)
        else:
            result = play(
                args.exe,
                mines=args.mines,
                delay=args.delay,
                base_url=args.url,
                model=args.model,
            )
            print(f"finished: {result}")
    except (TypeSafeAPIConnectionError, TypeSafeAPITimeoutError, TypeSafeError) as error:
        raise SystemExit(
            f"{error}\n"
            "Start local-jev first, for example:\n"
            "  local-jev serve\n"
            f"Then this client talks to {args.url or DEFAULT_BASE_URL}"
        ) from error


if __name__ == "__main__":
    main()
