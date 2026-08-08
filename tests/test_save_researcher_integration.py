"""Integration test against this machine's real save.

Skipped entirely if no Palworld save is present (e.g. CI, a different
machine) -- there is no bundled save fixture in this repo by design (project
rule: never commit a player's personal save data).

Reads the real save directly (read-only) only to make a safe copy; never
opens it for writing. See save/parser/save_bundle.py.
"""

from __future__ import annotations

import pytest

from config.settings import DEFAULT_STEAM_SAVE_ROOT, DEFAULT_WORKDIR
from save.parser.save_bundle import (
    find_world_dirs,
    discover_save_bundle,
    copy_bundle_to_workdir,
)
from save.inspector.save_researcher import run_save_researcher

pytestmark = pytest.mark.skipif(
    not find_world_dirs(DEFAULT_STEAM_SAVE_ROOT),
    reason="No real Palworld save found on this machine",
)


@pytest.fixture(scope="module")
def report():
    world_dir = find_world_dirs(DEFAULT_STEAM_SAVE_ROOT)[0]
    bundle = discover_save_bundle(world_dir)
    safe_bundle = copy_bundle_to_workdir(bundle, DEFAULT_WORKDIR / "pytest_run")
    return run_save_researcher(safe_bundle)


def _result_for(report, role: str):
    return next(r for r in report.file_results if r.role == role)


def test_level_sav_decompresses_and_parses(report):
    r = _result_for(report, "Level.sav")
    assert r.decompression_ok
    assert r.parse_ok, r.parse_error


def test_level_sav_uses_oodle_compression(report):
    from save.adapters.compression import SaveCompressionFormat

    r = _result_for(report, "Level.sav")
    assert r.detected_format is SaveCompressionFormat.PLM_OODLE


def test_user_option_sav_is_uncompressed(report):
    from save.adapters.compression import SaveCompressionFormat

    r = _result_for(report, "UserOption.sav")
    assert r.detected_format is SaveCompressionFormat.UNCOMPRESSED_GVAS
    assert r.parse_ok


def test_character_save_parameter_map_is_nonempty(report):
    r = _result_for(report, "Level.sav")
    count = r.top_level_structure_counts.get("worldSaveData.CharacterSaveParameterMap", 0)
    assert count > 0


def test_engine_version_is_recorded(report):
    r = _result_for(report, "Level.sav")
    assert r.engine_version is not None and "5.1" in r.engine_version


def test_local_data_sav_known_gap_is_still_open(report):
    """Documents a known, tracked limitation (see SAVE_FORMAT.md) rather than
    hiding it. If this starts passing, the vendored parser has improved --
    update SAVE_FORMAT.md and data/rules/ruleset.py, then delete this assertion.
    """
    r = _result_for(report, "LocalData.sav")
    assert r.decompression_ok
    assert not r.parse_ok, "LocalData.sav now parses -- update docs, this test's assumption is stale"
