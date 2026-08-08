"""Phase 0 deliverable: Save Researcher.

Inspects a real Palworld save (read-only, on copies only -- see
save/parser/save_bundle.py) and produces a structured report of what was
found: compression format, parse success/failure per file, discovered
top-level structures and their sizes, and a full field inventory per file.

This tool intentionally does NOT try to build a domain model or interpret
what any field *means* -- that is later-phase work. Its only job is
observation and honest reporting, tagged VERIFIED / INFERRED / UNKNOWN.
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from save.adapters.compression import decompress, SaveCompressionFormat
from save.adapters.gvas_adapter import parse_raw_gvas
from save.inspector.schema_walker import (
    SchemaWalker,
    count_by_top_level_array_or_map,
    summarize_top_level,
)
from save.parser.save_bundle import SaveBundle


@dataclass
class FileInspectionResult:
    path: Path
    role: str  # e.g. "Level.sav", "Players/<uid>.sav"
    file_size_bytes: int
    detected_format: SaveCompressionFormat | None = None
    decompression_ok: bool = False
    decompression_error: str | None = None
    uncompressed_len_header: int | None = None
    uncompressed_len_actual: int | None = None
    parse_ok: bool = False
    parse_error: str | None = None
    engine_version: str | None = None
    save_game_class_name: str | None = None
    top_level_properties: dict[str, str] = field(default_factory=dict)
    top_level_structure_counts: dict[str, int] = field(default_factory=dict)
    field_inventory_size: int = 0  # number of distinct paths discovered


@dataclass
class SaveResearchReport:
    world_dir: Path
    file_results: list[FileInspectionResult] = field(default_factory=list)
    schema_walker: SchemaWalker = field(default_factory=SchemaWalker)


def inspect_file(path: Path, role: str, walker: SchemaWalker) -> FileInspectionResult:
    result = FileInspectionResult(
        path=path, role=role, file_size_bytes=path.stat().st_size
    )
    data = path.read_bytes()

    try:
        decompressed = decompress(data)
        result.detected_format = decompressed.detected_format
        result.decompression_ok = True
        result.uncompressed_len_actual = len(decompressed.raw_gvas)
        if decompressed.detected_format is not SaveCompressionFormat.UNCOMPRESSED_GVAS:
            result.uncompressed_len_header = int.from_bytes(data[0:4], "little")
    except Exception as exc:  # noqa: BLE001 -- Save Researcher must record, not hide, failures
        result.decompression_error = f"{type(exc).__name__}: {exc}"
        return result

    try:
        parsed = parse_raw_gvas(decompressed.raw_gvas)
        result.parse_ok = True
    except Exception as exc:  # noqa: BLE001
        result.parse_error = f"{type(exc).__name__}: {exc}\n" + traceback.format_exc(limit=3)
        return result

    header = parsed.get("header", {})
    result.engine_version = (
        f"{header.get('engine_version_major')}."
        f"{header.get('engine_version_minor')}."
        f"{header.get('engine_version_patch')} "
        f"({header.get('engine_version_branch')})"
    )
    result.save_game_class_name = header.get("save_game_class_name")

    properties = parsed.get("properties", {})
    result.top_level_properties = summarize_top_level(properties)
    result.top_level_structure_counts = count_by_top_level_array_or_map(properties)

    before = len(walker.paths)
    walker.walk_properties(properties, base_path=role)
    result.field_inventory_size = len(walker.paths) - before

    return result


def run_save_researcher(bundle: SaveBundle) -> SaveResearchReport:
    report = SaveResearchReport(world_dir=bundle.world_dir)
    walker = report.schema_walker

    named_singles: list[tuple[str, Path | None]] = [
        ("Level.sav", bundle.level_sav),
        ("LevelMeta.sav", bundle.level_meta_sav),
        ("LocalData.sav", bundle.local_data_sav),
        ("WorldOption.sav", bundle.world_option_sav),
        ("GlobalPalStorage.sav", bundle.global_pal_storage_sav),
        ("UserOption.sav", bundle.user_option_sav),
    ]
    for role, path in named_singles:
        if path is not None:
            report.file_results.append(inspect_file(path, role, walker))

    for player_path in bundle.player_sav_files:
        role = f"Players/{player_path.name}"
        report.file_results.append(inspect_file(player_path, role, walker))

    return report
