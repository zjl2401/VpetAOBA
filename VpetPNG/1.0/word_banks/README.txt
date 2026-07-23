词库文件夹 — 打字 / 背单词专用

请将开源词库 JSON 放在此目录，不要使用视频字幕素材。

文件说明：
  english.json       — 英语背单词
  chinese.json       — 中文背单词
  typing_english.json — 英语打字
  typing_chinese.json — 中文打字（拼音）
  japanese.json       — 日语背单词（JLPT N5–N3，OpenJLPT / CC BY）
  typing_japanese.json — 日语打字（显示假名/汉字，输入罗马字）

日语说明：
  · 背单词释义以英文原注为主，部分高频词附中文
  · hint 含读音（假名）与 JLPT 级别
  · 打字请输入罗马字，如 ありがとう → arigatou

JSON 格式示例见各文件。

重新生成日语词库（开发用）：
  1) 下载 OpenJLPT vocab n5/n4/n3 为 _src_n5.json 等
  2) python _build_japanese_banks.py
