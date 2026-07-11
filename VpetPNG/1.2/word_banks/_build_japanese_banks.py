#!/usr/bin/env python3
"""从 OpenJLPT（CC BY）生成日语背单词 / 打字词库。"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC_LEVELS = ("n5", "n4", "n3")

# 基本平假名 / 片假名 → 罗马字（ヘボン式简化）
_KANA_ROMAJI: dict[str, str] = {
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "を": "o", "ん": "n",
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
    "きゃ": "kya", "きゅ": "kyu", "きょ": "kyo",
    "しゃ": "sha", "しゅ": "shu", "しょ": "sho",
    "ちゃ": "cha", "ちゅ": "chu", "ちょ": "cho",
    "にゃ": "nya", "にゅ": "nyu", "にょ": "nyo",
    "ひゃ": "hya", "ひゅ": "hyu", "ひょ": "hyo",
    "みゃ": "mya", "みゅ": "myu", "みょ": "myo",
    "りゃ": "rya", "りゅ": "ryu", "りょ": "ryo",
    "ぎゃ": "gya", "ぎゅ": "gyu", "ぎょ": "gyo",
    "じゃ": "ja", "じゅ": "ju", "じょ": "jo",
    "びゃ": "bya", "びゅ": "byu", "びょ": "byo",
    "ぴゃ": "pya", "ぴゅ": "pyu", "ぴょ": "pyo",
    "っ": "",  # 促音单独处理
    "ー": "",
    "ぁ": "a", "ぃ": "i", "ぅ": "u", "ぇ": "e", "ぉ": "o",
    "ゃ": "ya", "ゅ": "yu", "ょ": "yo", "ゎ": "wa",
}
# 片假名：由平假名偏移生成（仅单字）
for _h, _r in list(_KANA_ROMAJI.items()):
    if len(_h) == 1 and "\u3041" <= _h <= "\u3096":
        _KANA_ROMAJI[chr(ord(_h) + 0x60)] = _r
# 片假名拗音
for _h, _r in list(_KANA_ROMAJI.items()):
    if len(_h) == 2 and all("\u3041" <= c <= "\u3096" for c in _h):
        _KANA_ROMAJI["".join(chr(ord(c) + 0x60) for c in _h)] = _r


def _kata_to_hira(text: str) -> str:
    out = []
    for ch in text:
        if "ァ" <= ch <= "ヶ":
            out.append(chr(ord(ch) - 0x60))
        else:
            out.append(ch)
    return "".join(out)


def kana_to_romaji(text: str) -> str:
    s = _kata_to_hira(text.strip())
    # 长音符号在平假名里少见；片假名ー上面已映射为空，下面用启发式
    out: list[str] = []
    i = 0
    while i < len(s):
        if s[i] in " \t　・、。!！?？「」『』（）()[]【】":
            i += 1
            continue
        if s[i] == "ー" and out:
            # 拉长前一元音
            prev = out[-1]
            for v in ("a", "i", "u", "e", "o"):
                if prev.endswith(v):
                    out[-1] = prev + v
                    break
            i += 1
            continue
        if s[i] == "っ" and i + 1 < len(s):
            # 促音：双写下一段辅音
            nxt = s[i + 1 : i + 3] if i + 2 <= len(s) else s[i + 1 :]
            dig = _KANA_ROMAJI.get(nxt[:2]) or _KANA_ROMAJI.get(nxt[:1], "")
            if dig:
                out.append(dig[0])
            i += 1
            continue
        digraph = s[i : i + 2]
        if digraph in _KANA_ROMAJI and len(digraph) == 2:
            out.append(_KANA_ROMAJI[digraph])
            i += 2
            continue
        ch = s[i]
        if ch in _KANA_ROMAJI:
            out.append(_KANA_ROMAJI[ch])
            i += 1
            continue
        # 非假名（汉字等）跳过，罗马字目标只靠 reading
        i += 1
    roma = "".join(out)
    roma = re.sub(r"n([bmp])", r"m\1", roma)
    return roma


def _reading_of(entry: dict) -> str:
    reading = str(entry.get("reading") or "").strip()
    word = str(entry.get("word") or "").strip()
    if reading:
        return reading
    # 纯假名词：reading 为空时用 word
    if word and all(
        ("ぁ" <= c <= "ゖ") or ("ァ" <= c <= "ヶ") or c in "ーっッ・ "
        for c in word
    ):
        return word
    return ""


def _translate_batch(texts: list[str]) -> dict[str, str]:
    from deep_translator import GoogleTranslator

    cache_path = ROOT / "_zh_gloss_cache.json"
    cache: dict[str, str] = {}
    if cache_path.exists():
        try:
            raw = json.loads(cache_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                cache = {str(k): str(v) for k, v in raw.items()}
        except Exception:
            cache = {}

    tr = GoogleTranslator(source="en", target="zh-CN")
    uniq = []
    seen = set()
    for t in texts:
        key = t.strip()
        if key and key not in seen:
            seen.add(key)
            uniq.append(key)
    pending = [t for t in uniq if t not in cache]
    print(f"translate {len(pending)} new / {len(uniq)} unique glosses…")
    for i, text in enumerate(pending, 1):
        try:
            cache[text] = tr.translate(text) or text
        except Exception:
            cache[text] = text
        if i % 50 == 0:
            cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
            print(f"  {i}/{len(pending)}")
            time.sleep(0.4)
        else:
            time.sleep(0.04)
    cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return cache


def main() -> None:
    entries: list[dict] = []
    for lv in SRC_LEVELS:
        path = ROOT / f"_src_{lv}.json"
        if not path.exists():
            raise SystemExit(f"missing {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise SystemExit(f"bad format: {path}")
        entries.extend(data)

    glosses = []
    for e in entries:
        meanings = e.get("meanings") or []
        if meanings:
            glosses.append(str(meanings[0]))
    zh_map = _translate_batch(glosses)

    vocab_words: list[dict] = []
    typing_items: list[dict] = []
    seen_word: set[str] = set()
    seen_type: set[str] = set()

    for e in entries:
        word = str(e.get("word") or "").strip()
        if not word or word in seen_word:
            continue
        level = str(e.get("level") or "").upper() or "?"
        meanings = e.get("meanings") or []
        en = str(meanings[0]).strip() if meanings else ""
        zh = zh_map.get(en, en) if en else ""
        if not zh:
            continue
        reading = _reading_of(e)
        hint = f"JLPT {level}"
        if reading and reading != word:
            hint = f"{reading} · JLPT {level}"
        vocab_words.append(
            {
                "word": word,
                "meaning": zh,
                "hint": hint,
                "lang": "日语",
            }
        )
        seen_word.add(word)

        roma = kana_to_romaji(reading) if reading else ""
        if roma and len(roma) >= 2 and roma.isascii() and roma not in seen_type:
            typing_items.append({"display": word, "target": roma})
            seen_type.add(roma)

    # 额外假名打字练习（基础）
    kana_drills = [
        ("あ", "a"), ("い", "i"), ("う", "u"), ("え", "e"), ("お", "o"),
        ("か", "ka"), ("き", "ki"), ("く", "ku"), ("け", "ke"), ("こ", "ko"),
        ("さ", "sa"), ("し", "shi"), ("す", "su"), ("せ", "se"), ("そ", "so"),
        ("た", "ta"), ("ち", "chi"), ("つ", "tsu"), ("て", "te"), ("と", "to"),
        ("な", "na"), ("に", "ni"), ("ぬ", "nu"), ("ね", "ne"), ("の", "no"),
        ("は", "ha"), ("ひ", "hi"), ("ふ", "fu"), ("へ", "he"), ("ほ", "ho"),
        ("ま", "ma"), ("み", "mi"), ("む", "mu"), ("め", "me"), ("も", "mo"),
        ("や", "ya"), ("ゆ", "yu"), ("よ", "yo"),
        ("ら", "ra"), ("り", "ri"), ("る", "ru"), ("れ", "re"), ("ろ", "ro"),
        ("わ", "wa"), ("を", "o"), ("ん", "n"),
        ("が", "ga"), ("ざ", "za"), ("だ", "da"), ("ば", "ba"), ("ぱ", "pa"),
        ("ア", "a"), ("カ", "ka"), ("サ", "sa"), ("タ", "ta"), ("ナ", "na"),
        ("こんにちは", "konnichiwa"), ("ありがとう", "arigatou"),
        ("すみません", "sumimasen"), ("おはようございます", "ohayou"),
    ]
    for disp, tgt in kana_drills:
        if tgt not in seen_type:
            typing_items.append({"display": disp, "target": tgt})
            seen_type.add(tgt)

    vocab_out = {
        "source": "OpenJLPT N5–N3 (CC BY) + zh gloss via auto-translate",
        "license_note": "JLPT level lists attributed via OpenJLPT / Jonathan Waller (CC BY). Not official JLPT.",
        "words": vocab_words,
    }
    typing_out = {
        "source": "OpenJLPT N5–N3 readings → romaji + kana drills",
        "license_note": "Same attribution as japanese.json. Type romaji for the shown Japanese.",
        "items": typing_items,
    }

    (ROOT / "japanese.json").write_text(
        json.dumps(vocab_out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (ROOT / "typing_japanese.json").write_text(
        json.dumps(typing_out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"vocab {len(vocab_words)}  typing {len(typing_items)}")


if __name__ == "__main__":
    main()
