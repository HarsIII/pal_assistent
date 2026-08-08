"""Normalization: RAW SAVE MODEL -> DOMAIN MODEL for Pal/player entries.

This is the only place that translates between the raw parsed-GVAS property
shapes (see save/inspector/schema_walker.py's docstring for what those look
like) and the clean domain/pal/pal_instance.py dataclass. Everything above
this layer should only ever see PalInstance, never the raw dict shape.
"""

from __future__ import annotations

from typing import Any

from domain.pal.pal_instance import FriendshipStats, PalContainerSlot, PalInstance
from save.inspector.pal_identity import PalEntryRef


def _scalar(sp: dict[str, Any], name: str) -> Any:
    node = sp.get(name)
    if node is None:
        return None
    value = node.get("value")
    # ByteProperty enum-like values are wrapped as {"type": "None", "value": X}
    if isinstance(value, dict) and set(value.keys()) <= {"type", "value"}:
        return value.get("value")
    return value


def _array_values(sp: dict[str, Any], name: str) -> tuple[Any, ...]:
    node = sp.get(name)
    if node is None:
        return ()
    values = node.get("value", {}).get("values", [])
    return tuple(values)


def _hp_value(sp: dict[str, Any], name: str) -> float | None:
    """Applies the VERIFIED Hp.Value = displayed_HP * 1000 scaling (see
    data/rules/ruleset.py). Same scaling for ShieldHP is an UNVERIFIED
    extension, applied here for consistency but flagged in pal_instance.py's
    docstring.
    """
    node = sp.get(name)
    if node is None:
        return None
    raw = node.get("value", {}).get("Value", {}).get("value")
    return raw / 1000 if raw is not None else None


def _slot(sp: dict[str, Any]) -> PalContainerSlot | None:
    node = sp.get("SlotId")
    if node is None:
        return None
    value = node["value"]
    container_id = value["ContainerId"]["value"]["ID"]["value"]
    slot_index = value["SlotIndex"]["value"]
    return PalContainerSlot(container_id=str(container_id), slot_index=slot_index)


def _friendship(sp: dict[str, Any]) -> FriendshipStats | None:
    if "FriendshipPoint" not in sp:
        return None
    return FriendshipStats(
        points=_scalar(sp, "FriendshipPoint") or 0,
        otomo_seconds=_scalar(sp, "FriendshipOtomoSec") or 0,
        active_otomo_seconds=_scalar(sp, "FriendshipActiveOtomoSec") or 0,
        basecamp_seconds=_scalar(sp, "FriendshipBasecampSec") or 0,
    )


def map_pal_entry_to_instance(ref: PalEntryRef) -> PalInstance:
    """Maps one CharacterSaveParameterMap entry (already resolved to a
    PalEntryRef -- see save/inspector/pal_identity.py) to a PalInstance.

    Works for both Pal and player entries; player entries will have most
    Pal-specific fields as None (is_player=True signals this to callers).
    """
    sp = ref.save_parameter

    old_owners = sp.get("OldOwnerPlayerUIds")
    old_owner_uids = (
        tuple(str(u) for u in old_owners["value"]["values"]) if old_owners else ()
    )
    owner_node = sp.get("OwnerPlayerUId")
    owner_uid = str(owner_node["value"]) if owner_node else None

    return PalInstance(
        instance_id=ref.instance_id,
        species_id=ref.character_id or "",
        is_player=ref.is_player,
        nickname=ref.nickname,
        sex=_scalar(sp, "Gender"),
        level=ref.level,
        experience=_scalar(sp, "Exp"),
        passive_skills=_array_values(sp, "PassiveSkillList"),
        equipped_active_skills=_array_values(sp, "EquipWaza"),
        mastered_active_skills=_array_values(sp, "MasteredWaza"),
        potential_hp=_scalar(sp, "Talent_HP"),
        potential_shot=_scalar(sp, "Talent_Shot"),
        potential_defense=_scalar(sp, "Talent_Defense"),
        condensation_rank=_scalar(sp, "Rank"),
        soul_hp=_scalar(sp, "Rank_HP"),
        soul_attack=_scalar(sp, "Rank_Attack"),
        soul_defence=_scalar(sp, "Rank_Defence"),
        soul_work_speed=_scalar(sp, "Rank_CraftSpeed"),
        is_rare_pal=_scalar(sp, "IsRarePal"),
        unique_npc_id=_scalar(sp, "UniqueNPCID"),
        hp=_hp_value(sp, "Hp"),
        shield_hp=_hp_value(sp, "ShieldHP"),
        owner_player_uid=owner_uid,
        previous_owner_player_uids=old_owner_uids,
        slot=_slot(sp),
        friendship=_friendship(sp),
        skin_name=_scalar(sp, "SkinName"),
    )
