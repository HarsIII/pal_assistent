"""Generic, data-driven walker over a parsed GVAS properties dict.

Does not assume any Palworld-specific schema. It only knows the generic GVAS
property shapes that palworld_save_tools' JSON dump produces:

    {"type": "IntProperty", "id": ..., "value": <scalar>}
    {"type": "StructProperty", "struct_type": ..., "value": {<nested properties>} | <scalar/list>}
    {"type": "ArrayProperty", "array_type": ..., "value": {"values": [...]}}
    {"type": "MapProperty", "key_type": ..., "value_type": ..., "value": [{"key":.., "value":..}, ...]}

Anything not matching this shape (e.g. game-specific "rawdata" custom decoders,
which often return plain dicts/lists of already-decoded scalars with no "type"
tag) is recorded as a leaf of its own Python type. This is deliberate: we do
not guess at meaning, we only report what shape of data is actually present.

Output is a field inventory keyed by a normalized path (array/map entries
collapsed to "[]" so repeated entries count as one path), which is exactly
the "discover additional fields, don't assume a fixed schema" requirement
this tool exists for.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PathStats:
    path: str
    shapes_seen: set[str] = field(default_factory=set)
    occurrences: int = 0
    example: Any = None
    example_repr: str = ""

    def record(self, shape: str, example_value: Any) -> None:
        self.shapes_seen.add(shape)
        self.occurrences += 1
        if self.example is None:
            self.example = example_value
            self.example_repr = _safe_repr(example_value)


def _safe_repr(value: Any, limit: int = 200) -> str:
    try:
        r = repr(value)
    except Exception:
        r = "<unrepresentable>"
    return r if len(r) <= limit else r[: limit - 3] + "..."


def _is_property_node(value: Any) -> bool:
    return isinstance(value, dict) and "type" in value and "value" in value


class SchemaWalker:
    """Accumulates PathStats across one or more parsed save dicts."""

    def __init__(self) -> None:
        self.paths: dict[str, PathStats] = {}

    def _stats_for(self, path: str) -> PathStats:
        if path not in self.paths:
            self.paths[path] = PathStats(path=path)
        return self.paths[path]

    def walk_properties(self, properties: dict[str, Any], base_path: str = "") -> None:
        for name, node in properties.items():
            self._walk_node(node, f"{base_path}.{name}" if base_path else name)

    def _walk_node(self, node: Any, path: str) -> None:
        if _is_property_node(node):
            prop_type = node["type"]
            value = node["value"]

            if prop_type == "StructProperty" and isinstance(value, dict):
                # Distinguish "nested property bag" (all children are property
                # nodes) from a special struct's raw payload (Guid/DateTime/...).
                if value and all(_is_property_node(v) for v in value.values()):
                    self._stats_for(path).record(
                        f"StructProperty({node.get('struct_type')}, nested)", None
                    )
                    self.walk_properties(value, path)
                else:
                    struct_type = node.get("struct_type", "?")
                    self._stats_for(path).record(
                        f"StructProperty({struct_type}, raw)", value
                    )

            elif prop_type == "ArrayProperty" and isinstance(value, dict) and "values" in value:
                array_type = node.get("array_type", "?")
                values = value["values"]
                self._stats_for(path).record(
                    f"ArrayProperty[{array_type}] (len examples vary)", None
                )
                item_path = f"{path}[]"
                for item in values:
                    self._walk_node_or_leaf(item, item_path)

            elif prop_type == "ArrayProperty":
                # A game-specific "rawdata" custom decoder (see vendored
                # rawdata/*.py) replaced the normal {"values": [...]} shape
                # with its own decoded structure (e.g. RawData -> {"object": {...}}).
                # Recurse into it like any other untagged structure instead of
                # treating it as an opaque leaf -- this is where Pal-specific
                # fields (Talent_*, PassiveSkillList, EquipWaza, ...) live.
                array_type = node.get("array_type", "?")
                self._stats_for(path).record(
                    f"ArrayProperty[{array_type}] (custom-decoded)", None
                )
                self._walk_node_or_leaf(value, path)

            elif prop_type == "MapProperty" and isinstance(value, list):
                key_type = node.get("key_type", "?")
                value_type = node.get("value_type", "?")
                self._stats_for(path).record(
                    f"MapProperty[{key_type} -> {value_type}]", None
                )
                for entry in value:
                    if isinstance(entry, dict) and "value" in entry:
                        self._walk_node_or_leaf(entry["value"], f"{path}{{}}")

            else:
                self._stats_for(path).record(f"{prop_type} (leaf)", value)
        else:
            self._walk_node_or_leaf(node, path)

    def _walk_node_or_leaf(self, node: Any, path: str) -> None:
        if _is_property_node(node):
            self._walk_node(node, path)
        elif isinstance(node, dict):
            # Plain dict with no "type" tag: almost always a game-specific
            # "rawdata" custom decoder's output (see vendored
            # rawdata/*.py). Record its keys as children directly.
            self._stats_for(path).record("dict (custom-decoded, untagged)", None)
            for k, v in node.items():
                self._walk_node_or_leaf(v, f"{path}.{k}")
        elif isinstance(node, list):
            self._stats_for(path).record(f"list[{len(node)}] (custom-decoded, untagged)", None)
            item_path = f"{path}[]"
            for item in node:
                self._walk_node_or_leaf(item, item_path)
        else:
            self._stats_for(path).record(type(node).__name__, node)

    def summary_rows(self) -> list[PathStats]:
        return sorted(self.paths.values(), key=lambda s: s.path)


def summarize_top_level(properties: dict[str, Any]) -> dict[str, str]:
    """Cheap one-level summary: top-level property name -> its declared type."""
    out = {}
    for name, node in properties.items():
        if _is_property_node(node):
            out[name] = node["type"]
        else:
            out[name] = type(node).__name__
    return out


def count_by_top_level_array_or_map(properties: dict[str, Any]) -> dict[str, int]:
    """For every top-level ArrayProperty/MapProperty (and one level of nesting
    under a top-level StructProperty, which is where Palworld keeps
    `worldSaveData`), report the number of entries. Purely structural, no
    assumptions about what the entries mean.
    """
    counts: dict[str, int] = {}

    def inspect(name: str, node: Any) -> None:
        if not _is_property_node(node):
            return
        if node["type"] == "ArrayProperty" and isinstance(node["value"], dict):
            counts[name] = len(node["value"].get("values", []))
        elif node["type"] == "MapProperty" and isinstance(node["value"], list):
            counts[name] = len(node["value"])
        elif node["type"] == "StructProperty" and isinstance(node["value"], dict):
            for sub_name, sub_node in node["value"].items():
                inspect(f"{name}.{sub_name}", sub_node)

    for name, node in properties.items():
        inspect(name, node)
    return counts
