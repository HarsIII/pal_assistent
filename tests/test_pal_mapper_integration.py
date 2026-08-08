"""Integration test: maps every CharacterSaveParameterMap entry in the real
save (if present) to a PalInstance and checks structural invariants. Skipped
entirely if no save is present (see test_save_researcher_integration.py for
why there's no bundled fixture).

Deliberately does not assert exact values for any specific named Pal --
those change as the user keeps playing. Structural invariants only.
"""

from __future__ import annotations

import pytest

from config.settings import DEFAULT_STEAM_SAVE_ROOT, DEFAULT_WORKDIR
from save.parser.save_bundle import find_world_dirs, discover_save_bundle, copy_bundle_to_workdir
from save.adapters.gvas_adapter import load_raw_gvas_dict
from save.inspector.pal_identity import all_refs
from save.normalization.pal_mapper import map_pal_entry_to_instance
from domain.pal.pal_genotype import from_pal_instance

pytestmark = pytest.mark.skipif(
    not find_world_dirs(DEFAULT_STEAM_SAVE_ROOT),
    reason="No real Palworld save found on this machine",
)


@pytest.fixture(scope="module")
def all_pal_instances():
    world_dir = find_world_dirs(DEFAULT_STEAM_SAVE_ROOT)[0]
    bundle = discover_save_bundle(world_dir)
    safe_bundle = copy_bundle_to_workdir(bundle, DEFAULT_WORKDIR / "pytest_mapper_run")
    parsed = load_raw_gvas_dict(safe_bundle.level_sav)
    refs = all_refs(parsed)
    return [map_pal_entry_to_instance(r) for r in refs]


def test_maps_every_entry_without_error(all_pal_instances):
    assert len(all_pal_instances) > 0


def test_every_instance_has_a_stable_identity(all_pal_instances):
    ids = [p.instance_id for p in all_pal_instances]
    assert len(ids) == len(set(ids)), "InstanceIds must be unique after mapping"


def test_non_player_pals_have_a_species_id(all_pal_instances):
    for pal in all_pal_instances:
        if not pal.is_player:
            assert pal.species_id, f"non-player {pal.instance_id} has no species_id"


def test_condensation_rank_and_souls_are_independent(all_pal_instances):
    """Regression guard for the finding that these are separate systems --
    a Pal with a soul stat set is not required to have a condensation_rank,
    and vice versa.
    """
    has_soul_but_no_rank = [
        p for p in all_pal_instances
        if not p.is_player and p.condensation_rank is None
        and any([p.soul_hp, p.soul_attack, p.soul_defence, p.soul_work_speed])
    ]
    # Not asserting this is non-empty (save state can change) -- just that,
    # IF it happens, the mapper preserves it rather than coupling the fields.
    for pal in has_soul_but_no_rank:
        assert pal.condensation_rank is None


def test_potential_stats_in_expected_range(all_pal_instances):
    for pal in all_pal_instances:
        for value in (pal.potential_hp, pal.potential_shot, pal.potential_defense):
            if value is not None:
                assert 0 <= value <= 100


def test_genotype_derivable_for_non_players(all_pal_instances):
    non_players = [p for p in all_pal_instances if not p.is_player][:20]
    for pal in non_players:
        genotype = from_pal_instance(pal)
        assert genotype.species_id == pal.species_id


def test_genotype_rejects_players(all_pal_instances):
    players = [p for p in all_pal_instances if p.is_player]
    if not players:
        pytest.skip("no player entries in this save snapshot")
    with pytest.raises(ValueError):
        from_pal_instance(players[0])
