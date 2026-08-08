"""Lists every non-player Pal at a given Rank (default 5, the observed max)
with its full identifying profile, so Rank_* field presence can be compared
against the FULL population at that Rank -- not just the subset that already
has a Rank_* field (selection bias otherwise).

Usage: python scripts/list_max_rank_pals.py <snapshot_label> [rank]
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import DEFAULT_WORKDIR
from save.adapters.gvas_adapter import load_raw_gvas_dict
from save.inspector.pal_identity import all_refs

RANK_STAT_FIELDS = ["Rank_HP", "Rank_Attack", "Rank_Defence", "Rank_CraftSpeed"]


def main() -> None:
    label = sys.argv[1]
    target_rank = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    parsed = load_raw_gvas_dict(DEFAULT_WORKDIR / "snapshots" / f"{label}_Level.sav")
    refs = all_refs(parsed)

    def rank_of(r):
        node = r.save_parameter.get("Rank")
        if node is None:
            return None
        v = node.get("value")
        return v.get("value") if isinstance(v, dict) else v

    at_rank = [r for r in refs if not r.is_player and rank_of(r) == target_rank]
    print(f"Non-player Pals at Rank={target_rank}: {len(at_rank)}")

    for r in at_rank:
        sp = r.save_parameter
        passives_node = sp.get("PassiveSkillList")
        passives = passives_node["value"]["values"] if passives_node else []
        present = [f for f in RANK_STAT_FIELDS if f in sp]

        def val(name):
            node = sp.get(name)
            if node is None:
                return None
            v = node.get("value")
            return v.get("value") if isinstance(v, dict) else v

        print(
            f"\n{r.character_id!r} (nick={r.nickname!r}) InstanceId={r.instance_id} Level={r.level}"
        )
        print(
            f"  Talent HP/Shot/Def: {val('Talent_HP')}/{val('Talent_Shot')}/{val('Talent_Defense')}"
        )
        print(f"  Passives: {passives}")
        print(f"  Rank_* fields present: {present or '(none)'}")
        if present:
            print(f"  Values: {{{', '.join(f'{f}={val(f)}' for f in present)}}}")


if __name__ == "__main__":
    main()
