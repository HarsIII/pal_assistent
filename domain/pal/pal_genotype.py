"""PalGenotype: the subset of a PalInstance's data that a future breeding
engine would read from a parent.

IMPORTANT: this does NOT claim to represent what Palworld's breeding
mechanics actually inherit -- that is exactly the open question the (not yet
built) breeding engine phase must verify empirically (differential analysis
of real breeding actions), not assume. This class exists only as a stable,
narrow "parent-facing view" of a PalInstance, so the future breeding engine
depends on this small surface instead of the full PalInstance/save shape.

Do not add a field here on the assumption that it's heritable. Add it only
once breeding engine work has a reason to read it, and note the confidence
of "this is actually inherited" separately (in data/rules/ruleset.py) from
"this field exists on the parent."
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.pal.pal_instance import PalInstance


@dataclass(frozen=True)
class PalGenotype:
    species_id: str
    sex: str | None
    passive_skills: tuple[str, ...] = field(default_factory=tuple)
    potential_hp: int | None = None
    potential_shot: int | None = None
    potential_defense: int | None = None


def from_pal_instance(pal: PalInstance) -> PalGenotype:
    if pal.is_player:
        raise ValueError("Cannot derive a PalGenotype from a player entry")
    return PalGenotype(
        species_id=pal.species_id,
        sex=pal.sex,
        passive_skills=pal.passive_skills,
        potential_hp=pal.potential_hp,
        potential_shot=pal.potential_shot,
        potential_defense=pal.potential_defense,
    )
