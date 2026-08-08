# Architecture

## Pipeline (target shape; first four boxes exist today)

```
SAVE FILE
    |
SAVE PARSER        <- save/adapters/, save/parser/           (EXISTS)
    |
RAW SAVE MODEL      (a plain dict: header/properties/trailer -- what
    |                save/adapters/gvas_adapter.py returns)
NORMALIZATION       <- save/normalization/pal_mapper.py       (EXISTS, Pal/player only so far)
    |
DOMAIN MODEL        <- domain/pal/ (PalInstance, PalGenotype exist;
    |                  PalSpecies is a schema only, no data source yet)
GAME RULES          <- data/rules/ has the fact registry; data/breeding/
    |                  now has vendored species + breeding-combination data
SIMULATION          <- not started (engine/)
    |
OPTIMIZATION        <- not started (optimizer/)
    |
RECOMMENDATION      <- not started (assistant/)
    |
GUI                 <- not started
```

## Why the Save Parser is isolated behind `save/adapters/`

Two things can change independently of the rest of this project:

1. **Which library decodes GVAS bytes.** Right now that's a vendored,
   pinned snapshot of a community fork (see
   `save/adapters/vendor/palworld_save_tools/VENDOR_INFO.md` for exactly
   why, and what it fixes relative to the official package). Palworld
   updates may eventually outpace this snapshot too -- when that happens, the
   fix happens inside `save/adapters/`, and nothing above it should need to
   change.
2. **The save format itself.** Compression scheme, property shapes, new
   game-specific raw structs -- all of this is Unreal/Palworld trivia that
   only `save/adapters/gvas_adapter.py` and `save/adapters/compression.py`
   are allowed to know about. Everything above this layer works with a plain
   Python dict.

## Current modules

| Module | Responsibility |
|---|---|
| `save/adapters/compression.py` | Detects PlZ (zlib) / PlM (Oodle) / uncompressed GVAS; decompresses. Read-only: no compress/write path exposed. |
| `save/adapters/gvas_adapter.py` | Parses decompressed bytes into a plain dict via the vendored parser. |
| `save/adapters/vendor/palworld_save_tools/` | Vendored third-party GVAS parser (MIT). See its `VENDOR_INFO.md`. |
| `save/parser/save_bundle.py` | Finds a save on disk; makes safe read-only copies before anything touches the files. |
| `save/inspector/schema_walker.py` | Generic, data-driven walker that discovers every field path in a parsed save without assuming a schema. |
| `save/inspector/save_researcher.py` | Orchestrates: locate -> copy -> decompress -> parse -> walk -> report, per file in a save bundle. |
| `save/inspector/report_writer.py` | Renders SchemaWalker/SaveResearchReport data as markdown tables. |
| `save/differential/differ.py` | Path-level diff between two parsed saves (dev/research tool for reverse-engineering unknown fields). |
| `save/inspector/pal_identity.py` | Identification hierarchy for CharacterSaveParameterMap entries: InstanceId (verified stable) > nickname (optional, not unique) > CharacterID (species, not identity). See its docstring for the full evidence. |
| `save/normalization/pal_mapper.py` | Maps one raw CharacterSaveParameterMap entry (via a `PalEntryRef`) to a `domain.pal.pal_instance.PalInstance`. The only place that translates between raw property shapes and the domain model. |
| `domain/pal/pal_instance.py` | A single Pal/player as it exists in a save. Every field's confidence (VERIFIED/INFERRED/UNKNOWN) is documented in its module docstring. |
| `domain/pal/pal_genotype.py` | Narrow "parent-facing view" of a `PalInstance` for the future breeding engine. Does NOT claim these fields are what Palworld actually inherits -- that's unverified, pending breeding-engine-phase differential testing. |
| `domain/pal/pal_species.py` | Static per-species data (base stats, partner skill, breeding rank, etc.) -- **schema only, no data populated**. This cannot come from a save file; it needs an external, citable source, not yet chosen. |
| `data/rules/ruleset.py` | Versioned fact registry: statement, confidence (VERIFIED/INFERRED/UNKNOWN/USER_DEFINED), source, date. |
| `data/breeding/vendor/palcalc/` | Vendored species + breeding-combination data (MIT). See its `VENDOR_INFO.md`. |
| `data/breeding/breeding_database.py` | The only intended access point for the vendored breeding data -- species lookup, breeding-pair lookup (order-independent, gender-aware), and clearly-separated "raw, unverified" accessors for inheritance weights and the vendor's own pathfinding table. |
| `config/settings.py` | Paths (project root, default save location, safe workdir under the OS temp directory -- never inside the repo). |

## Not yet built (by design -- see README's phase plan)

`engine/`, `optimizer/`, `assistant/`, `database/`, `gui/` do not exist yet.
`domain.pal.PalSpecies` now gets real data via `BreedingDatabase`, but several
fields remain genuinely unpopulated because the vendored source doesn't have
them either (`partner_skill_id`, `elements`, `active_skill_pool`) -- these are
documented gaps, not bugs, and need a different/additional data source later
if they turn out to matter. Breeding pathfinding (the actual solver, as
opposed to the vendored `MinBreedingSteps` cross-check table) is the next
piece of engine/ work.

## Save safety

`save/parser/save_bundle.copy_bundle_to_workdir` is the only place original
save files are opened, and it only ever reads them (`shutil.copy2`). Every
other module operates on the copies. There is currently no code path capable
of writing a `.sav` file at all.
