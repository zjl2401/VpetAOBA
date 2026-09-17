# -*- coding: utf-8 -*-
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import home_cottage as home_room

s = home_room.home_day_sky_state()
need = ("sky", "trim", "indoor_wall", "indoor_trim", "celestial", "cx", "label")
missing = [k for k in need if k not in s]
print("missing", missing)
assert not missing
print("ok", s["indoor_trim"], s["period"])
