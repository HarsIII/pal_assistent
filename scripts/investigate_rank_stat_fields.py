"""Investigates Rank_HP / Rank_Attack / Rank_Defence / Rank_CraftSpeed across
the whole save, without assuming they are condensation modifiers.

Three passes:
  1. Level.sav CharacterSaveParameterMap (sparse encoding: fields are either
     present or entirely absent -- presence itself is the signal).
  2. GlobalPalStorage.sav SaveParameterArray (dense encoding: every field is
     always present, defaulting to 0 -- a non-zero VALUE is the signal, not
     presence).
  3. A full recursive search across Level.sav's ENTIRE parsed structure (not
     just CharacterSaveParameterMap) for any property path containing
     "Rank_", in case the same or a related field appears elsewhere under a
     different context (base camp work assignments, etc.).

Reports raw observations only -- no rule is derived here.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import DEFAULT_WORKDIR
from save.adapters.gvas_adapter import load_raw_gvas_dict
from save.inspector.pal_identity import all_refs
from save.inspector.schema_walker import SchemaWalker

RANK_STAT_FIELDS = ["Rank_HP", "Rank_Attack", "Rank_Defence", "Rank_CraftSpeed"]
SNAPSHOTS = DEFAULT_WORKDIR / "snapshots"


def profile(sp: dict) -> dict:
    def val(name):
        node = sp.get(name)
        if node is None:
            return None
        v = node.get("value")
        if isinstance(v, dict) and "value" in v:
            return v["value"]
        return v

    passives_node = sp.get("PassiveSkillList")
    passives = passives_node["value"]["values"] if passives_node else []

    rank_stats_present = {f: (f in sp) for f in RANK_STAT_FIELDS}
    rank_stats_values = {f: val(f) for f in RANK_STAT_FIELDS if f in sp}

    return {
        "CharacterID": val("CharacterID"),
        "NickName": val("NickName"),
        "Level": val("Level"),
        "Rank": val("Rank"),
        "IsRarePal": val("IsRarePal"),
        "IsPlayer": val("IsPlayer"),
        "Talent_HP": val("Talent_HP"),
        "Talent_Shot": val("Talent_Shot"),
        "Talent_Defense": val("Talent_Defense"),
        "Passives": passives,
        "rank_stats_present": rank_stats_present,
        "rank_stats_values": rank_stats_values,
    }


def pass1_level_sav():
    print("=" * 80)
    print("PASS 1: Level.sav CharacterSaveParameterMap (sparse encoding)")
    print("=" * 80)
    parsed = load_raw_gvas_dict(SNAPSHOTS / "rank_investigation_Level.sav")
    refs = all_refs(parsed)
    print(f"Total entries: {len(refs)}")

    hits = [r for r in refs if any(f in r.save_parameter for f in RANK_STAT_FIELDS)]
    print(f"Entries with at least one Rank_* field PRESENT: {len(hits)}")
    for r in hits:
        p = profile(r.save_parameter)
        print(f"\nInstanceId={r.instance_id}")
        for k, v in p.items():
            print(f"  {k}: {v}")
    if not hits:
        print("(none found)")
    return hits


def pass2_global_pal_storage():
    print("\n" + "=" * 80)
    print("PASS 2: GlobalPalStorage.sav SaveParameterArray (dense encoding, 0 = default)")
    print("=" * 80)
    parsed = load_raw_gvas_dict(SNAPSHOTS / "rank_investigation_GlobalPalStorage.sav")
    entries = parsed["properties"]["SaveParameterArray"]["value"]["values"]
    print(f"Total slots: {len(entries)}")

    occupied = [e for e in entries if e["SaveParameter"]["value"].get("CharacterID", {}).get("value") not in (None, "None")]
    print(f"Occupied slots (CharacterID != None): {len(occupied)}")

    def val(sp, name):
        node = sp.get(name)
        if node is None:
            return None
        v = node.get("value")
        if isinstance(v, dict) and "value" in v:
            return v["value"]
        return v

    hits = []
    for e in occupied:
        sp = e["SaveParameter"]["value"]
        nonzero = {f: val(sp, f) for f in RANK_STAT_FIELDS if val(sp, f) not in (None, 0)}
        if nonzero:
            hits.append((sp, nonzero))

    print(f"Occupied slots with a NON-ZERO Rank_* value: {len(hits)}")
    for sp, nonzero in hits:
        p = profile(sp)
        print("\n(GlobalPalStorage entry)")
        for k, v in p.items():
            print(f"  {k}: {v}")
        print(f"  non-zero Rank_* values: {nonzero}")
    if not hits:
        print("(none found -- every occupied Palbox slot has all four Rank_* fields at exactly 0)")

    # Also report the distribution of Rank field itself among occupied slots,
    # for context (are any boxed Pals condensed at all?).
    ranks = [val(e["SaveParameter"]["value"], "Rank") for e in occupied]
    from collections import Counter
    print(f"\nRank value distribution among occupied Palbox slots: {dict(Counter(ranks))}")
    return hits


def pass3_full_search():
    print("\n" + "=" * 80)
    print("PASS 3: Full recursive search of Level.sav for any 'Rank_' path")
    print("=" * 80)
    parsed = load_raw_gvas_dict(SNAPSHOTS / "rank_investigation_Level.sav")
    walker = SchemaWalker()
    walker.walk_properties(parsed["properties"])

    matches = [s for s in walker.summary_rows() if "rank_" in s.path.lower()]
    print(f"Distinct paths containing 'rank_' (case-insensitive): {len(matches)}")
    for m in matches:
        print(f"  {m.path}  (occurrences={m.occurrences}, shapes={m.shapes_seen})")


if __name__ == "__main__":
    pass1_level_sav()
    pass2_global_pal_storage()
    pass3_full_search()
