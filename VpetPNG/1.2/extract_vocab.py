"""从 vocab_sources 文件夹提取词库，写入 vocab.json。"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ASSET_DIR = Path(__file__).parent
VOCAB_SOURCES = ASSET_DIR / "vocab_sources"
VOCAB_FILE = ASSET_DIR / "vocab.json"

# 复用 pet.py 中的默认词与解析逻辑
sys.path.insert(0, str(ASSET_DIR))
from pet import DEFAULT_VOCAB_WORDS, _merge_vocab_from_sources, _save_vocab  # noqa: E402


def main() -> None:
    VOCAB_SOURCES.mkdir(exist_ok=True)
    words = _merge_vocab_from_sources()
    _save_vocab(words)
    print(f"已写入 {VOCAB_FILE}，共 {len(words)} 条词库。")
    print("提示：可将 .srt/.txt/.json 放入 vocab_sources 后重新运行本脚本。")


if __name__ == "__main__":
    main()
