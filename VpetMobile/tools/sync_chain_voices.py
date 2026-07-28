"""Copy digit/letter chain voice pairs into VpetMobile assets (ASCII-safe names)."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent / "VpetPNG" / "1.0" / "bundled" / "Vpetvoice"
DST = ROOT / "app" / "src" / "main" / "assets" / "voice"
PREFIX_RE = re.compile(r"^((?:\d+)|(?:[a-zA-Z]))(?:[\s._\-]+)(.+)$")


def collect(src_root: Path, source: str) -> dict[str, Path]:
    out: dict[str, Path] = {}
    if not src_root.is_dir():
        return out
    files = sorted(src_root.rglob("*.wav")) if source == "vpet" else sorted(src_root.glob("*.wav"))
    for f in files:
        m = PREFIX_RE.match(f.stem)
        if not m:
            continue
        raw = m.group(1)
        key = raw.lower() if raw.isalpha() else raw
        # keep first match per prefix
        out.setdefault(key, f)
    return out


def main() -> None:
    vpet = collect(SRC / "Vpet", "vpet")
    mate = collect(SRC / "Allmate", "allmate")
    chain_dir = DST / "chain"
    chain_dir.mkdir(parents=True, exist_ok=True)
    index: dict[str, dict[str, str]] = {"vpet": {}, "allmate": {}}

    for prefix, src in vpet.items():
        kind = "digit" if prefix.isdigit() else "letter"
        name = f"vpet_{kind}_{prefix}.wav"
        shutil.copy2(src, chain_dir / name)
        index["vpet"][prefix] = f"voice/chain/{name}"
        print("vpet", prefix, "<-", src.name)

    for prefix, src in mate.items():
        kind = "digit" if prefix.isdigit() else "letter"
        name = f"allmate_{kind}_{prefix}.wav"
        shutil.copy2(src, chain_dir / name)
        index["allmate"][prefix] = f"voice/chain/{name}"
        print("allmate", prefix, "<-", src.name)

    (DST / "chain_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("wrote", DST / "chain_index.json")


if __name__ == "__main__":
    main()
