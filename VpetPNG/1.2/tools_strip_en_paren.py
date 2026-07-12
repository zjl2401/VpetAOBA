# -*- coding: utf-8 -*-
"""Strip English leftovers in parentheses from english vocab meanings."""
import json
import re
from collections import Counter
from pathlib import Path

BANK = Path(__file__).resolve().parent / "word_banks"
PATH = BANK / "english.json"


def clean_meaning(meaning: str) -> str:
    m = str(meaning or "")
    m = re.sub(r"[（(][^）)]*[A-Za-z][^）)]*[）)]", "", m)
    m = re.sub(r"\[[^\]]*[A-Za-z][^\]]*\]", "", m)
    m = re.sub(r"(?i)English word:\s*\S+", "", m)
    m = re.sub(r"\s{2,}", " ", m).strip(" ；;，,、 ")
    return m or "常用词汇"


def main() -> None:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    words = data.get("words", [])
    for w in words:
        w["meaning"] = clean_meaning(w.get("meaning", ""))

    counts = Counter(w["meaning"] for w in words)
    seen: dict[str, int] = {}
    for w in words:
        m = w["meaning"]
        if counts[m] <= 1:
            continue
        n = seen.get(m, 0) + 1
        seen[m] = n
        hint = str(w.get("hint") or "").strip()
        if hint and hint not in m and not re.search(r"[A-Za-z]", hint):
            w["meaning"] = f"{m}（{hint}）" if n == 1 else f"{m}（{hint}{n}）"
        elif n > 1:
            w["meaning"] = f"{m}（义项{n}）"

    # final uniqueness without English
    used: dict[str, int] = {}
    for w in words:
        m = w["meaning"]
        if m not in used:
            used[m] = 1
            continue
        used[m] += 1
        w["meaning"] = f"{m}（义项{used[m]}）"

    latin = [(w["word"], w["meaning"]) for w in words if re.search(r"[A-Za-z]", w["meaning"])]
    data["words"] = words
    data["source"] = "enriched-en-no-en-paren"
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("count", len(words), "unique", len({w["meaning"] for w in words}), "latin_left", len(latin))
    if latin:
        print("samples", latin[:8])


if __name__ == "__main__":
    main()
