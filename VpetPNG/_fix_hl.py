# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(__file__).with_name("pet.py")
t = p.read_text(encoding="utf-8")
old = 'btn.config(bg=MENU_ACTIVE if on else HOME_UI_BTN_ALT, relief=tk.SUNKEN if on else tk.FLAT)'
new = 'btn.config(bg=HOME_THEME["accent"] if on else HOME_THEME["card"], relief=tk.SUNKEN if on else tk.FLAT)'
c = t.count(old)
t = t.replace(old, new)
print("replaced", c)
p.write_text(t, encoding="utf-8")
