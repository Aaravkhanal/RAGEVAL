"""Locate project assets in a checkout or an installed wheel."""
from __future__ import annotations

import os
import sys


def resolve_asset(path: str) -> str:
    if os.path.exists(path) or os.path.isabs(path):
        return path
    installed = os.path.join(sys.prefix, "share", "rageval", path)
    return installed if os.path.exists(installed) else path
