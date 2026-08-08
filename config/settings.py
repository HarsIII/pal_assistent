"""Project-wide paths and configuration.

Deliberately outside the git-tracked project tree for anything that touches
real save data (project rule: never commit a player's personal save data).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Where safe, read-only working copies of a real save get placed for
# inspection. Lives under the OS temp directory, never inside the repo.
DEFAULT_WORKDIR = Path(tempfile.gettempdir()) / "pal_breeding_assistant_workdir"

# Default Steam save location (VERIFIED on this machine; Xbox/dedicated-server
# layouts are UNKNOWN -- not yet investigated).
DEFAULT_STEAM_SAVE_ROOT = Path(os.path.expandvars(r"%LOCALAPPDATA%\Pal\Saved\SaveGames"))
