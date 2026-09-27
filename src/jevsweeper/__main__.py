from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv
from typesafe_sdk import TypeSafeAPIConnectionError, TypeSafeAPITimeoutError, TypeSafeError

from jevsweeper.client import BackendConfigError, LOCAL_BASE_URL
from jevsweeper.loop import DEFAULT_EXE, once, play


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(
        prog="python -m jevsweeper",
        description="Play XP Minesweeper with local-jev or hosted TypeSafe Jev.",
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
        "--backend",
        choices=("auto", "local", "hosted"),
        default=None,
        help="auto (default): local-jev if it is up, otherwise hosted TypeSafe",
    )
    parser.add_argument(
        "--url",
        default=None,
        help=f"API root (local-jev default {LOCAL_BASE_URL}; hosted is https://api.typesafe.ai)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name (local-jev card or hosted jev-latest)",
    )
    args = parser.parse_args()

    try:
        if args.once:
            once(
                args.exe,
                mines=args.mines,
                click=False,
                backend=args.backend,
                base_url=args.url,
                model=args.model,
            )
        else:
            result = play(
                args.exe,
                mines=args.mines,
                delay=args.delay,
                backend=args.backend,
                base_url=args.url,
                model=args.model,
            )
            print(f"finished: {result}")
    except BackendConfigError as error:
        raise SystemExit(str(error)) from error
    except (TypeSafeAPIConnectionError, TypeSafeAPITimeoutError, TypeSafeError) as error:
        raise SystemExit(
            f"{error}\n"
            "Hosted: set TYPESAFE_API_KEY and use --backend hosted.\n"
            "Local: run `local-jev serve` and use --backend local."
        ) from error


if __name__ == "__main__":
    main()
