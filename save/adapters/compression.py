"""Decompression boundary for Palworld .sav files.

Isolates the rest of the system from the vendored parsing library (see
save/adapters/vendor/palworld_save_tools/VENDOR_INFO.md for why this specific
fork is vendored, and what it fixes relative to the official package).

Read-only by design: this module intentionally does not expose a compress /
write path. See project rule "READ-ONLY" (never write to .sav files in the MVP).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import save.adapters.vendor  # noqa: F401  (side effect: puts vendored package on sys.path)
from palworld_save_tools.palsav import decompress_sav_to_gvas as _vendor_decompress


class SaveCompressionFormat(Enum):
    """Confidence: VERIFIED (empirically, against real save files -- see SAVE_FORMAT.md)."""

    PLZ_ZLIB = "PlZ"
    PLM_OODLE = "PlM"
    CNK_CHUNK = "CNK"
    UNCOMPRESSED_GVAS = "GVAS"


@dataclass(frozen=True)
class DecompressedSav:
    raw_gvas: bytes
    save_type: int
    detected_format: SaveCompressionFormat


def detect_format(data: bytes) -> SaveCompressionFormat:
    if data[:4] == b"GVAS":
        return SaveCompressionFormat.UNCOMPRESSED_GVAS
    magic = data[8:11]
    if magic == b"PlZ":
        return SaveCompressionFormat.PLZ_ZLIB
    if magic == b"PlM":
        return SaveCompressionFormat.PLM_OODLE
    if magic == b"CNK":
        return SaveCompressionFormat.CNK_CHUNK
    raise ValueError(f"Unrecognized .sav magic bytes: {magic!r}")


def decompress(data: bytes) -> DecompressedSav:
    """Decompress raw .sav file bytes into raw GVAS bytes.

    Handles the case of already-uncompressed GVAS files (e.g. UserOption.sav,
    which -- verified empirically -- ships with no size/magic wrapper header at all).
    """
    fmt = detect_format(data)
    if fmt is SaveCompressionFormat.UNCOMPRESSED_GVAS:
        return DecompressedSav(raw_gvas=data, save_type=0x00, detected_format=fmt)

    raw_gvas, save_type = _vendor_decompress(data)
    return DecompressedSav(raw_gvas=raw_gvas, save_type=save_type, detected_format=fmt)
