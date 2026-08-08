"""Finds a Pal by exact nickname and dumps its COMPLETE raw SaveParameter
field set -- every key actually present, not a curated subset -- so nothing
is assumed or missed before a controlled differential test.

Usage: python scripts/dump_by_nickname.py <snapshot_label> <exact_nickname>
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import DEFAULT_WORKDIR
from save.adapters.gvas_adapter import load_raw_gvas_dict
from save.inspector.pal_identity import all_refs, find_by_exact_nickname


def render_value(node):
    """Renders a property-node's value compactly, unwrapping simple ByteProperty
    enum-style {'type': 'None', 'value': X} and EnumProperty wrappers for readability,
    without discarding any information (raw node is still available on request)."""
    if not isinstance(node, dict) or "value" not in node:
        return repr(node)
    v = node["value"]
    if isinstance(v, dict) and set(v.keys()) <= {"type", "value"}:
        return repr(v.get("value"))
    return repr(v)


def main() -> None:
    label, nickname = sys.argv[1], sys.argv[2]
    snapshots_dir = DEFAULT_WORKDIR / "snapshots"
    parsed = load_raw_gvas_dict(snapshots_dir / f"{label}_Level.sav")
    refs = all_refs(parsed)

    matches = find_by_exact_nickname(refs, nickname)
    print(f"Matches for nickname={nickname!r} in {label}: {len(matches)}")
    for m in matches:
        print(f"  - CharacterID={m.character_id} InstanceId={m.instance_id} Level={m.level}")

    if len(matches) != 1:
        print("\nNeed exactly one match to proceed unambiguously. Stopping.")
        return

    ref = matches[0]
    print(f"\n=== Full SaveParameter field dump: InstanceId={ref.instance_id} ===\n")
    for key in sorted(ref.save_parameter.keys()):
        print(f"{key}: {render_value(ref.save_parameter[key])}")


if __name__ == "__main__":
    main()
