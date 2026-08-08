"""Tests for the vendored breeding database. Uses the REAL vendored data
(not synthetic fixtures) deliberately -- this module's job is entirely about
correctly interpreting a specific real dataset, so the tests should catch
real edge cases in that dataset (like the CatMage/FoxMage gender-dependent
result), not a simplified stand-in that wouldn't have caught them.
"""

import pytest

from data.breeding.breeding_database import BreedingDatabase


@pytest.fixture(scope="module")
def db():
    return BreedingDatabase()


# --- Internal-name mappings, cross-checked against real CharacterIDs seen
# --- in this project's own save (see data/rules/ruleset.py and
# --- data/breeding/vendor/palcalc/VENDOR_INFO.md for the same list).
@pytest.mark.parametrize(
    "internal_name,expected_display_name",
    [
        ("IceHorse", "Frostallion"),
        ("MonochromeQueen", "Solenne"),
        ("Umihebi", "Jormuntide"),
        ("Umihebi_Fire", "Jormuntide Ignis"),
        ("JetDragon", "Jetragon"),
        ("ClownRabbit", "Dupin"),
        ("BlackPuppy", "Smokie"),
        ("DomeArmorDragon", "Aegidron"),
        ("WeaselDragon", "Chillet"),
    ],
)
def test_known_save_character_ids_resolve_correctly(db, internal_name, expected_display_name):
    species = db.get_species(internal_name)
    assert species is not None, f"{internal_name} not found in vendored data"
    assert species.display_name == expected_display_name


def test_unresolvable_variant_suffix_returns_none_not_a_guess(db):
    """KingWhale_otomo (a real CharacterID from this project's save) does not
    resolve directly -- the database must say so plainly (None) rather than
    silently guessing via a stripped suffix.
    """
    assert db.get_species("KingWhale_otomo") is None
    assert db.get_species("KingWhale") is not None


def test_unknown_species_returns_none(db):
    assert db.get_species("ThisSpeciesDoesNotExist") is None


def test_species_has_base_stats_and_breeding_power(db):
    frostallion = db.get_species("IceHorse")
    assert frostallion.base_stats is not None
    assert frostallion.base_stats.hp > 0
    assert frostallion.breeding_power is not None


def test_partner_skill_is_known_gap_not_silently_wrong(db):
    """Documented gap: PartnerSkill is null for every species in this
    vendored snapshot. This test exists so that if palcalc ever populates
    it, we notice and can update PalSpecies mapping/docs accordingly.
    """
    frostallion = db.get_species("IceHorse")
    assert frostallion.partner_skill_id is None


# --- Breeding combination lookups: order independence + the real
# --- gender-dependent exception discovered during vendoring.
def test_same_species_pair(db):
    results = db.find_breeding_results("Alpaca", "Alpaca")
    assert len(results) == 1
    assert results[0].child == "Alpaca"


def test_breeding_lookup_is_order_independent(db):
    forward = db.find_breeding_results("BerryGoat", "Monkey_Fire")
    reverse = db.find_breeding_results("Monkey_Fire", "BerryGoat")
    assert forward == reverse
    assert len(forward) == 1
    assert forward[0].child == "Alpaca"


def test_nonexistent_pair_returns_empty(db):
    assert db.find_breeding_results("Alpaca", "ThisSpeciesDoesNotExist") == ()


def test_gender_dependent_pair_returns_both_outcomes(db):
    """The one verified real exception: CatMage x FoxMage produces a
    DIFFERENT child depending on which parent is male vs female. A naive
    order/gender-agnostic lookup would silently collapse this to one
    result -- this must not happen.
    """
    results = db.find_breeding_results("CatMage", "FoxMage")
    assert len(results) == 2
    children = {r.child for r in results}
    assert children == {"CatMage_Fire", "FoxMage_Dark"}

    by_gender_pair = {(r.parent1_gender, r.parent2_gender): r.child for r in results}
    assert by_gender_pair[("FEMALE", "MALE")] == "CatMage_Fire"
    assert by_gender_pair[("MALE", "FEMALE")] == "FoxMage_Dark"


# --- Raw, explicitly-unverified accessors: exist and return sane shapes,
# --- without asserting their VALUES are correct (they're not verified).
def test_breeding_mechanics_raw_has_expected_shape(db):
    mechanics = db.get_breeding_mechanics_raw()
    assert "IVInheritanceWeights" in mechanics
    assert "PassiveInheritanceWeights" in mechanics
    assert "PassiveRandomWeights" in mechanics


def test_min_breeding_steps_raw_is_source_data_not_solver_output(db):
    steps = db.get_min_breeding_steps_raw("BadCatgirl")
    assert steps is not None
    assert steps["BadCatgirl"] == 0  # distance to self is trivially 0


def test_breeding_gender_probability_raw(db):
    prob = db.get_breeding_gender_probability_raw("BrownRabbit")
    assert prob == {"MALE": 0.5, "FEMALE": 0.5}
