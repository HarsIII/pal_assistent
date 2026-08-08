# Save Format

Everything in this document was established empirically against a real save
on the development machine (Steam, single-player/co-op, world ID
`07A8CBAE48FFC56464871C9F7A9FCA66`) during Phase 0, cross-checked where
possible against independent sources. See `data/rules/ruleset.py` for the
same facts in machine-readable form with confidence levels.

## File layout (Steam)

```
%LOCALAPPDATA%\Pal\Saved\SaveGames\
    UserOption.sav                      <- account-level, uncompressed GVAS
    <SteamID>\
        GlobalPalStorage.sav            <- account-level, Palbox storage
        <WorldID>\
            Level.sav                   <- the big one: Pals, players, bases, items, map objects
            LevelMeta.sav                <- world metadata (in-game day, timestamp, ...)
            LocalData.sav                <- world map UI state, boss flags, treasure points
            WorldOption.sav              <- difficulty/settings
            Players\<PlayerUID>.sav      <- per-player progress/records
            Players\<PlayerUID>_dps.sav  <- per-player "SaveParameterArray" (role UNKNOWN -- not
                                             yet investigated; parses fine, meaning undetermined)
            backup\local\<timestamp>\... <- rolling backups, same file layout
            backup\world\<timestamp>\... <- rolling backups, same file layout
```

Xbox/Game Pass and dedicated-server layouts: **UNKNOWN**, not investigated.
Do not assume this layout is universal.

## Wrapper header (compressed files)

Every file except `UserOption.sav` starts with a 12-byte header:

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | `uncompressed_len` (u32, little-endian) |
| 4 | 4 | `compressed_len` (u32, little-endian) |
| 8 | 3 | magic bytes |
| 11 | 1 | `save_type` |
| 12 | ... | compressed payload |

Magic bytes observed, VERIFIED:

- **`PlM`** -- Oodle-compressed. Every world/account file in this save uses
  this. Decompressed via the open-source `ooz` reimplementation of Oodle
  (PyPI package `pyooz`), which we verified byte-exact: decompressed length
  matches the header's `uncompressed_len` on every file tested.
- **`PlZ`** -- zlib-compressed (the older format; not present in this save,
  but the decompression path supports it since some tooling and older saves
  still use it). `save_type` 0x31 = single zlib pass, 0x32 = double.
- **`CNK`** -- a chunked variant with a further-nested header (community
  term: "Xbox container"). Not encountered in this save. Not implemented in
  `save/adapters/compression.py` beyond magic detection -- **UNKNOWN**,
  treat as unsupported until a real CNK file is available to test against.

`UserOption.sav` has **no wrapper header at all** -- it starts directly with
the `GVAS` magic. VERIFIED directly (first 4 bytes are literally `GVAS`, and
`int.from_bytes` of what would be the length fields doesn't correspond to any
sane size).

## GVAS header (after decompression)

Standard Unreal SaveGame header, VERIFIED via `GvasHeader.read`:

- `SaveGameFileVersion = 3`
- Engine version: **5.1.1**, branch `++UE5+Release-5.1`
- `save_game_class_name` identifies the specific save type (e.g.
  `Pal.PalLocalWorldSaveGame` for `Level.sav`)

## Why the official `palworld-save-tools` package doesn't work here

VERIFIED by direct reproduction (installed `palworld-save-tools==0.24.0` from
PyPI and ran it against this save):

- It has **no Oodle/PlM support at all**. `palsav.py`'s `MAGIC_BYTES` constant
  is hardcoded to `b"PlZ"`; a `PlM` file raises immediately.
