# Architecture

## Pipeline (target shape; only the first two boxes exist today)

```
SAVE FILE
    |
SAVE PARSER        <- save/adapters/, save/parser/     (EXISTS)
    |
RAW SAVE MODEL      (a plain dict: header/properties/trailer -- what
    |                save/adapters/gvas_adapter.py returns)
NORMALIZATION       <- not started
    |
DOMAIN MODEL        <- not started (domain/)
    |
GAME RULES          <- not started (data/rules/ has only the Phase 0
    |                  fact registry so far, not gameplay rules)
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
| `data/rules/ruleset.py` | Versioned fact registry: statement, confidence (VERIFIED/INFERRED/UNKNOWN/USER_DEFINED), source, date. |
| `config/settings.py` | Paths (project root, default save location, safe workdir under the OS temp directory -- never inside the repo). |

## Not yet built (by design -- see README's phase plan)

`domain/`, `engine/`, `optimizer/`, `assistant/`, `database/`, `gui/` do not
exist yet. Building them before the save format is understood and verified
would mean designing a domain model against guessed data shapes -- exactly
what this project's own principles rule out.

## Save safety

`save/parser/save_bundle.copy_bundle_to_workdir` is the only place original
save files are opened, and it only ever reads them (`shutil.copy2`). Every
other module operates on the copies. There is currently no code path capable
of writing a `.sav` file at all.
