伊得 UI 音效（可选外置 wav）
放到本目录后优先于合成音播放。支持 .wav / .ogg / .mp3。

文件名（中英均可）：
  点击.wav / click.wav
  打开窗口.wav / open_window.wav
  打开商店.wav / open_shop.wav
  游戏开始.wav / game_start.wav
  游戏成功.wav / game_success.wav
  游戏失败.wav / game_fail.wav
  收获.wav / harvest.wav

触发规则：
  游戏开始     — 小游戏倒计时开始、打开 RPG
  游戏成功/失败 — 结算画面；背词错、暴露失败也播失败
  打开窗口     — 菜单/设置/家园/面板等窗口（toast/特效/倒计时除外）
  打开商店     — 背包展开、经营商店、合成台、吃东西菜单
  收获         — 仅：采集完成、家园收获成功、领到金币
  点击         — 任意鼠标左键（70ms 去重）
