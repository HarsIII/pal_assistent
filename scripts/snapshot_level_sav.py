"""Takes a timestamped, read-only snapshot of the current Level.sav for later
differential analysis. Snapshots live outside the repo (OS temp dir) --
never committed, since they're personal save data.

Usage: python scripts/snapshot_level_sav.py <label>
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import DEFAULT_WORKDIR, DEFAULT_STEAM_SAVE_ROOT
from save.parser.save_bundle import find_world_dirs, discover_save_bundle


def main() -> None:
    label = sys.argv[1] if len(sys.argv) > 1 else "snapshot"
    world_dir = find_world_dirs(DEFAULT_STEAM_SAVE_ROOT)[0]
    bundle = discover_save_bundle(world_dir)

    snapshots_dir = DEFAULT_WORKDIR / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    dest = snapshots_dir / f"{label}_Level.sav"

    import shutil

    shutil.copy2(bundle.level_sav, dest)
    print(f"Snapshot saved: {dest}")
    print(f"Source: {bundle.level_sav}")
    print(f"Source last modified: {bundle.level_sav.stat().st_mtime}")


if __name__ == "__main__":
    main()
