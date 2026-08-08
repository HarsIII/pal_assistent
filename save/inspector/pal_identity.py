"""Identification hierarchy for entries in `worldSaveData.CharacterSaveParameterMap`.

VERIFIED (see tests/test_save_researcher_integration.py and
scripts/verify_instance_id_stability.py, run against this project's real
save across a save-to-save transition, n=1217 persisted entries, 0
mismatches): each map entry's key is a raw `{PlayerUId, InstanceId,
DebugName}` struct, and `InstanceId` is:

  1. Unique within a single save (no two entries share it).
  2. Stable across a save-to-save transition for any entry that persists
     (confirmed by CharacterID/IsPlayer never mismatching for a shared
     InstanceId across two real saves of the same world 5 minutes apart).

This makes InstanceId the correct primary key for "is this the same
individual Pal/player" -- NOT NickName (optional, usually absent, and not
guaranteed unique when present) and NOT CharacterID (identifies the
*species*, shared by every instance of it -- this save has ~90 separate
Umihebi-family instances alone).

Identification hierarchy, in priority order, for matching a specific
individual entity:

  1. InstanceId (GUID) -- primary identity, VERIFIED stable (see above).
  2. (No other stable per-instance identifier has been found in the save.
     If one is found later -- e.g. some games also expose a persistent
     "unique tag" -- add it here above Nickname, not below it.)
  3. NickName -- optional secondary identifier. Only useful when the player
     has actually set one, and never assumed unique (nothing prevents two
     Pals sharing a nickname).
  4. CharacterID -- identifies the SPECIES, not the individual. Never use
     alone to pick out "the" Pal a user means.
  5. Level, passives, stats, location/container, etc. -- secondary
     corroborating evidence only. Never sufficient alone for identity: this
     save alone has multiple Umihebi-family Pals sharing the same level
     and/or the same passive list.

This module never picks a "best guess" silently when a query is ambiguous --
callers get back every candidate and must disambiguate (e.g. by asking the
user, or by having the user supply the InstanceId/nickname directly).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PalEntryRef:
    """A reference to one CharacterSaveParameterMap entry, with its identity
    fields extracted per the hierarchy documented above.
    """

    instance_id: str
    player_uid: str
    debug_name: str
    character_id: str | None
    nickname: str
    is_player: bool
    level: int | None
    save_parameter: dict[str, Any]  # the raw RawData.object.SaveParameter dict


def extract_ref(entry: dict[str, Any]) -> PalEntryRef:
    """Extracts identity fields from one raw CharacterSaveParameterMap entry.

    Raises KeyError if the entry doesn't have the expected key shape --
    deliberately not defensive here, since a missing InstanceId means
    something about the save format has changed and callers should find out
    immediately, not silently fall back to a weaker identifier.
    """
    key = entry["key"]
    sp = entry["value"]["RawData"]["value"]["object"]["SaveParameter"]["value"]

    level_node = sp.get("Level")
    level = level_node["value"]["value"] if level_node else None

    return PalEntryRef(
        instance_id=str(key["InstanceId"]["value"]),
        player_uid=str(key["PlayerUId"]["value"]),
        debug_name=key["DebugName"]["value"],
        character_id=sp.get("CharacterID", {}).get("value"),
        nickname=sp.get("NickName", {}).get("value", ""),
        is_player=bool(sp.get("IsPlayer", {}).get("value", False)),
        level=level,
        save_parameter=sp,
    )


def all_refs(parsed_level_sav: dict[str, Any]) -> list[PalEntryRef]:
    char_map = parsed_level_sav["properties"]["worldSaveData"]["value"]["CharacterSaveParameterMap"]["value"]
    return [extract_ref(entry) for entry in char_map]


def find_by_instance_id(refs: list[PalEntryRef], instance_id: str) -> PalEntryRef | None:
    """Priority 1 of the hierarchy: exact, unique, verified-stable identity."""
    for ref in refs:
        if ref.instance_id == instance_id:
            return ref
    return None


def find_by_exact_nickname(refs: list[PalEntryRef], nickname: str) -> list[PalEntryRef]:
    """Priority 3. Returns ALL matches -- nickname uniqueness is NOT assumed."""
    return [r for r in refs if r.nickname == nickname]


def find_by_character_id_substring(refs: list[PalEntryRef], query: str) -> list[PalEntryRef]:
    """Priority 4, species-level only. Almost always returns many candidates
    for a common species -- callers must not treat this as identification.
    """
    q = query.lower()
    return [r for r in refs if r.character_id and q in r.character_id.lower()]
