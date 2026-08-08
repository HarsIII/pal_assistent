"""Finds a specific Pal in two Level.sav snapshots and diffs just that Pal's
SaveParameter data -- scoped to one entity so real-time gameplay noise
elsewhere in the save (positions, hunger, other Pals' states) doesn't drown
out the change we're looking for.

Identification follows the documented hierarchy in save/inspector/pal_identity.py:
InstanceId (exact, verified-stable) > NickName (exact, NOT assumed unique) >
CharacterID substring (species-level only, will usually return many
candidates and is not a valid way to pick out "the" Pal).

Usage:
  diff_specific_pal.py <before_label> <after_label> --instance-id <guid>
  diff_specific_pal.py <before_label> <after_label> --nickname <exact nickname>
  diff_specific_pal.py <before_label> <after_label> --species <substring>   (lists candidates, will not diff unless exactly one)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import DEFAULT_WORKDIR
from save.adapters.gvas_adapter import load_raw_gvas_dict
from save.differential.differ import diff_properties
from save.inspector.pal_identity import (
    all_refs,
    find_by_instance_id,
    find_by_exact_nickname,
    find_by_character_id_substring,
)


def describe(ref) -> str:
    return f"CharacterID={ref.character_id} NickName={ref.nickname!r} Level={ref.level} InstanceId={ref.instance_id}"


def resolve(refs, args) -> list:
    if args.instance_id:
        ref = find_by_instance_id(refs, args.instance_id)
        return [ref] if ref else []
    if args.nickname:
        return find_by_exact_nickname(refs, args.nickname)
    if args.species:
        return find_by_character_id_substring(refs, args.species)
    return []


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("before_label")
    parser.add_argument("after_label")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--instance-id", help="Exact InstanceId GUID (preferred -- verified stable identity)")
    group.add_argument("--nickname", help="Exact nickname (only reliable if you know it's unique)")
    group.add_argument("--species", help="CharacterID substring (species-level only, likely ambiguous)")
    args = parser.parse_args()

    snapshots_dir = DEFAULT_WORKDIR / "snapshots"
    before_path = snapshots_dir / f"{args.before_label}_Level.sav"
    after_path = snapshots_dir / f"{args.after_label}_Level.sav"

    if not before_path.exists() or not after_path.exists():
        print(f"Missing snapshot(s): before={before_path.exists()} after={after_path.exists()}")
        return

    before_refs = all_refs(load_raw_gvas_dict(before_path))
    after_refs = all_refs(load_raw_gvas_dict(after_path))

    before_matches = resolve(before_refs, args)
    after_matches = resolve(after_refs, args)

    print(f"Matches in BEFORE ({args.before_label}): {len(before_matches)}")
    for r in before_matches:
        print(f"  - {describe(r)}")
    print(f"Matches in AFTER ({args.after_label}): {len(after_matches)}")
    for r in after_matches:
        print(f"  - {describe(r)}")

    if len(before_matches) != 1 or len(after_matches) != 1:
        print(
            "\nNeed exactly one match in each snapshot to diff unambiguously. "
            "Prefer --instance-id once you know it (e.g. from a first pass with --nickname)."
        )
        return

    print(f"\nDiffing: {describe(before_matches[0])}  -->  {describe(after_matches[0])}\n")
    changes = diff_properties(before_matches[0].save_parameter, after_matches[0].save_parameter)
    if not changes:
        print("No changes detected.")
    for c in changes:
        print(c)


if __name__ == "__main__":
    main()
