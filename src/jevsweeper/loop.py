from __future__ import annotations

import subprocess
import time
from pathlib import Path

from typesafe_sdk import TypeSafeClient

from jevsweeper.clicker import click_move
from jevsweeper.jev_move import Move, next_click
from jevsweeper.vision import WindowNotFoundError, find_minesweeper, read_board, wait_for_window

DEFAULT_EXE = Path(r"C:/Users/chuka/Documents/Minesweeper-Windows-XP/WINMINE.EXE")


def attach_or_launch(exe: Path, timeout: float = 10.0) -> int:
    try:
        return find_minesweeper()
    except WindowNotFoundError:
        if not exe.exists():
            raise FileNotFoundError(f"Minesweeper EXE not found: {exe}") from None
        subprocess.Popen([str(exe)], cwd=str(exe.parent))
        return wait_for_window(timeout=timeout)


def play(
    exe: Path = DEFAULT_EXE,
    *,
    mines: int | None = None,
    delay: float = 0.2,
    max_moves: int = 500,
    client: TypeSafeClient | None = None,
) -> str:
    hwnd = attach_or_launch(exe)
    owns_client = client is None
    if client is None:
        client = TypeSafeClient()
    last_text = ""
    stuck = 0
    status = "playing"
    try:
        for _ in range(max_moves):
            board, layout = read_board(hwnd, mines=mines)
            status = board.status()
            print(board.to_text())
            print(f"status={status}")
            if status != "playing":
                return status
            if board.to_text() == last_text:
                stuck += 1
                if stuck >= 3:
                    print("board did not change; stopping")
                    return "stuck"
            else:
                stuck = 0
            last_text = board.to_text()
            move = next_click(board, mines=board.mines, client=client)
            print(f"click r{move.row} c{move.col} noul={move.noul:.3f} ({move.reason})")
            click_move(layout, move)
            time.sleep(delay)
        return "max_moves"
    finally:
        if owns_client:
            client.close()


def once(exe: Path = DEFAULT_EXE, *, mines: int | None = None, click: bool = False) -> Move:
    hwnd = attach_or_launch(exe)
    board, layout = read_board(hwnd, mines=mines)
    print(board.to_text())
    move = next_click(board, mines=board.mines)
    print(f"next r{move.row} c{move.col} noul={move.noul:.3f} ({move.reason})")
    if click:
        click_move(layout, move)
    return move
