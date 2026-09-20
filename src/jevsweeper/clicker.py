from __future__ import annotations

import time

from jevsweeper.jev_move import Move
from jevsweeper.vision import Layout, restore_window


def _win32():
    import win32api
    import win32con
    import win32gui

    return win32api, win32con, win32gui


def tile_center(layout: Layout, row: int, col: int) -> tuple[int, int]:
    x = layout.left + col * layout.tile + layout.tile // 2
    y = layout.top + row * layout.tile + layout.tile // 2
    return x, y


def click_client(hwnd: int, x: int, y: int, *, right: bool = False) -> None:
    win32api, win32con, win32gui = _win32()
    restore_window(hwnd)
    lparam = win32api.MAKELONG(x, y)
    if right:
        down, up, wparam = win32con.WM_RBUTTONDOWN, win32con.WM_RBUTTONUP, win32con.MK_RBUTTON
    else:
        down, up, wparam = win32con.WM_LBUTTONDOWN, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON
    win32gui.SendMessage(hwnd, down, wparam, lparam)
    time.sleep(0.02)
    win32gui.SendMessage(hwnd, up, 0, lparam)


def hover_client(hwnd: int, x: int, y: int) -> None:
    win32api, _, win32gui = _win32()
    restore_window(hwnd)
    screen_x, screen_y = win32gui.ClientToScreen(hwnd, (x, y))
    win32api.SetCursorPos((screen_x, screen_y))


def hover_move(layout: Layout, move: Move) -> None:
    x, y = tile_center(layout, move.row, move.col)
    hover_client(layout.hwnd, x, y)


def click_move(layout: Layout, move: Move) -> None:
    x, y = tile_center(layout, move.row, move.col)
    click_client(layout.hwnd, x, y)
