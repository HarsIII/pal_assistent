"""GVAS property-tree parsing boundary.

This is the ONLY module in the project allowed to know that Palworld saves are
Unreal Engine GVAS files. Everything above this layer (normalization, domain
model, engine, optimizer, assistant, GUI) must consume the plain dict produced
by `load_raw_gvas_dict`, never the vendored library's own types directly.

Read-only by design: only exposes read/parse, never write/compress.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from save.adapters.compression import decompress

import save.adapters.vendor  # noqa: F401  (side effect: puts vendored package on sys.path)
from palworld_save_tools.gvas import GvasFile
from palworld_save_tools.paltypes import PALWORLD_CUSTOM_PROPERTIES, PALWORLD_TYPE_HINTS


def parse_raw_gvas(raw_gvas: bytes, *, allow_nan: bool = True) -> dict[str, Any]:
    """Parse decompressed GVAS bytes into a plain dict (header/properties/trailer)."""
    gvas_file = GvasFile.read(
        raw_gvas, PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES, allow_nan=allow_nan
    )
    return gvas_file.dump()


def load_raw_gvas_dict(sav_path: Path, *, allow_nan: bool = True) -> dict[str, Any]:
    """Read a .sav file from disk (read-only) and return its parsed GVAS dict.

    Raises whatever exception the underlying decompressor/parser raises on
    failure -- callers (e.g. the Save Researcher) are responsible for catching
    and recording failures rather than this layer silently hiding them.
    """
    data = sav_path.read_bytes()
    decompressed = decompress(data)
    return parse_raw_gvas(decompressed.raw_gvas, allow_nan=allow_nan)