- The package has not been updated since 2024-10-06 (v0.24.0, confirmed via
  GitHub's Releases API, not just the PyPI page).
- Even after bolting on Oodle decompression ourselves (calling `pyooz`
  directly, bypassing the library's own decompression step, then handing the
  raw GVAS bytes to its `GvasFile.read`), parsing **`Level.sav` still
  crashes**: several of its hardcoded raw-binary sub-decoders
  (`rawdata/base_camp.py`, `rawdata/character.py`,
  `rawdata/foliage_model_instance.py`, `rawdata/group.py`,
  `rawdata/map_model.py`) call `raise Exception("Warning: EOF not reached")`
  the moment there are trailing bytes they don't recognize -- which there
  are, because the game has added fields to these structures since the
  library's decoders were written.

This was cross-checked against the GitHub issue tracker (issues #138, #177,
#208), all still open, all describing the same failure mode against
different Palworld updates, none fixed upstream.

## What actually works: a pinned community fork

`KrisCris/palworld-save-tools` (used internally by the actively-maintained
`Palworld-Pal-Editor` project) patches exactly this failure mode -- its raw
decoders log-and-continue via `loguru` instead of raising -- and ships native
Oodle support (`compressor/oozlib.py`, which itself just wraps the same
`pyooz`/`ooz` bindings this project depends on directly).

We vendored a pinned snapshot (commit `82dc6ad06e6162b29c0ef7d321fed2a73609a4d6`,
MIT-licensed) into `save/adapters/vendor/palworld_save_tools/` -- see that
directory's `VENDOR_INFO.md` for the full reasoning, license, and what to do
when a future Palworld update breaks it again. **VERIFIED**: with this fork,
`Level.sav`, `GlobalPalStorage.sav`, `WorldOption.sav`, `LevelMeta.sav`,
`UserOption.sav`, and every `Players/*.sav` file in this save parse
completely.

### Known remaining gap: `LocalData.sav`

Still fails, with both the official package and the vendored fork:

```
Error decoding ascii string of length 184549376: b'...InstanceId...StructProperty...'
```

Root cause (VERIFIED by inspecting the parser's own debug output before the
crash): `.SaveData.Local_MaxFriendshipPalIds` is a `MapProperty` whose value
type isn't in the parser's known-types table. The parser logs `"Struct type
for .SaveData.Local_MaxFriendshipPalIds.Key not found, assuming Guid"` and
guesses -- and the guess is wrong, which desynchronizes the byte offset for
everything that follows, eventually reading a bogus multi-hundred-megabyte
string length from what's actually mid-structure binary data.

This is UNKNOWN, not guessed at: we do not know what `Local_MaxFriendshipPalIds`'
value type actually is. `LocalData.sav` holds world-map UI state, boss-defeat
flags, and treasure-map points -- not Pal/breeding data -- so this does not
block anything the project actually needs yet. Tracked as a known limitation
in `data/rules/ruleset.py` and asserted as still-open in
`tests/test_save_researcher_integration.py::test_local_data_sav_known_gap_is_still_open`
so we notice immediately if a future fork update fixes it.

## Pal/player field inventory (from `Level.sav`, `worldSaveData.CharacterSaveParameterMap`)

`CharacterSaveParameterMap` holds **both players and Pals** in the same map
(distinguished by an `IsPlayer` boolean field) -- VERIFIED: this save has
1351 entries total, of which 10 have `IsPlayer: True` and 1341 have a
`CharacterID` (species/character identifier).

Fields discovered (full inventory:
`reports/_generated/level_character_field_inventory.md`, not committed --
regenerate with `scripts/run_phase0.py`). Field *names* are VERIFIED (they
are exactly what's in the save); field *meaning* is INFERRED from the
vendored parser's own naming, which comes from community reverse-engineering,
not official documentation or our own independent confirmation:

| Field | Type | Likely meaning (INFERRED) |
|---|---|---|
| `CharacterID` | NameProperty | Species identifier |
| `Gender` | EnumProperty (`EPalGenderType`) | Sex |
| `Level`, `Exp` | ByteProperty / Int64Property | Level and experience |
| `Talent_HP`, `Talent_Shot`, `Talent_Defense` | ByteProperty | Almost certainly the in-game "Potential" / IV-like stats (0-100 range values observed) -- name-to-stat mapping not independently confirmed |
| `PassiveSkillList` | ArrayProperty[NameProperty] | Passive skills |
| `EquipWaza`, `MasteredWaza` | ArrayProperty[EnumProperty] | Active skills (equipped vs. all learned) |
| `Rank` | ByteProperty | Likely "condensation" star rank |
| `Rank_HP`, `Rank_Attack`, `Rank_Defence`, `Rank_CraftSpeed` | ByteProperty | Likely per-stat boosts from condensing |
| `IsRarePal` | BoolProperty | Candidate for "Alpha" -- **not confirmed**; could also mean shiny/rare color variant. UNKNOWN which. |
| `SlotId.ContainerId.ID` + `SlotId.SlotIndex` | StructProperty / IntProperty | Which container (party/base/Palbox) and slot the Pal occupies |
| `OwnerPlayerUId`, `OldOwnerPlayerUIds` | StructProperty (Guid) | Current and past owners |
| `FriendshipPoint`, `Friendship*Sec` | IntProperty | Bond/friendship tracking |
| `WorkSuitabilityOptionInfo` | StructProperty | Work-suitability preferences |
| `NickName`, `FilteredNickName` | StrProperty | Player-given nickname (raw and profanity-filtered) |
| `SkinName`, `SkinAppliedCharacterId` | NameProperty / Guid | Cosmetic skin |
| `HP.Value`, `ShieldHP.Value` | StructProperty(FixedPoint64) | Current HP / shield. **VERIFIED** (user cross-checked against in-game UI): `Hp.Value = displayed_HP * 1000` (e.g. 5244000 <-> displayed 5244). Same x1000 scaling for `ShieldHP.Value` is a reasonable but **unverified** extension (same struct type, not independently confirmed). |
| `UniqueNPCID` | NameProperty | Set on named/boss NPCs (observed value: a boss identifier matching names also seen in `LocalData.sav`'s boss-flag map) |

No per-instance "Partner Skill" field was observed -- consistent with the
project's own domain-model split (`PalSpecies.partner_skill` is
species-level static data, not saved per-instance).

## Pal/player instance identification (VERIFIED)

`CharacterSaveParameterMap`'s key is a raw `{PlayerUId, InstanceId, DebugName}`
struct. **`InstanceId` is the correct, verified-stable identifier for "this
exact individual Pal or player"** -- not `NickName` (usually absent, never
guaranteed unique) and not `CharacterID` (identifies the *species*; this save
alone has ~90 separate instances sharing the `Umihebi`/`Umihebi_Fire`
CharacterID family).

This was verified empirically, not assumed (`scripts/verify_instance_id_stability.py`),
against two real snapshots of this save taken 5 minutes apart around a real
condensation action:

- **Uniqueness within a save**: 0 collisions across 1303 entries (before) and
  1234 entries (after).
- **Stability across a save-to-save transition**: of 1217 entries present in
  both snapshots (matched by `InstanceId`), 0 had a mismatched `CharacterID`
  or `IsPlayer` value -- statistically conclusive at this sample size that
  `InstanceId` is not being reused/regenerated between saves.
- Confirmed to track a genuinely *mutating* entity, not a static one (e.g. one
  Pal's `Level` changed from 39 to 40 across the two snapshots while its
  `InstanceId` stayed fixed).
- Entry-count bookkeeping is internally consistent: 86 entries present only
  in "before" (consumed as condensation fodder) and 17 present only in
  "after" (net matches the observed 1303 -> 1234 total).

The full identification hierarchy this establishes -- and the reasoning for
never using nickname/species/level as a primary key -- is documented in
`save/inspector/pal_identity.py`, which all differential-analysis scripts now
use instead of duplicating this extraction logic ad hoc.

## Base camp (`worldSaveData.BaseCampSaveData`) structure

Parses completely via the vendored fork. Notable sub-structures: `WorkCollection`,
`WorkerDirector` (current battle/order type, spawn transform), and
`ModuleMap` (per-module data, including `passive_effects` with a `type` and
`work_hard_type` -- likely base facility passive-effect data, **UNKNOWN**
exact meaning of the effect `type` enum values, not yet cross-referenced).

## Locale note

Some default/template string values in this save are in Japanese (e.g. a
newly-created base's default name, and `GotStatusPointList[].StatusName`
values like `"最大HP"`). This appears to be default template text rather than
a mechanic -- noted so it isn't mistaken for a parsing bug later.

## Top-level structure counts (this save, for scale reference only)

| Structure | Count |
|---|---|
| `CharacterSaveParameterMap` (Pals + players) | 1351 |
| `ItemContainerSaveData` | 5671 |
| `BaseCampSaveData` (bases) | 4 |
| `GroupSaveDataMap` (guilds) | 9 |
| `MapObjectSaveData` | 7508 |
| `DynamicItemSaveData` | 374 |
| `GlobalPalStorage.sav` `SaveParameterArray` (boxed Pals) | 960 |

These are specific to this save and will differ for any other player -- they
exist here only to show the Save Researcher's output is real and the
pipeline scales to a save of this size (Level.sav decompresses to ~41.5 MB).
