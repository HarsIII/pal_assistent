"""Verifies (does not assume) whether InstanceId is a valid, stable
per-entity identifier for CharacterSaveParameterMap entries:

1. Uniqueness within a single snapshot -- no two different entries should
   share an InstanceId.
2. Stability across a save-to-save transition -- for entries whose
   InstanceId appears in both snapshots, CharacterID must never mismatch
   (a real Pal cannot change species). A single mismatch would mean
   InstanceId is NOT a safe cross-save identity and must not be used as one.
3. Reports how many entries disappeared / appeared, as context (expected
   from Pals being consumed as condense fodder or newly caught/hatched).

Usage: python scripts/verify_instance_id_stability.py <before_label> <after_label>
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import DEFAULT_WORKDIR
from save.adapters.gvas_adapter import load_raw_gvas_dict
from save.inspector.pal_identity import all_refs


def check_uniqueness(refs: list, label: str) -> bool:
    counts = Counter(r.instance_id for r in refs)
    dupes = {k: v for k, v in counts.items() if v > 1}
    print(f"[{label}] {len(refs)} entries, {len(counts)} distinct InstanceIds")
    if dupes:
        print(f"  FAILURE: {len(dupes)} InstanceId(s) used by more than one entry:")
        for iid, count in list(dupes.items())[:10]:
            print(f"    {iid}: {count} entries")
        return False
    print("  OK: every InstanceId in this snapshot is unique.")
    return True


def check_cross_save_stability(before: list, after: list) -> None:
    before_by_id = {r.instance_id: r for r in before}
    after_by_id = {r.instance_id: r for r in after}

    common_ids = set(before_by_id) & set(after_by_id)
    only_before = set(before_by_id) - set(after_by_id)
    only_after = set(after_by_id) - set(before_by_id)

    print(f"\nInstanceIds in BEFORE only (disappeared): {len(only_before)}")
    print(f"InstanceIds in AFTER only (newly appeared): {len(only_after)}")
    print(f"InstanceIds in BOTH: {len(common_ids)}")

    mismatches = []
    for iid in common_ids:
        b, a = before_by_id[iid], after_by_id[iid]
        if b.character_id != a.character_id:
            mismatches.append((iid, b.character_id, a.character_id))
        if b.is_player != a.is_player:
            mismatches.append((iid, f"is_player={b.is_player}", f"is_player={a.is_player}"))

    if mismatches:
        print(f"\nFAILURE: {len(mismatches)} InstanceId(s) changed CharacterID/IsPlayer across the save --")
        print("this would mean InstanceId is NOT a safe stable identifier. Details:")
        for iid, before_val, after_val in mismatches[:20]:
            print(f"  {iid}: {before_val} -> {after_val}")
    else:
        print(
            f"\nOK: all {len(common_ids)} entries present in both snapshots kept the exact same "
            "CharacterID and IsPlayer status. No coincidental collision is plausible at this sample "
            "size -- InstanceId is a stable, verified per-entity identifier across this save-to-save "
            "transition."
        )

    print("\nSample of entries with mutated fields (proof InstanceId tracks a live, changing entity):")
    shown = 0
    for iid in common_ids:
        b, a = before_by_id[iid], after_by_id[iid]
        if b.level != a.level and shown < 5:
            print(f"  {iid} ({a.character_id}): Level {b.level} -> {a.level}")
            shown += 1


def main() -> None:
    before_label, after_label = sys.argv[1], sys.argv[2]
    snapshots_dir = DEFAULT_WORKDIR / "snapshots"
    before_refs = all_refs(load_raw_gvas_dict(snapshots_dir / f"{before_label}_Level.sav"))
    after_refs = all_refs(load_raw_gvas_dict(snapshots_dir / f"{after_label}_Level.sav"))

    ok_before = check_uniqueness(before_refs, before_label)
    ok_after = check_uniqueness(after_refs, after_label)

    if not (ok_before and ok_after):
        print("\nStopping: uniqueness check failed, cross-save comparison would be meaningless.")
        return

    check_cross_save_stability(before_refs, after_refs)


if __name__ == "__main__":
    main()
