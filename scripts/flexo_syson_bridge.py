#!/usr/bin/env python3
"""Compatibility entry point for the Flexo/SysON bridge CLI."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mbse_lab.bridge.workflow import *  # noqa: E402,F403
from mbse_lab.bridge.workflow import main  # noqa: E402

if __name__ == "__main__":
    main()
