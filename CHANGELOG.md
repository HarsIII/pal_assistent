# Changelog

## Domain model started: PalInstance (2026-08-08)

- Built `domain/pal/pal_instance.py` (`PalInstance`), `domain/pal/pal_genotype.py`
  (`PalGenotype` + `from_pal_instance`), and `domain/pal/pal_species.py`
  (schema only, no data yet -- species-level static data needs an external
  source, not a save file).
- Built `save/normalization/pal_mapper.py`, the first NORMALIZATION-layer
  code: maps a raw `CharacterSaveParameterMap` entry to a `PalInstance`,
  applying the verified HP scaling and keeping condensation/Soul fields
  properly independent per the Rank_* investigation.
- 14 new tests (8 synthetic mapper tests, 6 integration tests against the
  real save mapping every current Pal/player entry and checking structural
  invariants). 47 total tests passing.
- Every field's confidence (VERIFIED/INFERRED/UNKNOWN) is documented directly
  in `PalInstance`'s docstring, cross-referenced to `data/rules/ruleset.py`.
- Next decision point: sourcing real `PalSpecies` data (base stats, breeding
  rank, partner skills) -- cannot come from a save file, needs the same
  research-before-committing treatment as the save-parser library decision.

## Rank_* field investigation resolved (2026-08-08)

- Investigated `Rank_HP`/`Rank_Attack`/`Rank_Defence`/`Rank_CraftSpeed` across
  the whole save (not just the two controlled condensation tests, which both
  showed zero change in these fields). Found no separate Soul-tracking field
  anywhere; scanned all 22 Rank-5 Pals and found species/boss-tier and
  Rank-5-alone both insufficient to explain presence.
- User confirmed `ClownRabbit`/"Dupina"'s fields correspond to Pal Soul
  investment, independent of its (also player-driven) condensation.
- Model updated: `Rank` = condensation/star progression; `Rank_HP/Attack/
  Defence/CraftSpeed` = Pal Soul investment per stat. Modeled as independent
  systems. Whether the user's Frostallion (`BOSS_IceHorse`, Medal Merchant
  condensed) was *also* Soul-invested remains explicitly unresolved --
  deliberately not inferred from its field values (would be circular).

## Post-Phase-0 hypothesis verification (2026-08-08)

- git installed and repo initialized; Phase 0 committed.
- Verified (not assumed) that `InstanceId` is a stable, unique per-Pal/player
  identifier, both within a single save and across a save-to-save
  transition, using two real before/after snapshots around a live
  condensation action. See `save/inspector/pal_identity.py` for the
  resulting identification hierarchy and `SAVE_FORMAT.md` for the evidence.
- Found and fixed a bug in an early ad-hoc diffing script that mis-extracted
  the map key (assumed a `{"value": ...}` wrapper that isn't there for this
  particular key shape), which had collapsed 1303/1234 entries into a single
  bucket. Refactored all differential scripts to share `pal_identity.py`
  instead of duplicating extraction logic, specifically to avoid this class
  of bug recurring.
- Confirmed condensing a Pal sets its `Rank` field and increases `Hp.Value`
  (via real before/after diff). Did NOT yet confirm which Pal instance the
  user intended to test -- CharacterID-substring matching was ambiguous
  (~90 Umihebi-family instances in this save) and matched the wrong one on
  the first attempt. A follow-up test with a unique marker nickname is in
  progress. `Rank_HP`/`Rank_Attack`/`Rank_Defence`/`Rank_CraftSpeed` remain
  unconfirmed either way.
- `IsRarePal` (Alpha hypothesis) deliberately left as UNKNOWN/open per user
  direction, pending correlation against Pals independently known to be (or
  not be) Alpha.
- Built `save/inspector/pal_identity.py`'s InstanceId-based identification
  hierarchy and used it for a clean, unambiguous controlled test
  (TEST_CONDENSE_002): one condensation (2 stars -> 3 stars) produced
  `Rank: 3 -> 4` and `Hp.Value: 5244000 -> 5483000`, with Talents, passives,
  level, and skills all unchanged, and no fields added or removed.
  `Rank_HP/Attack/Defence/CraftSpeed` remained absent for a second
  consecutive test.
- VERIFIED (user cross-checked against in-game UI): `Hp.Value = displayed_HP
  * 1000`.

## Phase 0 -- Save Researcher (2026-08-07)

- Investigated this machine's real Palworld save; discovered it uses Oodle
  compression (`PlM` magic) rather than the zlib (`PlZ`) format most existing
  tooling assumes.
- Confirmed the official `palworld-save-tools` PyPI package is unmaintained
  since 2024-10-06 and cannot parse this save (no Oodle support; several raw
  decoders hard-crash on fields added since the decoders were written).
- Vendored a pinned, actively-maintained community fork
  (`KrisCris/palworld-save-tools` @ `82dc6ad`) that fixes both problems;
  isolated it behind `save/adapters/`.
- Built the Save Researcher (`save/inspector/`): a data-driven walker that
  discovers every field in a parsed save without assuming a schema, plus
  safe read-only save discovery/copying (`save/parser/save_bundle.py`).
- Built a minimal Differential Save Analyzer (`save/differential/differ.py`)
  and demonstrated it against two real backup timestamps.
- Verified end-to-end against the real save: `Level.sav`, `LevelMeta.sav`,
  `WorldOption.sav`, `GlobalPalStorage.sav`, `UserOption.sav`, and 11
  `Players/*.sav` files all parse completely. `LocalData.sav` has one
  documented, tracked gap (see `SAVE_FORMAT.md`).
- 28 tests passing (22 synthetic/deterministic, 6 live integration tests
  against the real save, auto-skipped when no save is present).
- Wrote `README.md`, `ARCHITECTURE.md`, `SAVE_FORMAT.md`, and
  `reports/SAVE_RESEARCH_REPORT.md`.

Not started: domain model, game database, breeding engine, modifier engine,
simulation, breeding graph, optimizer, recommendation engine, GUI,
progress/history, advanced simulation, optional ML.
