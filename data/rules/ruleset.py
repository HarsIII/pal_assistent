"""Versioned fact/rule registry (project rules: VERSIONING, DATA-DRIVEN, DATA SOURCES).

This is data, not code: every fact the project relies on is recorded here with
its confidence level and provenance, instead of being silently assumed inside
parsing/engine code. Nothing here is permanent -- confidence and rules_version
must be revisited whenever the game updates.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Confidence(str, Enum):
    VERIFIED = "VERIFIED"          # empirically confirmed against real save/game data by this project
    INFERRED = "INFERRED"          # derived from a community/decoder naming or pattern, not independently confirmed
    UNKNOWN = "UNKNOWN"            # explicitly not yet known -- do not guess
    USER_DEFINED = "USER_DEFINED"  # provided by the user, not derived


class SourceType(str, Enum):
    OFFICIAL = "OFFICIAL"
    DATAMINED = "DATAMINED"
    COMMUNITY = "COMMUNITY"
    SAVE_OBSERVED = "SAVE_OBSERVED"
    USER_DEFINED = "USER_DEFINED"
    INFERRED = "INFERRED"


@dataclass(frozen=True)
class Fact:
    statement: str
    confidence: Confidence
    source_type: SourceType
    source: str
    date_recorded: str  # ISO date, e.g. "2026-08-07"
    game_version: str | None = None
    rules_version: str = "0.1"


# Facts established during Phase 0 (Save Researcher). Extend this list as new
# phases confirm or overturn things -- never edit a Fact in place if the game
# has since changed; add a new one and note the supersession.
PHASE_0_FACTS: list[Fact] = [
    Fact(
        statement=(
            "This save's world files (Level.sav, LevelMeta.sav, LocalData.sav, "
            "WorldOption.sav, GlobalPalStorage.sav, Players/*.sav) are wrapped in a "
            "12-byte header (uncompressed_len:u32LE, compressed_len:u32LE, "
            "3-byte magic, 1-byte save_type) followed by compressed payload, with "
            "magic bytes 'PlM' (Oodle) rather than the older 'PlZ' (zlib)."
        ),
        confidence=Confidence.VERIFIED,
        source_type=SourceType.SAVE_OBSERVED,
        source="Direct binary inspection of this machine's save files; cross-checked against community reports of the PlM/Oodle format introduced in Palworld v0.6+",
        date_recorded="2026-08-07",
    ),
    Fact(
        statement=(
            "UserOption.sav (account-level, not per-world) has no wrapper header at "
            "all -- it is stored as raw, uncompressed GVAS starting directly with the "
            "'GVAS' magic."
        ),
        confidence=Confidence.VERIFIED,
        source_type=SourceType.SAVE_OBSERVED,
        source="Direct binary inspection",
        date_recorded="2026-08-07",
    ),
    Fact(
        statement=(
            "Save engine version is Unreal Engine 5.1.1 (branch '++UE5+Release-5.1'), "
            "GVAS SaveGameFileVersion=3."
        ),
        confidence=Confidence.VERIFIED,
        source_type=SourceType.SAVE_OBSERVED,
        source="GvasHeader parsed from this save's files",
        date_recorded="2026-08-07",
    ),
    Fact(
        statement=(
            "The official PyPI package 'palworld-save-tools' (cheahjs, v0.24.0, "
            "released 2024-10-06) has no Oodle/PlM support at all and has not been "
            "updated since; several of its hardcoded raw-binary sub-decoders "
            "(base_camp, character, foliage_model_instance, group, map_model) raise "
            "a hard exception on any trailing bytes they don't recognize, which "
            "crashes parsing of this save's Level.sav entirely."
        ),
        confidence=Confidence.VERIFIED,
        source_type=SourceType.SAVE_OBSERVED,
        source="Reproduced directly: installed palworld-save-tools==0.24.0 and ran it against this save's files",
        date_recorded="2026-08-07",
    ),
    Fact(
        statement=(
            "The KrisCris/palworld-save-tools fork (commit 82dc6ad06e6162b29c0ef7d321fed2a73609a4d6) "
            "fully parses this save's Level.sav, GlobalPalStorage.sav, and Players/*.sav. "
            "LocalData.sav still fails: '.SaveData.Local_MaxFriendshipPalIds' has an "
            "unrecognized map value type, and the decoder's fallback guess ('assuming "
            "StructProperty') desynchronizes the rest of the byte stream."
        ),
        confidence=Confidence.VERIFIED,
        source_type=SourceType.SAVE_OBSERVED,
        source="Reproduced directly: vendored this fork and ran it against this save's files (see save/adapters/vendor/palworld_save_tools/VENDOR_INFO.md)",
        date_recorded="2026-08-07",
    ),
    Fact(
        statement=(
            "Field names inside parsed Pal/player/base structures (e.g. Talent_HP, "
            "Talent_Shot, Talent_Defense, PassiveSkillList, EquipWaza, Rank, "
            "IsRarePal) come from the community decoder's own naming and type hints, "
            "not from this project's independent verification of game mechanics or "
            "official documentation. Treat their exact meaning (e.g. which Talent_* "
            "corresponds to which in-game Potential stat) as INFERRED until "
            "cross-checked against observed in-game behavior."
        ),
        confidence=Confidence.INFERRED,
        source_type=SourceType.COMMUNITY,
        source="palworld_save_tools PALWORLD_CUSTOM_PROPERTIES / PALWORLD_TYPE_HINTS field naming",
        date_recorded="2026-08-07",
    ),
]
