import re
import sys
from pathlib import Path

sys.path.insert(0, r"c:\Users\36255\Desktop\VpetAOBA\VpetPNG")
import peer_friendship as pf

text = Path(r"c:\Users\36255\Desktop\VpetAOBA\VpetPNG\pet.py").read_text(encoding="utf-8")
defs = set(re.findall(r"^    def (\w+)\(", text, re.M))
m1 = text.find("    def _stop_peer_meet_poll")
m2 = text.find("    def _screen_wh")
block = text[m1:m2]
calls = set(re.findall(r"self\.(\w+)\(", block))
miss = [c for c in sorted(calls) if c not in defs]
print("missing methods", miss)
attrs = set(re.findall(r"peer_friendship\.(\w+)", block))
miss_a = [a for a in sorted(attrs) if not hasattr(pf, a)]
print("missing pf attrs", miss_a)
print(re.search(r'SPEECH_MEET_BUBBLE_FILL = "[^"]+"', text).group(0))
print("blue hotspot", "#66ccff" in block, "pink hotspot", "#c878a0" in block)
print("meet button", '("meet", "meet")' in block)
print("talk button", '("talk", "talk")' in block)
print("act button", '("act", "act")' in block)
print("has from_meet", "from_meet: bool = False" in text)
print("MEET_PRIORITY", "MEET_PRIORITY_HOLD_MS =" in text)
