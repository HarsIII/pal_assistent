"""Ad-hoc inspection helper (not part of the Phase 0 deliverable itself):
extracts a human-readable table of Pal instances from the current save,
for cross-checking hypotheses against what's shown in-game.

Not committed to git in its output form -- this prints personal save data
(nicknames) to the console only.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import DEFAULT_WORKDIR, DEFAULT_STEAM_SAVE_ROOT
from save.parser.save_bundle import find_world_dirs, discover_save_bundle, copy_bundle_to_workdir
from save.adapters.gvas_adapter import load_raw_gvas_dict


def get(props: dict, name: str, default=None):
    node = props.get(name)
    if node is None:
        return default
    return node.get("value", default)


def main() -> None:
    world_dir = find_world_dirs(DEFAULT_STEAM_SAVE_ROOT)[0]
    bundle = discover_save_bundle(world_dir)
    safe_bundle = copy_bundle_to_workdir(bundle, DEFAULT_WORKDIR / "inspect_run")

    parsed = load_raw_gvas_dict(safe_bundle.level_sav)
    char_map = parsed["properties"]["worldSaveData"]["value"]["CharacterSaveParameterMap"]["value"]

    rows = []
    for entry in char_map:
        obj = entry["value"]["RawData"]["value"]["object"]
        sp = obj["SaveParameter"]["value"]
        if get(sp, "IsPlayer", False):
            continue

        character_id = get(sp, "CharacterID")
        if character_id is None:
            continue

        nickname = get(sp, "NickName") or ""
        level_node = sp.get("Level")
        level = level_node["value"]["value"] if level_node else None
        is_rare = get(sp, "IsRarePal", False)
        rank = sp.get("Rank")
        rank_val = rank["value"]["value"] if rank else None
        talent_hp = sp.get("Talent_HP")
        talent_hp_val = talent_hp["value"]["value"] if talent_hp else None
        talent_shot = sp.get("Talent_Shot")
        talent_shot_val = talent_shot["value"]["value"] if talent_shot else None
        talent_def = sp.get("Talent_Defense")
        talent_def_val = talent_def["value"]["value"] if talent_def else None
        gender_node = sp.get("Gender")
        gender = gender_node["value"]["value"] if gender_node else None
        unique_npc = get(sp, "UniqueNPCID")

        rows.append(
            {
                "CharacterID": character_id,
                "NickName": nickname,
                "Level": level,
                "IsRarePal": is_rare,
                "UniqueNPCID": unique_npc,
                "Rank": rank_val,
                "Talent_HP": talent_hp_val,
                "Talent_Shot": talent_shot_val,
                "Talent_Defense": talent_def_val,
                "Gender": gender,
            }
        )

    rare = [r for r in rows if r["IsRarePal"]]
    print(f"Total non-player CharacterSaveParameterMap entries: {len(rows)}")
    print(f"IsRarePal=True entries: {len(rare)}\n")
    for r in rare:
        print(r)

    print("\n--- Highest-level Pals (top 10, for cross-checking Alpha hypothesis) ---")
    for r in sorted([r for r in rows if r["Level"] is not None], key=lambda r: -r["Level"])[:10]:
        print(r)


if __name__ == "__main__":
    main()
