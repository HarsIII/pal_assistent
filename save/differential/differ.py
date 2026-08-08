"""Differential Save Analyzer (project rule: dev/research tool, not user-facing).

Compares two parsed GVAS property dicts (e.g. the same world's Level.sav at
two points in time) and reports what changed, by path. This is the intended
way to reverse-engineer what an unknown field means: change one thing in
game, save, diff, and see exactly which path moved.

Known limitation: ArrayProperty entries with the plain {"values": [...]} shape
are compared by index, not identity -- if the game reorders an array between
saves, this will show spurious changes. MapProperty entries ARE compared by
key (e.g. a Pal's GUID), which is identity-stable across saves.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ChangeType(str, Enum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    CHANGED = "CHANGED"


@dataclass
class Change:
    path: str
    change_type: ChangeType
    before: Any = None
    after: Any = None

    def __repr__(self) -> str:
        if self.change_type is ChangeType.ADDED:
            return f"+ {self.path} = {_short(self.after)}"
        if self.change_type is ChangeType.REMOVED:
            return f"- {self.path} (was {_short(self.before)})"
        return f"~ {self.path}: {_short(self.before)} -> {_short(self.after)}"


def _short(value: Any, limit: int = 120) -> str:
    r = repr(value)
    return r if len(r) <= limit else r[: limit - 3] + "..."


def _is_property_node(value: Any) -> bool:
    return isinstance(value, dict) and "type" in value and "value" in value


def diff_properties(before: dict[str, Any], after: dict[str, Any], base_path: str = "") -> list[Change]:
    changes: list[Change] = []
    all_names = set(before.keys()) | set(after.keys())
    for name in sorted(all_names):
        path = f"{base_path}.{name}" if base_path else name
        if name not in before:
            changes.append(Change(path, ChangeType.ADDED, after=after[name]))
        elif name not in after:
            changes.append(Change(path, ChangeType.REMOVED, before=before[name]))
        else:
            changes.extend(_diff_node(before[name], after[name], path))
    return changes


def _diff_node(before: Any, after: Any, path: str) -> list[Change]:
    before_is_prop = _is_property_node(before)
    after_is_prop = _is_property_node(after)

    if before_is_prop != after_is_prop:
        return [Change(path, ChangeType.CHANGED, before=before, after=after)]

    if not before_is_prop:
        return _diff_plain(before, after, path)

    if before["type"] != after["type"]:
        return [Change(path, ChangeType.CHANGED, before=before, after=after)]

    prop_type = before["type"]
    before_val, after_val = before["value"], after["value"]

    if prop_type == "StructProperty" and isinstance(before_val, dict) and isinstance(after_val, dict):
        if all(_is_property_node(v) for v in before_val.values()) and all(
            _is_property_node(v) for v in after_val.values()
        ):
            return diff_properties(before_val, after_val, path)
        return _diff_plain(before_val, after_val, path)

    if prop_type == "ArrayProperty":
        b_values = before_val.get("values") if isinstance(before_val, dict) else None
        a_values = after_val.get("values") if isinstance(after_val, dict) else None
        if b_values is not None and a_values is not None:
            return _diff_indexed_list(b_values, a_values, f"{path}[]")
        return _diff_plain(before_val, after_val, path)

    if prop_type == "MapProperty" and isinstance(before_val, list) and isinstance(after_val, list):
        return _diff_keyed_list(before_val, after_val, path)

    if before_val != after_val:
        return [Change(path, ChangeType.CHANGED, before=before_val, after=after_val)]
    return []


def _diff_plain(before: Any, after: Any, path: str) -> list[Change]:
    if isinstance(before, dict) and isinstance(after, dict):
        changes: list[Change] = []
        for key in sorted(set(before.keys()) | set(after.keys())):
            sub_path = f"{path}.{key}"
            if key not in before:
                changes.append(Change(sub_path, ChangeType.ADDED, after=after[key]))
            elif key not in after:
                changes.append(Change(sub_path, ChangeType.REMOVED, before=before[key]))
            else:
                changes.extend(_diff_node(before[key], after[key], sub_path))
        return changes
    if isinstance(before, list) and isinstance(after, list):
        return _diff_indexed_list(before, after, f"{path}[]")
    if before != after:
        return [Change(path, ChangeType.CHANGED, before=before, after=after)]
    return []


def _diff_indexed_list(before: list[Any], after: list[Any], item_path: str) -> list[Change]:
    changes: list[Change] = []
    for i in range(max(len(before), len(after))):
        if i >= len(before):
            changes.append(Change(f"{item_path}#{i}", ChangeType.ADDED, after=after[i]))
        elif i >= len(after):
            changes.append(Change(f"{item_path}#{i}", ChangeType.REMOVED, before=before[i]))
        else:
            changes.extend(_diff_node(before[i], after[i], f"{item_path}#{i}"))
    return changes


def _entry_key_repr(entry: dict[str, Any]) -> str:
    key = entry.get("key")
    if _is_property_node(key):
        key = key.get("value")
    return repr(key)


def _diff_keyed_list(before: list[dict], after: list[dict], base_path: str) -> list[Change]:
    before_by_key = {_entry_key_repr(e): e.get("value") for e in before}
    after_by_key = {_entry_key_repr(e): e.get("value") for e in after}
    changes: list[Change] = []
    for key_repr in sorted(set(before_by_key.keys()) | set(after_by_key.keys())):
        path = f"{base_path}{{{key_repr}}}"
        if key_repr not in before_by_key:
            changes.append(Change(path, ChangeType.ADDED, after=after_by_key[key_repr]))
        elif key_repr not in after_by_key:
            changes.append(Change(path, ChangeType.REMOVED, before=before_by_key[key_repr]))
        else:
            changes.extend(_diff_node(before_by_key[key_repr], after_by_key[key_repr], path))
    return changes
