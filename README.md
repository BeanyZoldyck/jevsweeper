# jevsweeper

Play Windows XP Minesweeper by sending the live board to a System One API — either [hosted TypeSafe Jev](https://docs.typesafe.ai/introduction) or [local-jev](https://github.com/amithgc/local-jev) — then clicking or flagging the next square.

Both backends speak the same `/v1/systemone` wire format, so this bot uses `typesafe-sdk` for either. Code first flags or clicks cells that Minesweeper numbers already force (100% mine or 100% safe). Remaining frontier cells get two Nouls each — “safe to left-click?” and “is this a mine?” — then the bot left-clicks safes and right-clicks flags. Uncertain cells are flagged rather than clicked if the mine score is higher.

`--backend auto` (default) uses local-jev if `http://127.0.0.1:8765/healthz` is up, otherwise hosted TypeSafe when `TYPESAFE_API_KEY` is set.

## Setup

Python 3.10+ on Windows.

```powershell
cd C:\Users\chuka\Documents\GitHub\jevsweeper
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
copy .env.example .env
```

### Hosted TypeSafe

Get an API key from the [TypeSafe dashboard](https://docs.typesafe.ai/introduction/quickstart) and put it in `.env`:

```
JEV_BACKEND=hosted
TYPESAFE_API_KEY=...
```

### local-jev

Run the server in another terminal ([Windows via WSL2](https://github.com/amithgc/local-jev)):

```sh
git clone https://github.com/amithgc/local-jev && cd local-jev
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e .
.venv/bin/local-jev serve
```

Then in `.env`:

```
JEV_BACKEND=local
TYPESAFE_BASE_URL=http://127.0.0.1:8765
TYPESAFE_API_KEY=local
```

The SDK requires some `TYPESAFE_API_KEY`; local-jev ignores `local` unless you set `LOCAL_JEV_API_KEY` on the server.

Default Minesweeper path is `C:\Users\chuka\Documents\Minesweeper-Windows-XP\WINMINE.EXE` (override with `--exe`). Keep the window visible (not minimized).

## Run

```powershell
python -m jevsweeper
python -m jevsweeper --backend hosted
python -m jevsweeper --backend local --model llm-qwen3.5-4b
python -m jevsweeper --once
```

`--once` prints the next square and moves the mouse there without clicking.

## Library

```python
from jevsweeper.board import Board
from jevsweeper.client import make_client
from jevsweeper.jev_move import next_move

board = Board.from_text(
    ".....\n.111.\n.1 1.\n.111.\n.....",
    mines=10,
)
with make_client(backend="auto") as client:
    move = next_move(board, client=client)
print(move.action, move.row, move.col, move.noul)
```

Opening boards (nothing revealed yet) click the center tile in code and skip the model.

## Layout

| Module | Role |
| --- | --- |
| `board.py` | Grid, frontier cells, win/loss |
| `client.py` | Pick local-jev or hosted TypeSafe, then `typesafe-sdk` |
| `jev_move.py` | `next_move()` — one `/v1/systemone` call, then click or flag |
| `vision.py` | Capture the XP window and classify 16×16 tiles |
| `clicker.py` | Client-area left click or right-click flag |
| `loop.py` | Launch or attach `WINMINE.EXE` and play |
