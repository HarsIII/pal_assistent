# Changelog

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
