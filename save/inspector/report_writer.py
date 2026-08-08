"""Renders the mechanically-derived parts of the Save Research Report.

Deliberately narrow: this module only turns SaveResearchReport /
SchemaWalker data into markdown tables. Narrative sections (hypotheses,
open problems, next steps) are authored separately -- they require judgment,
not just data transcription, and mixing the two here would blur what's an
observed fact versus an interpretation.
"""

from __future__ import annotations

from save.inspector.save_researcher import SaveResearchReport


def render_file_status_table(report: SaveResearchReport) -> str:
    lines = [
        "| File | Size | Format | Decompress | Parse | Engine Version |",
        "|---|---|---|---|---|---|",
    ]
    for r in report.file_results:
        fmt = r.detected_format.value if r.detected_format else "?"
        decompress_status = "OK" if r.decompression_ok else f"FAILED: {r.decompression_error}"
        parse_status = "OK" if r.parse_ok else f"FAILED: {r.parse_error.splitlines()[0] if r.parse_error else '?'}"
        lines.append(
            f"| {r.role} | {r.file_size_bytes:,} B | {fmt} | {decompress_status} | "
            f"{parse_status} | {r.engine_version or '-'} |"
        )
    return "\n".join(lines)


def render_structure_counts(report: SaveResearchReport) -> str:
    lines = ["### Top-level structure counts (per file, where parse succeeded)\n"]
    for r in report.file_results:
        if not r.parse_ok or not r.top_level_structure_counts:
            continue
        lines.append(f"**{r.role}**")
        for path, count in sorted(r.top_level_structure_counts.items()):
            lines.append(f"- `{path}`: {count} entries")
        lines.append("")
    return "\n".join(lines)


def render_top_level_properties(report: SaveResearchReport) -> str:
    lines = ["### Top-level properties observed (per file)\n"]
    for r in report.file_results:
        if not r.parse_ok:
            continue
        lines.append(f"**{r.role}**")
        for name, type_name in sorted(r.top_level_properties.items()):
            lines.append(f"- `{name}`: {type_name}")
        lines.append("")
    return "\n".join(lines)


def render_field_inventory(report: SaveResearchReport, path_prefix: str, max_rows: int = 300) -> str:
    """Render the full discovered-field inventory for paths starting with
    `path_prefix` (e.g. "Level.sav.worldSaveData.CharacterSaveParameterMap").
    """
    rows = [
        s for s in report.schema_walker.summary_rows() if s.path.startswith(path_prefix)
    ]
    lines = [
        f"### Field inventory under `{path_prefix}` ({len(rows)} distinct paths, showing up to {max_rows})\n",
        "| Path | Shapes seen | Occurrences | Example |",
        "|---|---|---|---|",
    ]
    for s in rows[:max_rows]:
        shapes = ", ".join(sorted(s.shapes_seen))
        lines.append(f"| `{s.path}` | {shapes} | {s.occurrences} | `{s.example_repr}` |")
    return "\n".join(lines)
