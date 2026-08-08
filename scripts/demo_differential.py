"""Demonstrates the Differential Save Analyzer on two real LevelMeta.sav
backups this machine already has (fast: LevelMeta.sav is a few KB, unlike
Level.sav which is several MB and would make this demo slow).

Deliberately reads only from the game's backup/ directory (never modifies it)
and writes nothing back.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from save.adapters.gvas_adapter import load_raw_gvas_dict
from save.differential.differ import diff_properties

WORLD_DIR = Path(
    r"C:\Users\elmas\AppData\Local\Pal\Saved\SaveGames\76561198809928356\07A8CBAE48FFC56464871C9F7A9FCA66"
)


def main() -> None:
    backups = sorted((WORLD_DIR / "backup" / "world").iterdir())
    if len(backups) < 2:
        print("Not enough backups found.")
        return

    earliest, latest = backups[0], backups[-1]
    print(f"Comparing:\n  before = {earliest.name}\n  after  = {latest.name}\n")

    before_dict = load_raw_gvas_dict(earliest / "LevelMeta.sav")
    after_dict = load_raw_gvas_dict(latest / "LevelMeta.sav")

    changes = diff_properties(before_dict["properties"], after_dict["properties"])
    print(f"{len(changes)} change(s):\n")
    for c in changes:
        print(c)


if __name__ == "__main__":
    main()
