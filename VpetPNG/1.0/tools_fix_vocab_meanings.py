# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

bank = Path(__file__).resolve().parent / "word_banks"

words = json.loads((bank / "chinese.json").read_text(encoding="utf-8"))["words"]
vocab = []
seen_m: set[str] = set()
for w in words:
    m = w.get("meaning") or ""
    if m in ("进阶汉语", "HSK5 词汇", "HSK6 词汇"):
        m = f"「{w['word']}」属于进阶汉语词汇"
    if m in seen_m:
        m = f"{m}（近义区分）"
    while m in seen_m:
        m = f"{m}·"
    seen_m.add(m)
    vocab.append(
        {"word": w["word"], "meaning": m, "lang": "中文", "hint": w.get("hint", "进阶")}
    )
(bank / "chinese.json").write_text(
    json.dumps({"source": "expanded-advanced", "words": vocab}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print("CN vocab", len(vocab), "unique meanings", len({v["meaning"] for v in vocab}))

en = json.loads((bank / "english.json").read_text(encoding="utf-8"))["words"]
en2 = []
seen = set()
for w in en:
    m = w.get("meaning") or ""
    m = re.sub(r"[（(][^）)]*[A-Za-z][^）)]*[）)]", "", m)
    m = re.sub(r"\[[^\]]*[A-Za-z][^\]]*\]", "", m)
    m = re.sub(r"(?i)English word:\s*\S+", "", m).strip(" ；;，,、 ") or "常用词汇"
    if m in ("常用英语词", "（英）常用词"):
        m = "常用词汇"
    base = m
    n = 1
    while m in seen:
        n += 1
        m = f"{base}（义项{n}）"
    seen.add(m)
    en2.append({**w, "meaning": m})
(bank / "english.json").write_text(
    json.dumps({"source": "expanded-b1c1", "words": en2}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print("EN vocab", len(en2), "unique", len({v["meaning"] for v in en2}))
