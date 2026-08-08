# Vendored dependency: palworld_save_tools

## What this is

A vendored (copied, not pip-installed) snapshot of the `palworld_save_tools` Python
package, used here strictly as the GVAS property-tree parser inside
`save/adapters/gvas_adapter.py`. Nothing outside `save/adapters/` imports this
package directly (see ARCHITECTURE.md — the rest of the system must never depend
on the save format's internal representation).

## Source

- Origin repo: https://github.com/cheahjs/palworld-save-tools (original author: Jun Siang Cheah)
- Actual snapshot taken from a **fork**: https://github.com/KrisCris/palworld-save-tools
- Commit pinned: `82dc6ad06e6162b29c0ef7d321fed2a73609a4d6`
- Vendored on: 2026-08-07
- License: MIT (see `palworld_save_tools_LICENSE` next to this file; copyright Jun Siang Cheah)

## Why a fork instead of the official PyPI package

Verified directly against this project's own save files (not taken on faith from
documentation) — see `SAVE_FORMAT.md` at the project root for the full evidence trail:

- The official PyPI release (`palworld-save-tools` 0.24.0, last published 2024-10-06)
  has no Oodle/"PlM" support at all, and has not been updated since. It fails outright
  on this save's compression format.
- Several of its hardcoded raw-binary sub-decoders (`rawdata/base_camp.py`,
  `rawdata/character.py`, `rawdata/foliage_model_instance.py`, `rawdata/group.py`,
  `rawdata/map_model.py`, etc.) `raise Exception("Warning: EOF not reached")` the
  moment the game has added trailing fields they don't know about. This hard-crashes
  the ENTIRE file's parse, including `Level.sav` — the file that holds every Pal,
  player, and base in the save.
- The `KrisCris/palworld-save-tools` fork (actively updated; last commit as of
  vendoring was 3 days prior) patches these decoders to log-and-continue via
  `loguru` instead of raising, and ships native Oodle support through
  `compressor/oozlib.py` (which itself just wraps the open-source `pyooz` /
  `ooz` Python bindings — the same ones this project depends on directly).
- Empirically confirmed: this fork parses `Level.sav`, `GlobalPalStorage.sav`, and a
  `Players/*.sav` file from this save **completely**. `LocalData.sav` still has one
  known gap (see `SAVE_FORMAT.md`, `.SaveData.Local_MaxFriendshipPalIds` — an unknown
  map value type), tracked as UNKNOWN rather than guessed at.

## Consequences / what to watch

- This is a **pinned snapshot**, not a live dependency. Future Palworld updates may
  introduce fields this snapshot doesn't know about either (the same failure mode
  documented above). When that happens: re-check the fork for a newer commit, or
  patch the specific `rawdata/*.py` decoder ourselves following the same
  log-and-continue pattern — never silently guess at what new fields mean.
- We depend on the official PyPI `pyooz` package (by `zao`) directly, not
  `KrisCris/pyooz` (which this fork's own `pyproject.toml` actually references).
  We verified the official PyPI `pyooz` decompresses every file in this save
  byte-exact against the header-declared uncompressed length, so there was no need
  to take on an extra git-based dependency for it (this machine also has no `git`
  installed, which independently ruled out any git-based dependency).
- No modifications have been made to the vendored source itself. If we need to patch
  a decoder in the future, do it as a clearly-marked local diff, documented here.
