# Vendored dependency: palcalc species/breeding data

## What this is

Two unmodified data files copied verbatim from the `tylercamp/palcalc` project
(a Windows breeding-solver app): `db.json` (per-species static data) and
`breeding.json` (a fully precomputed parent-pair -> child breeding table,
plus a `MinBreedingSteps` table -- see caveats below on how we use, and
deliberately do NOT use, that field).

Nothing outside `data/breeding/` should import these files directly -- see
`data/breeding/breeding_database.py`, which is the only intended access
point (mirrors the `save/adapters/` isolation pattern used for the vendored
GVAS parser).

## Source

- Repo: https://github.com/tylercamp/palcalc
- Author: Tyler Camp
- Commit pinned: `c59712e24b839a0bedef16b06a1a0117e8741fe3` (default branch
  `main`; verified byte-identical to the `master` branch at the time of
  vendoring, so both branches were in sync at this commit)
- Commit date: 2026-08-02 (per GitHub's commit API, author date)
- Files vendored: `PalCalc.Model/db.json`, `PalCalc.Model/breeding.json`
- Vendored on: 2026-08-08
- License: MIT (verbatim text in `LICENSE.txt` next to this file, fetched
  from the same pinned commit's `LICENSE.txt`, copyright Tyler Camp, 2024)

## Checksums (of the exact files vendored here)

- `db.json`: `sha256:F9D68B04094A036C02836AF93896D3E6461D34A942EDD199DB9F4793F978F929`
- `breeding.json`: `sha256:E0F3A3EECA656FF506F4C1307397CAD1BF156680D8C90CA6250EA790F11B38BB`

Both hashes were computed on the files as downloaded directly from the
pinned commit's raw GitHub URL, matching the files stored in this directory
exactly. **These files must never be hand-edited** -- if a value needs
correcting, either wait for an upstream fix and re-vendor, or apply a
clearly-documented patch in `breeding_database.py` (never silently alter the
vendored source).

## Why this source, and confidence level

Source type: **DATAMINED**, not OFFICIAL -- Pocketpair has not published this
data. `db.json`'s companion generator (`PalCalc.GenDB`, in the same repo) is
documented to extract this data directly from the installed game's own
Unreal Engine asset files via CUE4Parse, rather than being manually
compiled from community observation. `db.json` carries an internal
`"Version": "v27"` stamp tying it to a specific game data revision.

Directly cross-checked (not merely trusted) against this project's own real
save data before vendoring: every `CharacterID` value pulled from a real
Pal in this project's save correctly resolved via `db.json`'s
`InternalName` field to the expected in-game display name --
`IceHorse` -> Frostallion, `MonochromeQueen` -> Solenne, `Umihebi` ->
Jormuntide, `Umihebi_Fire` -> Jormuntide Ignis, `JetDragon` -> Jetragon,
`ClownRabbit` -> Dupin, `BlackPuppy` -> Smokie, `DomeArmorDragon` -> Aegidron,
`WeaselDragon` -> Chillet. (`KingWhale_otomo` did not resolve directly --
the `_otomo` suffix is presumably a save-side variant/tamed-form marker not
present in `db.json`'s `InternalName` values; `breeding_database.py` should
handle this via suffix-stripping/fallback matching, not by assuming every
save `CharacterID` has a 1:1 exact-string match.)

## What we explicitly do NOT treat as authoritative from this source

- **`MinBreedingSteps`** (inside `breeding.json`): kept as vendored source
  data, but the project's own breeding-pathfinding solver (not yet built)
  will be independently implemented and tested. This field may be used
  later as a cross-check against our own solver's output, never as the
  solver's actual result.
- **`BreedingMechanics`** (inside `db.json`: `IVInheritanceWeights`,
  `PassiveInheritanceWeights`, `PassiveRandomWeights`): stored separately
  (see `breeding_database.py`'s `get_breeding_mechanics()`) and tagged
  DATAMINED/INFERRED in `data/rules/ruleset.py` until independently
  verified via this project's own differential-analysis methodology
  (the same approach used to verify Rank_HP/Attack/Defence/CraftSpeed).
- **`PartnerSkill`**: present as a field in `db.json` but was `null` for
  every species checked so far during vendoring verification -- not yet
  confirmed this field is reliably populated across the full species list.

## Consequences / what to watch

- This is a pinned snapshot, not a live dependency -- future Palworld
  updates (new species, rebalanced breeding power) will require re-syncing
  with a newer palcalc commit (or re-running their `PalCalc.GenDB`
  extractor, which needs a local Palworld install we don't currently have --
  see `save/adapters/vendor/palworld_save_tools/VENDOR_INFO.md` for the
  same caveat about this machine not having the game installed).
- MIT license: freely reusable, no copyleft obligations, consistent with
  this project's other MIT-licensed vendored dependency.
