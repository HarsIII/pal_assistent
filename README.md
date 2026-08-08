# Palworld Breeding Assistant

Local, read-only analysis and (eventually) breeding-optimization assistant for
Palworld. No external AI APIs; everything runs on your machine.

**Status: Phase 0 (Save Researcher) complete.** See
`reports/SAVE_RESEARCH_REPORT.md` for the full findings, and
`SAVE_FORMAT.md` for the technical detail behind them. Nothing beyond
save-file research and inspection has been built yet -- there is no domain
model, breeding engine, optimizer, or GUI. That is intentional (see
`ARCHITECTURE.md` and the phase plan at the bottom of this file).

## What exists right now

- `save/adapters/` -- decompression (zlib + Oodle) and GVAS property-tree
  parsing, isolated behind a small API so nothing else in the project needs
  to know the save format's internals.
- `save/parser/save_bundle.py` -- locates a real save on disk and makes
  safe, read-only working copies (the project never opens an original `.sav`
  file for writing).
- `save/inspector/` -- the Save Researcher: walks a parsed save and reports
  every field it finds, tagged by shape/type, without assuming a fixed
  schema.
- `save/differential/differ.py` -- diffs two parsed saves (e.g. the same
  world at two points in time) by path, for reverse-engineering unknown
  fields.
- `save/inspector/pal_identity.py` -- the identification hierarchy for
  individual Pals/players (InstanceId, verified stable, over nickname/species).
- `save/normalization/pal_mapper.py` -- maps raw save entries to the domain
  model.
- `domain/pal/` -- `PalInstance` (populated from real saves) and
  `PalGenotype` (a narrow view for the future breeding engine) exist.
  `PalSpecies` is a schema only -- no data source has been chosen yet.
- `data/rules/ruleset.py` -- a small, versioned fact registry (see
  "Principles" below).

## Setup

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## Running Phase 0 against your own save

```powershell
.venv\Scripts\python.exe scripts\run_phase0.py
```

This looks for a save under the default Steam location
(`%LOCALAPPDATA%\Pal\Saved\SaveGames`), copies it to a temp working
directory, and writes structural findings to `reports\_generated\` (not
committed -- see `.gitignore`; those files can contain snippets of your real
save data such as nicknames).

## Tests

```powershell
.venv\Scripts\python.exe -m pytest tests
```

Most tests are synthetic/deterministic. `test_save_researcher_integration.py`
additionally runs against your real save if one is found on this machine,
and is skipped otherwise (there is no bundled save fixture -- we don't commit
personal save data).

## Principles this project holds itself to

- **No inventing mechanics.** Every non-obvious fact is recorded in
  `data/rules/ruleset.py` with a confidence level: `VERIFIED` (we confirmed
  it ourselves against real data), `INFERRED` (taken from a community
  decoder's naming, not independently confirmed), `UNKNOWN` (explicitly not
  known), or `USER_DEFINED`.
- **Read-only.** The MVP never writes to a `.sav` file. Ever.
- **Modular.** Nothing outside `save/adapters/` knows this is Unreal Engine
  GVAS underneath, or which third-party library parses it.
- **Data-driven over hardcoded.** The Save Researcher discovers fields by
  walking the actual parsed structure rather than assuming a schema.

## Phase plan

Only Phase 0 is done. The remaining phases (domain model, game database,
breeding engine, modifier engine, simulation, breeding graph, optimizer,
recommendation engine, GUI, progress/history, advanced simulation, optional
ML) are deliberately not started -- each phase should be implemented, tested,
and documented before the next begins.
