"""Vendored third-party code lives under this package.

The vendored `palworld_save_tools` snapshot uses absolute imports internally
(e.g. `from palworld_save_tools.archive import ...`), because it was written to
be pip-installed as a top-level package. Importing this `vendor` package first
(which happens automatically any time something does
`from save.adapters.vendor.palworld_save_tools import ...`) puts this directory
on sys.path so those internal absolute imports resolve to our vendored copy
instead of requiring a real pip install of the package.
"""

import os
import sys

_VENDOR_DIR = os.path.dirname(__file__)
if _VENDOR_DIR not in sys.path:
    sys.path.insert(0, _VENDOR_DIR)
