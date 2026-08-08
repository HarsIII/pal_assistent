"""Locates a Palworld save on disk and produces safe, read-only working copies.

Project rule ("Save Safety"): the program must never read from -- let alone
write to -- the player's live save files while the game might touch them, and
must never modify or overwrite an original .sav file. Everything downstream of
`copy_bundle_to_workdir` operates only on copies.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path


# Confidence: VERIFIED against this machine's actual Steam install of Palworld.
# Other install types (Xbox/Game Pass, dedicated server) may use different
# locations -- UNKNOWN / not yet investigated, do not assume this is exhaustive.
DEFAULT_STEAM_SAVE_ROOT = Path(os.path.expandvars(r"%LOCALAPPDATA%\Pal\Saved\SaveGames"))


@dataclass
class SaveBundle:
    """Paths to the set of files that make up one world's save, plus the
    account-level files that live alongside it. Any field may be None if that
    file wasn't found -- callers must check, this class does not guess.
    """

    world_dir: Path
    level_sav: Path | None = None
    level_meta_sav: Path | None = None
    local_data_sav: Path | None = None
    world_option_sav: Path | None = None
    player_sav_files: list[Path] = field(default_factory=list)

    # Account-level (one directory up from world_dir)
    global_pal_storage_sav: Path | None = None
    user_option_sav: Path | None = None  # lives at the SaveGames root, not per-account

    def all_existing_files(self) -> list[Path]:
        singles = [
            self.level_sav,
            self.level_meta_sav,
            self.local_data_sav,
            self.world_option_sav,
            self.global_pal_storage_sav,
            self.user_option_sav,
        ]
        return [p for p in singles if p is not None] + list(self.player_sav_files)


def find_world_dirs(save_root: Path = DEFAULT_STEAM_SAVE_ROOT) -> list[Path]:
    """Find candidate world directories under a Steam-style SaveGames root.

    Layout (VERIFIED against a real save on this machine):
        SaveGames/
            UserOption.sav
            <SteamID>/
                GlobalPalStorage.sav
                <WorldID>/
                    Level.sav, LevelMeta.sav, LocalData.sav, WorldOption.sav
                    Players/*.sav
                    backup/...
    """
    world_dirs: list[Path] = []
    if not save_root.exists():
        return world_dirs
    for steam_id_dir in save_root.iterdir():
        if not steam_id_dir.is_dir():
            continue
        for world_dir in steam_id_dir.iterdir():
            if world_dir.is_dir() and (world_dir / "Level.sav").exists():
                world_dirs.append(world_dir)
    return world_dirs


def discover_save_bundle(world_dir: Path) -> SaveBundle:
    def existing(p: Path) -> Path | None:
        return p if p.exists() else None

    steam_id_dir = world_dir.parent
    save_root = steam_id_dir.parent

    players_dir = world_dir / "Players"
    player_files = sorted(players_dir.glob("*.sav")) if players_dir.exists() else []

    return SaveBundle(
        world_dir=world_dir,
        level_sav=existing(world_dir / "Level.sav"),
        level_meta_sav=existing(world_dir / "LevelMeta.sav"),
        local_data_sav=existing(world_dir / "LocalData.sav"),
        world_option_sav=existing(world_dir / "WorldOption.sav"),
        player_sav_files=player_files,
        global_pal_storage_sav=existing(steam_id_dir / "GlobalPalStorage.sav"),
        user_option_sav=existing(save_root / "UserOption.sav"),
    )


def copy_bundle_to_workdir(bundle: SaveBundle, workdir: Path) -> SaveBundle:
    """Copy every file in `bundle` into `workdir` and return a new SaveBundle
    pointing at the copies. The original files are only ever opened for
    reading here (shutil.copy2), never opened for writing.
    """
    workdir.mkdir(parents=True, exist_ok=True)

    def copy_one(src: Path | None, subdir: str = "") -> Path | None:
        if src is None:
            return None
        dest_dir = workdir / subdir if subdir else workdir
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name
        shutil.copy2(src, dest)
        return dest

    player_copies = [copy_one(p, "Players") for p in bundle.player_sav_files]

    return SaveBundle(
        world_dir=workdir,
        level_sav=copy_one(bundle.level_sav),
        level_meta_sav=copy_one(bundle.level_meta_sav),
        local_data_sav=copy_one(bundle.local_data_sav),
        world_option_sav=copy_one(bundle.world_option_sav),
        player_sav_files=[p for p in player_copies if p is not None],
        global_pal_storage_sav=copy_one(bundle.global_pal_storage_sav),
        user_option_sav=copy_one(bundle.user_option_sav),
    )
