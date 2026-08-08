"""PalInstance: a single Pal (or player) as it actually exists in a save.

Per project rule (separate static species data from individual instance
data): this holds ONLY what's stored per-instance in
worldSaveData.CharacterSaveParameterMap. Species-level static data
(base stats, partner skill, breeding rank, etc.) belongs in PalSpecies
(domain/pal/pal_species.py), sourced externally -- it is NOT derivable from
a save file at all.

Confidence notes (see data/rules/ruleset.py for the full evidence trail --
summarized here so this stays legible without cross-referencing):

  VERIFIED:
    - instance_id is unique and stable across saves (empirically verified,
      n=1217, 0 mismatches).
    - hp/shield_hp scaling: Hp.Value = displayed_HP * 1000 (user-confirmed
      against in-game UI). ShieldHP.Value is assumed to use the same scaling
      (same FixedPoint64 struct type) but this specific extension is
      UNVERIFIED.
    - condensation_rank changes when a Pal is condensed (2 controlled tests).
    - soul_hp/attack/defence/work_speed represent Pal Soul investment,
      independent of condensation_rank (see ruleset.py for the full
      evidence trail; one case, ClownRabbit/"Dupina", directly user-confirmed).

  INFERRED (community/decoder naming, not independently confirmed):
    - species_id -> potential/talent field semantics (potential_hp/shot/defense
      almost certainly correspond to the in-game "Potential" stats, but the
      exact display-name mapping, e.g. whether "Shot" reads as "Attack" in
      the UI, is not confirmed).
    - condensation_rank = visual_stars + 1 (2 consistent data points, not yet
      promoted to VERIFIED per explicit decision to require more evidence).

  UNKNOWN:
    - is_alpha (mapped from IsRarePal): could mean "Alpha" or something else
      (e.g. a rare color variant) -- deliberately left unresolved, not
      assumed, pending correlation against Pals independently known to be
      (or not be) Alpha.
    - Which container_id values correspond to "base," "party," or "Palbox" --
      not yet cross-referenced against BaseCampSaveData/GroupSaveDataMap.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class PalContainerSlot:
    """Where this instance currently sits. container_id's real-world meaning
    (base storage / party / Palbox / etc.) is UNKNOWN -- not yet resolved.
    """

    container_id: str
    slot_index: int


@dataclass(frozen=True)
class FriendshipStats:
    points: int
    otomo_seconds: int  # time spent as active companion ("Otomo")
    active_otomo_seconds: int
    basecamp_seconds: int  # time spent assigned to a base


@dataclass(frozen=True)
class PalInstance:
    # Identity (see pal_identity.py for why instance_id is the correct key)
    instance_id: str
    species_id: str  # CharacterID -- an internal codename, NOT the display name
    is_player: bool

    # Only meaningful when is_player is False; None fields below are for
    # players, whose CharacterSaveParameterMap entries don't carry Pal data.
    nickname: str = ""
    sex: Optional[str] = None  # raw EPalGenderType::* enum value
    level: Optional[int] = None
    experience: Optional[int] = None

    passive_skills: tuple[str, ...] = field(default_factory=tuple)
    equipped_active_skills: tuple[str, ...] = field(default_factory=tuple)
    mastered_active_skills: tuple[str, ...] = field(default_factory=tuple)

    # "Potential" / IV-like stats. INFERRED semantics -- see module docstring.
    potential_hp: Optional[int] = None
    potential_shot: Optional[int] = None
    potential_defense: Optional[int] = None

    # Condensation ("star") progression. INFERRED star-count mapping.
    condensation_rank: Optional[int] = None

    # Pal Soul investment per stat (0-20 observed). Independent of
    # condensation_rank -- see module docstring.
    soul_hp: Optional[int] = None
    soul_attack: Optional[int] = None
    soul_defence: Optional[int] = None
    soul_work_speed: Optional[int] = None

    # UNKNOWN semantics -- deliberately not mapped to "is_alpha" or similar.
    is_rare_pal: Optional[bool] = None
    unique_npc_id: Optional[str] = None

    hp: Optional[float] = None  # displayed HP (already divided by 1000)
    shield_hp: Optional[float] = None  # UNVERIFIED same scaling as hp

    owner_player_uid: Optional[str] = None
    previous_owner_player_uids: tuple[str, ...] = field(default_factory=tuple)
    slot: Optional[PalContainerSlot] = None
    friendship: Optional[FriendshipStats] = None

    skin_name: Optional[str] = None
