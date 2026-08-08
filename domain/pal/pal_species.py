"""PalSpecies: static, per-species data (base stats, elements, partner skill,
breeding rank, etc.).

IMPORTANT: this is a SCHEMA ONLY. No instances of this dataclass exist yet in
the project. Species-level data is NOT present in a save file at all -- a
save only ever contains a species_id (CharacterID) reference. Populating
this requires an external, citable data source (official game files,
datamining, or a maintained community database), tracked with the same
VERIFIED/INFERRED/UNKNOWN/USER_DEFINED discipline as everything else in this
project (see data/rules/ruleset.py). Do not invent values for any field here.

This schema will change once a real data source is selected -- treat field
names as provisional until then.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BaseStats:
    hp: int
    attack: int
    defense: int
    work_speed: int


@dataclass(frozen=True)
class PalSpecies:
    species_id: str  # matches PalInstance.species_id / save CharacterID
    display_name: str
    elements: tuple[str, ...] = field(default_factory=tuple)
    base_stats: BaseStats | None = None
    gender_ratio: dict[str, float] | None = None  # e.g. {"male": 0.5, "female": 0.5}

    # Breeding-relevant static data (Section 6.1 of the project spec). All
    # UNKNOWN / unpopulated until a real data source is sourced.
    breeding_power: int | None = None  # used by the breeding-combination formula
    partner_skill_id: str | None = None
    work_suitabilities: dict[str, int] | None = None
    active_skill_pool: tuple[str, ...] = field(default_factory=tuple)

    source: str | None = None  # citation for where this row's data came from
