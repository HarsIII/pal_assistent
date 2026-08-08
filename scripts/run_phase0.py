"""Entry point for Phase 0: locate the real save, copy it safely, run the
Save Researcher, and print/save a structured summary.

Usage: python scripts/run_phase0.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import DEFAULT_WORKDIR, DEFAULT_STEAM_SAVE_ROOT
from save.parser.save_bundle import (
    find_world_dirs,
    discover_save_bundle,
    copy_bundle_to_workdir,
)
from save.inspector.save_researcher import run_save_researcher
from save.inspector.report_writer import (
    render_file_status_table,
    render_structure_counts,
    render_top_level_properties,
    render_field_inventory,
)


def main() -> None:
    world_dirs = find_world_dirs(DEFAULT_STEAM_SAVE_ROOT)
    if not world_dirs:
        print(f"No world directories found under {DEFAULT_STEAM_SAVE_ROOT}")
        return

    print(f"Found {len(world_dirs)} world dir(s):")
    for w in world_dirs:
        print(f"  - {w}")

    world_dir = world_dirs[0]
    print(f"\nUsing: {world_dir}")

    bundle = discover_save_bundle(world_dir)
    print("Discovered files:")
    for p in bundle.all_existing_files():
        print(f"  - {p}")

    workdir = DEFAULT_WORKDIR / "phase0_run"
    print(f"\nCopying to safe workdir: {workdir}")
    safe_bundle = copy_bundle_to_workdir(bundle, workdir)

    print("\nRunning Save Researcher...")
    report = run_save_researcher(safe_bundle)

    print("\n" + "=" * 80)
    print(render_file_status_table(report))
    print("\n" + render_structure_counts(report))

    out_dir = PROJECT_ROOT / "reports" / "_generated"
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "file_status.md").write_text(render_file_status_table(report), encoding="utf-8")
    (out_dir / "structure_counts.md").write_text(render_structure_counts(report), encoding="utf-8")
    (out_dir / "top_level_properties.md").write_text(
        render_top_level_properties(report), encoding="utf-8"
    )

    # Full field inventories for the two files that matter most for breeding data.
    (out_dir / "level_character_field_inventory.md").write_text(
        render_field_inventory(
            report, "Level.sav.worldSaveData.CharacterSaveParameterMap", max_rows=2000
        ),
        encoding="utf-8",
    )
    (out_dir / "level_full_field_inventory.md").write_text(
        render_field_inventory(report, "Level.sav", max_rows=5000),
        encoding="utf-8",
    )
    (out_dir / "player_field_inventory.md").write_text(
        render_field_inventory(report, "Players/", max_rows=2000),
        encoding="utf-8",
    )

    print(f"\nWrote generated report fragments to {out_dir}")


if __name__ == "__main__":
    main()
