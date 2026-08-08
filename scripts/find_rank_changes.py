"""Scans two Level.sav snapshots for any non-player Pal whose Rank-related
fields changed, matched by InstanceId (see save/inspector/pal_identity.py
for why that's the verified-stable identity field, not CharacterID or
NickName).

Usage: python scripts/find_rank_changes.py <before_label> <after_label>
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import DEFAULT_WORKDIR
from save.adapters.gvas_adapter import load_raw_gvas_dict
from save.differential.differ import diff_properties
from save.inspector.pal_identity import all_refs

RANK_FIELDS = {"Rank", "Rank_HP", "Rank_Attack", "Rank_Defence", "Rank_CraftSpeed"}


def main() -> None:
    before_label, after_label = sys.argv[1], sys.argv[2]
    snapshots_dir = DEFAULT_WORKDIR / "snapshots"
    before_refs = all_refs(load_raw_gvas_dict(snapshots_dir / f"{before_label}_Level.sav"))
    after_refs = all_refs(load_raw_gvas_dict(snapshots_dir / f"{after_label}_Level.sav"))

    before_by_id = {r.instance_id: r for r in before_refs if not r.is_player}
    after_by_id = {r.instance_id: r for r in after_refs if not r.is_player}
    common_ids = set(before_by_id) & set(after_by_id)
    print(f"Common non-player entries across both snapshots (by InstanceId): {len(common_ids)}")

    found_any = False
    for instance_id in common_ids:
        before_ref, after_ref = before_by_id[instance_id], after_by_id[instance_id]
        changes = diff_properties(before_ref.save_parameter, after_ref.save_parameter)
        rank_changes = [c for c in changes if c.path.split(".")[0] in RANK_FIELDS]
        if rank_changes:
            found_any = True
            print(
                f"\n=== {after_ref.character_id} ({after_ref.nickname or 'no nickname'}) "
                f"InstanceId={instance_id} ==="
            )
            print(f"  All changes for this Pal ({len(changes)} total):")
            for c in changes:
                print(f"  {c}")

    if not found_any:
        print("\nNo Pal with a Rank-related change found between these two snapshots.")


if __name__ == "__main__":
    main()
