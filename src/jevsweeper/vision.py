from __future__ import annotations

import time
from dataclasses import dataclass

from PIL import Image

from jevsweeper.board import FLAG, HIDDEN, MINE, Board, default_mine_count

WINDOW_TITLE = "Minesweeper"
TILE = 16
BOARD_LEFT = 12
BOARD_TOP = 55
BOARD_RIGHT_PAD = 8
BOARD_BOTTOM_PAD = 8

# Classic Windows XP Minesweeper number ink colors.
NUMBER_COLORS: dict[tuple[int, int, int], str] = {
    (0, 0, 255): "1",
    (0, 128, 0): "2",
    (255, 0, 0): "3",
    (0, 0, 128): "4",
    (128, 0, 0): "5",
    (0, 128, 128): "6",
    (0, 0, 0): "7",
    (128, 128, 128): "8",
}


class WindowNotFoundError(RuntimeError):
    pass


@dataclass(frozen=True)
class Layout:
    hwnd: int
    rows: int
    cols: int
    left: int
    top: int
    tile: int


def _win32():
    import win32con
    import win32gui
    import win32ui

    return win32con, win32gui, win32ui


def find_minesweeper() -> int:
    _, win32gui, _ = _win32()

    hwnd = win32gui.FindWindow(None, WINDOW_TITLE)
    if not hwnd:
        hwnd = win32gui.FindWindow("Minesweeper", None)
    if not hwnd:
        raise WindowNotFoundError("Minesweeper window not found")
    return hwnd


def wait_for_window(timeout: float = 10.0) -> int:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            return find_minesweeper()
        except WindowNotFoundError:
            time.sleep(0.2)
    raise WindowNotFoundError("Minesweeper window did not appear")


def restore_window(hwnd: int) -> None:
    win32con, win32gui, _ = _win32()
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass


def client_size(hwnd: int) -> tuple[int, int]:
    _, win32gui, _ = _win32()
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    return right - left, bottom - top


def capture_client(hwnd: int) -> Image.Image:
    win32con, win32gui, win32ui = _win32()
    restore_window(hwnd)
    width, height = client_size(hwnd)
    if width <= 0 or height <= 0:
        raise RuntimeError("Minesweeper client area is empty")

    hwnd_dc = win32gui.GetDC(hwnd)
    src_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    mem_dc = src_dc.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(src_dc, width, height)
    mem_dc.SelectObject(bitmap)
    mem_dc.BitBlt((0, 0), (width, height), src_dc, (0, 0), win32con.SRCCOPY)
    bits = bitmap.GetBitmapBits(True)

    win32gui.DeleteObject(bitmap.GetHandle())
    mem_dc.DeleteDC()
    src_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwnd_dc)

    return Image.frombuffer("RGB", (width, height), bits, "raw", "BGRX", 0, 1)


def infer_layout(hwnd: int, image: Image.Image | None = None) -> Layout:
    if image is None:
        width, height = client_size(hwnd)
    else:
        width, height = image.size
    cols = max(1, (width - BOARD_LEFT - BOARD_RIGHT_PAD) // TILE)
    rows = max(1, (height - BOARD_TOP - BOARD_BOTTOM_PAD) // TILE)
    return Layout(
        hwnd=hwnd,
        rows=rows,
        cols=cols,
        left=BOARD_LEFT,
        top=BOARD_TOP,
        tile=TILE,
    )


def _channel_sum(pixel: tuple[int, ...] | int) -> tuple[int, int, int]:
    if isinstance(pixel, int):
        return (pixel, pixel, pixel)
    return (pixel[0], pixel[1], pixel[2])


def _close(pixel: tuple[int, int, int], target: tuple[int, int, int], tolerance: int = 40) -> bool:
    return sum(abs(a - b) for a, b in zip(pixel, target)) <= tolerance


def _nearest_number(pixel: tuple[int, int, int]) -> str | None:
    best_label: str | None = None
    best_dist = 50
    for color, label in NUMBER_COLORS.items():
        dist = sum(abs(a - b) for a, b in zip(pixel, color))
        if dist < best_dist:
            best_dist = dist
            best_label = label
    return best_label


def classify_tile(image: Image.Image, left: int, top: int, tile: int = TILE) -> str:
    highlight = _channel_sum(image.getpixel((left + 1, top + 1)))
    center = _channel_sum(image.getpixel((left + tile // 2, top + tile // 2)))
    flag_pixel = _channel_sum(image.getpixel((left + 6, top + 6)))
    body = _channel_sum(image.getpixel((left + 4, top + 8)))

    raised = _close(highlight, (255, 255, 255), 30)
    exploded = _close(body, (255, 0, 0), 60) and not raised
    if exploded:
        return MINE
    if raised:
        if _close(flag_pixel, (255, 0, 0), 80) or _close(center, (255, 0, 0), 80):
            return FLAG
        if _close(center, (0, 0, 0), 40) and not _close(center, (192, 192, 192), 40):
            return MINE
        return HIDDEN

    number = _nearest_number(center)
    if number == "3" and _close(body, (255, 0, 0), 40) and _close(center, (0, 0, 0), 40):
        return MINE
    if number:
        return number
    return " "


def read_board(hwnd: int | None = None, mines: int | None = None) -> tuple[Board, Layout]:
    if hwnd is None:
        hwnd = find_minesweeper()
    restore_window(hwnd)
    image = capture_client(hwnd)
    layout = infer_layout(hwnd, image)
    grid: list[list[str]] = []
    for row in range(layout.rows):
        line: list[str] = []
        for col in range(layout.cols):
            left = layout.left + col * layout.tile
            top = layout.top + row * layout.tile
            line.append(classify_tile(image, left, top, layout.tile))
        grid.append(line)
    mine_count = mines if mines is not None else default_mine_count(layout.rows, layout.cols)
    return Board(grid, mine_count), layout
