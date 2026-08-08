"""BreedingDatabase: the only intended access point for the vendored
palcalc species/breeding data (see data/breeding/vendor/palcalc/VENDOR_INFO.md
for full provenance). Nothing outside this module should read db.json or
breeding.json directly.

Confidence summary (see data/rules/ruleset.py for the full entries):
  - Species records and the breeding-combination table: DATAMINED, directly
    cross-checked against this project's own real save data (species
    identity resolution verified for every CharacterID tested).
  - BreedingMechanics (IV/passive inheritance weights) and
    BreedingGenderProbability: DATAMINED/INFERRED, NOT yet independently
    verified by this project. Exposed separately (get_breeding_mechanics_raw,
    get_breeding_gender_probability_raw) specifically so callers can't
    accidentally treat them with the same confidence as the rest.
  - MinBreedingSteps: vendored source data only. This project's own
    breeding-pathfinding solver (not yet built) is the authoritative result;
    this table may be used as a cross-check, never as the answer itself.
    Exposed as get_min_breeding_steps_raw() to make that impossible to miss.

Known gaps in the vendored data itself (not this module's fault -- see
VENDOR_INFO.md): PartnerSkill is null for all 299 species in the vendored
snapshot; per-species elemental typing is not present on Pal records at all
(only a standalone Name/InternalName element list exists, not linked to
species). Both surface as empty/None in PalSpecies until a source with that
data is found.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from domain.pal.pal_species import BaseStats, PalSpecies

_VENDOR_DIR = Path(__file__).parent / "vendor" / "palcalc"
_DB_PATH = _VENDOR_DIR / "db.json"
_BREEDING_PATH = _VENDOR_DIR / "breeding.json"

_SOURCE_CITATION = (
    "tylercamp/palcalc @ c59712e24b839a0bedef16b06a1a0117e8741fe3 "
    "(see data/breeding/vendor/palcalc/VENDOR_INFO.md)"
)


@dataclass(frozen=True)
class BreedingCombination:
    parent1: str
    parent1_gender: str  # "WILDCARD" | "MALE" | "FEMALE"
    parent2: str
    parent2_gender: str
    child: str


def _species_from_raw(raw: dict) -> PalSpecies:
    work_suitability = {k: v for k, v in raw.get("WorkSuitability", {}).items() if v}
    return PalSpecies(
        species_id=raw["InternalName"],
        display_name=raw["Name"],
        elements=(),  # UNKNOWN -- not present per-species in this data source
        base_stats=BaseStats(
            hp=raw["Hp"],
            attack=raw["Attack"],
            defense=raw["Defense"],
            work_speed=raw["CraftSpeed"],
        ),
        gender_ratio=None,  # see BreedingDatabase.get_breeding_gender_probability_raw
        breeding_power=raw["BreedingPower"],
        partner_skill_id=raw["PartnerSkill"],  # UNKNOWN -- null for all 299 species vendored
        work_suitabilities=work_suitability or None,
        active_skill_pool=(),  # UNKNOWN -- not present in this data source
        source=_SOURCE_CITATION,
    )


class BreedingDatabase:
    def __init__(self, db_path: Path = _DB_PATH, breeding_path: Path = _BREEDING_PATH):
        with open(db_path, encoding="utf-8") as f:
            self._db = json.load(f)
        with open(breeding_path, encoding="utf-8") as f:
            self._breeding = json.load(f)

        self._species_by_id: dict[str, PalSpecies] = {
            raw["InternalName"]: _species_from_raw(raw) for raw in self._db["Pals"]
        }

        # Indexed by the UNORDERED species pair (order the caller queries with
        # shouldn't matter), but each combination's own parent1/parent2 order
        # AND gender assignment is preserved -- verified against the real
        # vendored data that at least one pair (CatMage/FoxMage) genuinely
        # produces a DIFFERENT child depending on which parent is which
        # gender, so this must never collapse to a single result per pair.
        self._combinations_by_species_pair: dict[frozenset[str], list[BreedingCombination]] = {}
        for entry in self._breeding["Breeding"]:
            combo = BreedingCombination(
                parent1=entry["Parent1InternalName"],
                parent1_gender=entry["Parent1Gender"],
                parent2=entry["Parent2InternalName"],
                parent2_gender=entry["Parent2Gender"],
                child=entry["ChildInternalName"],
            )
            key = frozenset({combo.parent1, combo.parent2})
            self._combinations_by_species_pair.setdefault(key, []).append(combo)

    def get_species(self, internal_name: str) -> PalSpecies | None:
        """Exact-match lookup only -- see VENDOR_INFO.md's note on save
        CharacterID variants (e.g. '_otomo' suffixes) that don't resolve
        directly. Deliberately does not guess at fuzzy matches.
        """
        return self._species_by_id.get(internal_name)

    def all_species(self) -> tuple[PalSpecies, ...]:
        return tuple(self._species_by_id.values())

    def find_breeding_results(self, species_a: str, species_b: str) -> tuple[BreedingCombination, ...]:
        """Returns EVERY recorded combination for this unordered species
        pair. Usually exactly one. Can be more than one when the outcome is
        gender-dependent (verified real case: CatMage x FoxMage produces
        CatMage_Fire or FoxMage_Dark depending on which parent is which
        gender) -- callers must inspect parent1_gender/parent2_gender rather
        than assume a single answer.
        """
        return tuple(self._combinations_by_species_pair.get(frozenset({species_a, species_b}), ()))

    def get_breeding_mechanics_raw(self) -> dict:
        """DATAMINED/INFERRED, not independently verified by this project.
        See data/rules/ruleset.py. Do not treat as ground truth without
        cross-checking via this project's own differential-analysis method.
        """
        return self._db["BreedingMechanics"]

    def get_breeding_gender_probability_raw(self, species_id: str) -> dict | None:
        """DATAMINED/INFERRED, not independently verified."""
        return self._db["BreedingGenderProbability"].get(species_id)

    def get_min_breeding_steps_raw(self, species_id: str) -> dict | None:
        """Vendored source data ONLY -- NOT this project's authoritative
        pathfinding result. See module docstring.
        """
        return self._breeding["MinBreedingSteps"].get(species_id)
