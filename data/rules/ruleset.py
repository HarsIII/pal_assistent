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
    Fact(
        statement=(
            "worldSaveData.CharacterSaveParameterMap's key is a raw "
            "{PlayerUId, InstanceId, DebugName} struct (not itself wrapped in "
            "a further property-node level). InstanceId is a valid, stable "
            "per-entity identifier: (1) unique within a single save -- "
            "verified zero collisions across 1303 and 1234 entries in two "
            "real snapshots; (2) stable across a save-to-save transition for "
            "any entry that persists -- verified zero CharacterID/IsPlayer "
            "mismatches across 1217 entries common to both snapshots, and "
            "confirmed to track a genuinely mutating entity (e.g. a Pal's "
            "own Level field changing while its InstanceId stayed fixed). "
            "NickName is NOT a safe identifier: usually absent, and never "
            "guaranteed unique when present. CharacterID identifies the "
            "species, not an individual -- this save alone has ~90 separate "
            "instances sharing the CharacterID family 'Umihebi'/'Umihebi_Fire'. "
            "See save/inspector/pal_identity.py for the full identification "
            "hierarchy this informs."
        ),
        confidence=Confidence.VERIFIED,
        source_type=SourceType.SAVE_OBSERVED,
        source=(
            "scripts/verify_instance_id_stability.py run against two real "
            "Level.sav snapshots of this save (before/after a Pal "
            "condensation), 2026-08-08"
        ),
        date_recorded="2026-08-08",
    ),
    Fact(
        statement=(
            "Condensing a Pal (combining duplicates to raise its rank) sets "
            "its Rank field (was absent/None before any condensing) and "
            "increases Hp.Value. Confirmed via before/after diff of a real "
            "condensation action, matched by InstanceId. NOT yet confirmed: "
            "which specific Pal instance the user intended to test -- an "
            "initial attempt to identify it by CharacterID substring ('contains "
            "Jormuntide') was ambiguous (this save has ~90 Umihebi-family "
            "instances) and matched the wrong one. A follow-up test using a "
            "unique marker nickname is in progress to confirm this "
            "unambiguously and to test the Rank_HP/Rank_Attack/Rank_Defence/"
            "Rank_CraftSpeed per-stat-boost hypothesis (no change was observed "
            "in those four fields in this first attempt, which could mean "
            "no random proc succeeded, or that they are unrelated to "
            "condensing -- inconclusive either way from a single data point)."
        ),
        confidence=Confidence.INFERRED,
        source_type=SourceType.SAVE_OBSERVED,
        source="scripts/find_rank_changes.py, before_condense/after_condense snapshots, 2026-08-08",
        date_recorded="2026-08-08",
    ),
    Fact(
        statement=(
            "Hp.Value (the Int64Property under the FixedPoint64 'Hp' struct) is "
            "displayed_HP * 1000. Confirmed by the user directly cross-referencing "
            "this save's stored values against the in-game UI on a controlled test "
            "Pal (TEST_CONDENSE_002 / InstanceId=ad09af1a-4c9c-c977-fea2-6d8ab37bb295): "
            "5244000 <-> displayed 5244 (before condensing), 5483000 <-> displayed "
            "5483 (after). NOT independently verified for ShieldHP.Value, which "
            "uses the same FixedPoint64 struct type -- the same x1000 scaling is a "
            "reasonable but UNVERIFIED extension for that field."
        ),
        confidence=Confidence.VERIFIED,
        source_type=SourceType.USER_DEFINED,
        source="User cross-checked save values against in-game UI display, 2026-08-08",
        date_recorded="2026-08-08",
    ),
    Fact(
        statement=(
            "Controlled test #2 (TEST_CONDENSE_002, CharacterID=BOSS_MonochromeQueen, "
            "InstanceId=ad09af1a-4c9c-c977-fea2-6d8ab37bb295, unambiguously tracked "
            "via InstanceId, unlike test #1): one condensation from visual 2 stars to "
            "3 stars produced Rank 3 -> 4 and Hp.Value 5244000 -> 5483000. "
            "Talent_HP/Talent_Shot/Talent_Defense, PassiveSkillList, EquipWaza/"
            "MasteredWaza, Level, and Exp were all unchanged. Rank_HP/Rank_Attack/"
            "Rank_Defence/Rank_CraftSpeed remained entirely absent (2nd consecutive "
            "condensation test with no per-stat Rank_* field appearing -- still not "
            "conclusive proof they're unrelated to condensing, but two consistent "
            "null results is meaningful accumulating evidence). No fields were "
            "added or removed by condensing; only existing field values changed. "
            "This is now 2 consistent data points for the hypothesis "
            "save_rank = visual_stars + 1 (test #1: uncondensed -> Rank 5 at 4 "
            "stars; test #2: Rank 3 -> 4 for 2 stars -> 3 stars). Per explicit user "
            "instruction, this mapping stays INFERRED, not promoted to VERIFIED, "
            "until further confirmed."
        ),
        confidence=Confidence.INFERRED,
        source_type=SourceType.SAVE_OBSERVED,
        source="scripts/diff_specific_pal.py --instance-id, before_condense2/after_condense2 snapshots, 2026-08-08",
        date_recorded="2026-08-08",
    ),
    Fact(
        statement=(
            "Rank_HP, Rank_Attack, Rank_Defence, and Rank_CraftSpeed represent "
            "Pal Soul investment (a progression system independent of Rank -- "
            "condensation/star level), NOT a condensation byproduct. Field-by-field: "
            "Rank_HP = HP souls invested, Rank_Attack = Attack souls, Rank_Defence = "
            "Defense souls, Rank_CraftSpeed = Work Speed souls. Values observed "
            "0-20 -- consistent with Palworld's known 20-souls-per-stat cap. "
            "Evidence: (1) a full search of every property path and leaf string "
            "value in Level.sav found no separate 'souls invested' counter "
            "anywhere -- these fields are the only candidate location; (2) "
            "ClownRabbit ('Dupina', InstanceId=8e4b29b7-4028-4256-e563-30bd53d4c8db), "
            "an ordinary wild-caught Pal with no special/boss status, has all four "
            "fields at 20, and the user confirmed this corresponds exactly to Pal "
            "Soul investment they personally made -- NOT to condensation (Dupina's "
            "condensation to Rank 5 is a separate, independently-made investment); "
            "(3) among 22 Rank-5 Pals in this save, only 6 have any Rank_* field, "
            "including a stark within-species-tier split (5 of 9 BOSS_-prefixed "
            "Rank-5 Pals have it, 4 don't -- e.g. BOSS_BlackPuppy is Rank 5 with a "
            "'Rare' passive and zero Rank_* fields), ruling out species/boss-tier "
            "and Rank-5-alone as sufficient explanations; (4) two Pals have "
            "Rank_Attack present while Rank is None (never condensed), which is "
            "only consistent with an independent progression system. "
            "UNRESOLVED: whether BOSS_IceHorse (the user's Frostallion, Medal "
            "Merchant/Dog Coin condensed to Rank 5, Rank_HP=Rank_Attack=Rank_Defence=20) "
            "was ALSO separately given Pal Souls. The user has explicitly declined "
            "to infer this from the field values themselves (doing so would be "
            "circular -- the fields being at 20 cannot both be the evidence for "
            "and the fact being tested). This must be confirmed independently "
            "(the user's own memory/records), not derived from the save."
        ),
        confidence=Confidence.INFERRED,
        source_type=SourceType.SAVE_OBSERVED,
        source=(
            "scripts/investigate_rank_stat_fields.py, scripts/list_max_rank_pals.py, "
            "search for a separate soul-tracking field (none found), user confirmation "
            "of Dupina's Soul-investment history, 2026-08-08"
        ),
        date_recorded="2026-08-08",
    ),
    Fact(
        statement=(
            "Rank (condensation/star progression) and Rank_HP/Attack/Defence/"
            "CraftSpeed (Pal Soul investment) are modeled as INDEPENDENT "
            "progression systems in the domain model -- a Pal can have either, "
            "both, or neither, and one cannot be inferred from the other. This "
            "is a modeling decision, to be revised if future evidence shows a "
            "real dependency between the two systems."
        ),
        confidence=Confidence.INFERRED,
        source_type=SourceType.SAVE_OBSERVED,
        source="Synthesis of the Rank_* investigation, 2026-08-08",
        date_recorded="2026-08-08",
    ),
]
