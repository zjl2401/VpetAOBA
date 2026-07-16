# 语音添加前功能基线（必须实现）

> **适用范围**：除「语音模式 / 语音字幕 / 留声机语音条目」以外，下列功能在任意版本中都**必须一一实现**。  
> **维护纪律**：每次改 `pet.py`、`voice_system.py`、打包脚本或 UI 资源后，**必须按文末核对表逐条勾选**，不得跳过。  
> **只读对照**：`REQUIREMENTS.md`、`FEATURES.md` 原文不得覆盖改写；本文件在其基础上补全代码锚点与验收项。

---

## 一、基线范围说明

| 类别 | 是否属于本基线 | 说明 |
|------|----------------|------|
| 菜单、模式、小游戏、互动、面板 | ✅ 必须 | 与语音开关无关 |
| 打字对话框、粒子/下雨/灯泡等 FX | ✅ 必须 | 语音不得替代或跳过 |
| border5 对话条（仅系统→对话） | ✅ 必须 | `SPEECH_BORDER_STEM=border5` + `_layout_speech_dialog(use_border5=True)`；内容区不透明；其余为扁平 |
| 出场逆向像素扫描 | ✅ 必须 | 关闭桌宠时播放 |
| 语音播放、语音台词框、Vpetvoice 扫描 | ❌ 不在此表 | 见 `voice_system.py`，仅作附加层 |
| 留声机（音乐/音效/语音分类） | ⚠️ 部分 | 原留声 + 音乐/音效必须；语音导入为扩展 |

---

## 二、基础与菜单

| # | 功能 | 预期行为 | 代码锚点 |
|---|------|----------|----------|
| B01 | 四大模块菜单 | 右键：模式 / 面板 / 互动 / 系统 | `_toggle_main_menu` |
| B02 | 左键拖拽 | 透明抠图精灵可拖动 | `_on_press` / `_on_drag` |
| B03 | 三档大小 | 小/中/大，持久化 `app_config` | `_apply_display_size` |
| B04 | 四档字体 | 小/中/大/特大，持久化 | `_apply_font_scale` |
| B05 | 操作说明 F1 | 首次启动自动弹一次 | `_open_operation_guide` |
| B06 | 一次性提示 | 游戏/伴侣/音乐等只提示一次 | `_show_once_hint` |
| B07 | 难度 低/中/高 | 影响体力心情、接食物、暴露 QTE、对战 | `_difficulty_params` |
| B08 | 重置 | 恢复初始设置，编号保留 | `_reset_app_settings` |
| B09 | 关于 | 百科风文案 + Steam 链接 | `_open_about` |
| B10 | Esc 回自由 | 退出当前模式/子窗口 | `_exit_to_free` |
| B11 | 模式切换优先 | 打断睡眠/工作/互动 | `_interrupt_for_mode_switch` |

---

## 三、模式

| # | 功能 | 预期行为 | 代码锚点 |
|---|------|----------|----------|
| M01 | 跟随 | 跟鼠标；频繁变向晕眩 3s +「我晕了……」 | `_follow_tick` / `_trigger_follow_dizzy` |
| M02 | 自由 | 随机动作/表情/词库对话 | `_resume_idle` / 词库对话 |
| M03 | 漫步 | 仅 stand/walk | `mode == "stroll"` |
| M04 | 睡眠模式 | 深度睡眠与唤醒 | `_enter_quiet_mode` |
| M05 | 游戏▶采集 | 30s 鼠标接食物，写背包与记录 | `_start_game_mode` / `_end_game_session` |
| M06 | 游戏▶打字 | 30s、C~S 评级、虚拟键盘闪光 | `_open_typing_game` |
| M07 | 游戏▶背单词 | 英/日；自由模式每日限次 | `_open_vocab_game` |
| M08 | 音乐模式 | BGM + music 精灵 + 脚下声波（自主律动，不跟拍） | `_enter_music_sprite_mode` |

---

## 四、对话框与打字（原功能，语音不得占用）

| # | 功能 | 预期行为 | 代码锚点 |
|---|------|----------|----------|
| D01 | 逐字打字 | 动作/表情打字框有打字动画 + `type_cache` | `_speech_type_next` |
| D02 | 打字音效 | `type_cache.wav`，按字播放 | `_play_type_sound` |
| D03 | border5 对话条 | **仅系统→对话**（AI / 普通对话）使用 **border5 资源**九宫形变；内容区不透明（沿用面板内色，禁止透明底）；其余一律扁平框 | `_layout_speech_dialog(use_border5=True)` / `SPEECH_BORDER_STEM` |
| D04 | 无台词动作 | wink、脸红、有主意、下蹲无 banter | `_interact_flair` banter 配置 |
| D05 | ×生活文案 | 固定 ADULT 文案（扁平框） | `_play_adult_msg` |
| D06 | 打电话 | 关语音：CALL_TEXT 扁平打字+铃声；开语音：**必先 ring→非 ring 台词+语音框**（专项，不参与二选一） | `_show_call_dialog` / `play_call` |
| D07 | 打招呼 | 关语音：HI_TEXT 扁平打字；开语音：语音标题框 **与** HI_TEXT **随机二选一** | `_show_hi_dialog` / `_trigger_voice_or_dialog` |
| D08 | 语音台词框 | 抽中语音时：`voice_subtitle_win` 扁平标题框；与打字框互斥 | `_show_voice_subtitle` |
| D09 | 开/关语音抽选 | **关语音**：只有动作/表情打字框；**开语音**：有对应语音时「语音框」与「动作/表情打字框」随机一条 | `_trigger_voice_or_dialog` / `_interact_flair` |

**语音附加规则**：
1. **系统→对话**必须用 **border5** 边框（`assets/ui/border5.*`），内容区**不透明**（不必改成 `#1a1a1a`，沿用现有内色即可）；动作、表情、打招呼、电话（关语音）、语音字幕等**全部扁平框**。
2. 开语音抽中台词：播语音同时 `_show_voice_subtitle`；抽中打字框：仅 `_show_speech_dialog`（扁平）+ 打字音，不播语音。
3. 关语音不得播语音；动作/表情原有文本框必须保留。
4. 播放失败或无声时不得残留文本框（见第十二节 V-AUDIO）。

---

## 五、表情与背景特效（必须完整播放）

| # | 动作 | 特效 | 对话 | 代码锚点 |
|---|------|------|------|----------|
| F01 | 开心 | 跳跃 + 身后像素小花 | 无 | `_play_happy` / `_show_happy_fx` |
| F02 | 生气 | walkback 上移 + 怒 mark | 有 | `_play_expression_angry` |
| F03 | 伤心 | 头上像素下雨 | 有 | `_play_expression_sad` / `_show_rain_fx` |
| F04 | 有主意 | 左上角灯泡亮 → eat2 | 无 | `_play_expression_idea` / `_show_bulb_fx` |
| F05 | 侧踢 | 粒子 3s | 有 banter | `_show_interact_fx` / `_interact_flair("kick")` |
| F06 | 点赞 | 背景像素发光 | 无 | `_show_like_fx` |
| F07 | wink | 爱心声波像素 | 无 | `_show_wink_fx` |
| F08 | 脸红 | 爱心像素 | 可选 | `_show_shy_fx` |
| F09 | 音乐模式 | 脚下像素声波**自主律动**（与曲目节奏无关） | 有 | `_start_music_wave_fx` / `_draw_music_wave` |
| F10 | 喂食 | 食物粒子 FX | 有 | `_show_food_fx` |
| F11 | 动作结束 | 自动清理雨/灯泡/点赞/wink 等 | — | `_interrupt_current_interaction` 内 `_hide_*_fx` |

**禁止**：因 `voice_player.is_busy()` 或语音字幕存在而跳过 `show_fx` 或 `_interact_flair` 粒子。

---

## 六、判断与暴露 QTE

| # | 功能 | 预期行为 | 代码锚点 |
|---|------|----------|----------|
| E01 | 判断 | stand +「答案」5s → 随机 yes/no | `_play_yesno` |
| E02 | 暴露界面 | 无黑屏；圆环 QTE + 故障层 | `_spawn_expose_glitch_round` |
| E03 | Enter 判定 | 难度影响扇区/指针速度 | `_resolve_expose_qte_hit` |
| E04 | 暴露成功 | **game_clear 通关动画** → 恢复 | `_finish_expose_session(cleared=True)` |
| E05 | 暴露失败 | **故障界面保留约 900ms** + 打字「暴露失败…」 | `_finish_expose_session(cleared=False)` |
| E06 | 暴露失败禁止项 | **不得**用全屏 game_clear 替代失败反馈 | 同上 else 分支 |

---

## 七、小游戏结算（原画面必须先出现）

| # | 游戏 | 失败/结束时的原功能 | 代码锚点 |
|---|------|---------------------|----------|
| G01 | 采集结束 | game_clear 粒子结算（接取/得分/库存） | `_end_game_session` → `_show_game_clear` |
| G02 | 采集差劲 | 结算照常；语音仅附加 | `_play_game_fail_voice` 在 clear 之后 |
| G03 | 打字结束 | game_clear + 字母评级 | `finish_game` in typing |
| G04 | 音游结束 | game_clear + 评级 D~S | `_close_rhythm_game(finished=True)` |
| G05 | 背单词错 | 状态标签 + 生词本提示 + 自动下一题 | `_vocab_answer` wrong 分支 |
| G06 | 背单词连击 | game_clear 连击通关 | streak clear 分支 |
| G07 | 练习对战胜 | game_clear 胜利 → 关闭对战窗 | `end_fight(True)` |
| G08 | 练习对战败 | **对战界面保留 ~1.6s** 后关闭（非全屏结算） | `end_fight(False)` → `after(1600, _close_rhyme_fight)` |

---

## 八、面板、背包、伴侣

| # | 功能 | 预期行为 | 代码锚点 |
|---|------|----------|----------|
| P01 | 面板外观 | **已去除 border1**；纯色内容区 + `panel_decor` 条纹装饰 | `_layout_panel_border` / `PANEL_BORDER_STEM=""` |
| P02 | 体力/心情/背包 | 数值展示与刷新；**食物仅在背包内** | `_refresh_panel` |
| P03 | 背包交互 | **默认合上**；点击背包头展开/收起，内显食物列表 | `_toggle_panel_backpack` / `_set_panel_backpack_open` |
| P04 | 面板关闭 | 面板右上角 **×** 可关闭（除自动隐藏外） | `_toggle_panel` / `_close_panel` |
| P05 | 食物拖拽喂食 | 只拖给苍叶；有智能伴侣时伴侣不用吃；每次 1 份，恢复苍叶体力心情 | `_feed_food` / `_play_eat_food` |
| P06 | 吃东西动画 | eat 序列 + 食物 FX + 咀嚼音 | `_play_eat_food` / `_play_eat_sound` |
| P07 | 智能伴侣金目 | 100px 侧向跟随；游戏跟紧；工作导航；跟随朝向防抖（hold+轴向迟滞） | `_mini_pet_follow_tick` |
| P08 | 面板弹出定位 | 靠屏外方向展开 | `_place_panel_popup` |

---

## 九、出场 / 入场动画

| # | 功能 | 预期行为 | 代码锚点 |
|---|------|----------|----------|
| A01 | 入场扫描 | 切换尺寸/召唤金目：像素格点亮 | `_draw_size_loading_frame` |
| A02 | 出场逆向 | 关闭桌宠：像素格熄灭（reverse） | `_run_exit_dissolve_at(..., reverse 逻辑)` |
| A03 | 退出顺序 | **无语音**：默认时长出场动画 → 销毁 | `_on_close` → `_play_exit_dissolve` |
| A04 | 退出+语音 | 有语音：`end` 语音与出场**同步**；**动画时长=语音时长**；语音结束且动画结束 → 彻底退出 | `_on_close` / `_try_finish_exit_sync` |

---

## 十、其他系统

| # | 功能 | 预期行为 | 代码锚点 |
|---|------|----------|----------|
| S01 | 拖拽落地 | move 动画结束整体下移 | `_move_land_settle` |
| S02 | 游戏模式移动 | 鼠标移动接食物（非拖拽） | `_game_mode_tick` |
| S03 | 工作模式 | 搬箱；拖拽松手继续工作 | work 相关 |
| S04 | 睡眠互动 30s | 深度睡眠后自动醒 | `_play_sleep_interact` |
| S05 | 日程提醒 | schedules 到点 toast | `_reminder_tick` |
| S06 | AI 对话 | 千问 + fallback | `_toggle_ai_chat` |
| S07 | 留声机 | 音乐/音效播放与列表 | `_open_phonograph` |
| S08 | 全局热键 | Ctrl+Shift+* 见 FEATURES.md | `_register_hotkey` |

---

## 十一、语音附加层（不改变上表，仅并行）

以下为语音**额外**行为，**不能**替换第二节～第十节任何一项：

1. `voice_mode` 关闭时，行为与上表完全一致。
2. `voice_mode` 开启时：原功能照常 + 语音并行；有台词必出**语音扁平框**（非 border5，见 D08）。
3. 游戏失败、暴露失败、打电话：原 UI/动画/结算**先执行**，语音排队附加。
4. ffmpeg 转码使用 `CREATE_NO_WINDOW`，不得闪黑控制台。
5. 音效与语音声道互斥仅作用于 `sfx`，不阻止 FX 与 game_clear。
6. 语音缓存 `voice_cache/*_p2.wav`；裁切过短回退 plain wav，避免「无声但有框」。

---

## 十二、每次改动后的强制核对表（必做）

> **操作要求**：打包前逐项打勾 `[x]`。**任一项未通过不得发布。**  
> 下列同时覆盖：语音前基线 + 会话最终要求（语音/文本框/设置/退出/喂食/打电话等）。

### A. UI 可用性（最高优先）
- [x] **UI-01** 系统→设置：按钮可点、可滚动（含语音模式开/关）
- [x] **UI-02** 设置打开时桌宠/金目**不得**抬到设置之上吞点击
- [x] **UI-03** 系统→退出：能正常彻底退出；开语音时出场时长跟 `end` 语音，语音结束且动画结束再销毁；卡死时仍有兜底强制退出
- [x] **UI-04** Ctrl+Shift+Q 强制退出热键始终可用（**不在面板/菜单里显示**；小人/面板卡死时用）

### B. 面板 / 背包 / 喂食 / 伴侣
- [x] **P-UI-01** 面板右上角 **×** 可立即关闭
- [x] **P-UI-02** 背包**默认合上**；点击展开/收起
- [x] **P-UI-03** 食物只在背包内（图标+数量+加成）
- [x] **P-UI-04** 面板**无 border1**（`PANEL_BORDER_STEM=""`）
- [x] **P-FEED-01** 喂食只喂**苍叶**；有智能伴侣时**伴侣不用吃**（不作为落点、不播吃动画）
- [x] **P-FEED-02** 每次只消耗 **1 份**食物（体力/心情只加给苍叶）
- [x] **P-MATE-01** 金目位置钳在屏幕内
- [x] **P-MATE-02** 点击金目 / 开启伴侣：Allmate ring 或启动音

### C. 文本框（最终规格）
- [x] **V-BORDER5** 系统→对话：`use_border5=True` 且资源为 **`border5`**（非 border2）；内容区不透明；其余一律扁平普通框
- [x] **V-TEXT-01** 抽中语音有台词：显示**独立扁平** `voice_subtitle_win`，内容=去前缀标题
- [x] **V-TEXT-02** 语音框显示时长 = 语音时长 + **1s**，然后必须消失
- [x] **V-TEXT-03** 打字框与语音框**互斥**
- [x] **V-TEXT-04** ring（打电话铃响）**不出**文本框
- [x] **V-TEXT-05** 无声/播放失败：**不出**残留文本框
- [x] **V-TEXT-06** 语音框叠在立绘之上
- [x] **V-TEXT-07** 打招呼动作结束不得提前关掉仍在播的语音标题框
- [x] **V-PICK-01** **关语音**：只有动作/表情打字框（扁平 + 打字音）；不播语音
- [x] **V-PICK-02** **开语音**：有对应语音时，在「语音+标题框」与「动作/表情打字框」中**随机抽一条**；抽中语音则播语音+框，否则只打字框
- [x] **V-PICK-03** 动作/表情原有文本框逻辑必须保留（不可因开语音永久删掉打字框路径）
- [x] **D-TYPE** 动作/表情打字框使用 `type_cache`；与语音声道冲突时语音优先

### D. 打电话 / 打招呼
- [x] **V-CALL-01** 开语音：**必须先** `Vpet/call/ring`（无框）→ 紧跟非 ring（框+声）；专项强制，不参与二选一
- [x] **V-CALL-02** 关语音：CALL_TEXT 扁平打字 + 原铃声
- [x] **V-HI-01** 关语音：HI_TEXT 扁平打字框
- [x] **V-HI-02** 开语音：语音标题框 与 HI_TEXT 打字框**随机二选一**；动作结束不杀仍在播的语音框

### E. 语音规则与场景触发
- [x] **V-MODE** 设置里可开关；关=去掉电话语音轨，保留音效/音乐
- [x] **V-MIX** 音效与语音互斥；音乐与二者均可共存
- [x] **V-CHAIN-NUM** Vpet 数字前缀 → 有伴侣时接 Allmate 同号
- [x] **V-CHAIN-ALPHA** Allmate 字母前缀 → 接 Vpet normal 同字母
- [x] **V-CD** 整段会话结束后 ≥10s 再触发下一段（链式对答算一段）
- [x] **V-SCENE** eat/sleep/kick/call/hi/end 等专项优先于自由随机；有专用资源时**强制播**（不被 50/50 打字框整段盖掉）；interrupt 后延后补播；stop 作废旧异步回调防抢声道
- [x] **V-FREE** 自由：normal/forget/dizzy/jinmu；（有伴侣）+ren；error 长间隔
- [x] **V-WALK/WORK** walk / work 随机
- [x] **V-HUNGRY** 体力低 hungry
- [x] **V-EMAIL** 点对话 email
- [x] **V-GAME** 关于 game；莱姆开始前 laimu open
- [x] **V-HURT** 游戏失败 hurt（**只附加**，原结算画面保留）— 采集（错过≥接住或 0 接）/打字 D·C / 音游 D·C / 背词错 / 暴露失败；延迟补播+可重试；`ignore_cooldown` **不得**误掐 hurt；**对战失败受 G08 牵连**
- [x] **V-END** 退出：`end` 与出场同步，时长由语音决定；结束后彻底退出（可超时强制退）
- [x] **V-ADDON** 语音附加层不得 `return` 跳过原动画/结算/特效

### F. 基线动画 / 特效 / 暴露 / 出场
- [x] B01–B11 / M02–M08 / G01–G07 与基线表大体一致（2026-07-16 代码抽检）
- [ ] **G08** 练习对战失败：保留对战界面 ~1.6s 后关闭（**仍** `_show_game_clear(title="对战失败")` → 未过）
- [ ] **M01** 跟随晕眩 **3s**（**仍** `FOLLOW_DIZZY_STAND_MS=1500` → 未过）
- [ ] **F07** wink 专用特效 `_show_wink_fx`（**仍** `_play_like_or_wink` → `_show_like_fx` → 未过）
- [ ] **E05** 暴露失败：故障界面保留约 **900ms** + 打字「暴露失败…」（**仍** toast 2.2s + 无打字框 → 未过；hurt 无字幕见 H-EXPOSE-NOSUB 已过）
- [x] 暴露成功 game_clear；失败不用全屏 clear（见 H-EXPOSE-NOSUB）
- [x] 进出场像素动画保留；语音开启不吃掉特效；风格固定见 H-LOAD-FIXED

### G. 文档 / 发布
- [x] 未改写 `REQUIREMENTS.md` / `FEATURES.md` 原文（只读对照仍在）
- [x] 新包路径明确；托盘退出旧进程后再开快捷方式；`BUILD_STAMP` 可核对

### H. 会话后追加（写入必做 · 逐条核对）
> 下列为基线之后陆续提出、现已并入必做的规格。**缺项不得按已完成发布。**

- [x] **H-SPEECH-BELOW** 对话/语音文本框**优先**桌宠正下方；越界则夹进屏内**强制显示**（禁止因放不下/重叠直接销毁；系统→对话回答框必现）
- [x] **H-BG-OPAQUE** 面板与文本框内容区**必须不透明**；底色**不必**改成 `#1a1a1a`，沿用现有内色（如 `#12182a`）即可；**禁止透明底**
- [x] **H-BORDER5** 系统→对话边框资源为 **border5**（九宫按内容形变、去外圈白边）；动作/表情/语音字幕等仍扁平；**废弃**对 border2/border3 对话条的强制要求
- [x] **H-BORDER3** **废弃**（有资源无逻辑；对话统一 border5，不再做 border3）
- [x] **H-LAYER** 设置「显示层级」三档：`top` / `middle` / `bottom`（底部含智能伴侣）
- [x] **H-RPG** 模式→游戏→**RPG**（Silent Oath / `Vpetgame`）独立进程启动；打包同步 `bundled/Vpetgame`
- [x] **H-WALK** 走动顺畅；连续转向锁定 **≤3s**；自由/漫游/音乐/工作同半速步长（`MOVE_STEP=2`，工作用 `light` 位移）
- [x] **H-WORK-VOICE-PACE** 工作（模式/动作）：语音抽检与自由同频（每 24 步、`VOICE_FREE_RANDOM_CHANCE`）；禁止每帧抽音与 30–90s 强制鼓励链
- [x] **H-DRAG-YUQI** 拖动 move 超过 **5s** 强制随机播 `yuqi` 一条（长拖可再触发）；无资源退回台词框
- [x] **H-VOICE-PRELOAD** 特定触发（`yuqi`/eat/kick/sleep/hurt/work/walk/dizzy/call/你好/end）与 **normal 整组**一并 `preload_priority_clips` 提前缓存
- [x] **H-KEYOUT** 精灵抠图**只扣与外圈连通**的键色（边缘泛洪，不伤内色）
- [x] **H-LOAD-FIXED** 入场/出场/加载像素动画**固定风格**（溶解 `radial`、加载 `pulse`），禁止随机换场
- [x] **H-EXPOSE-NOSUB** 暴露失败：hurt 语音**无字幕**；故障反馈不得被全屏 clear 替代
- [x] **H-INTERJECT** 点击脸/躯干/腿触发 `interjection` 部位语音（开语音模式）
- [x] **H-CALL** = V-CALL-01（先 ring 无框 → 非 ring 有框）
- [x] **H-HI** = V-HI-01/02（关：HI_TEXT；开：你好语音与打字框二选一）
- [x] **H-MUSIC-WAVE** 音乐模式脚下光圈：**自主 phase 律动**，不跟曲目 BPM/响度；恢复像素环+底部条（走动 lite 可用）
- [x] **H-PERSONA-JINMU** 面板「人格切换」↔ 金目（`nc*` / `ncstand`）；金目自由随机语音走 `Vpet/jinmu`；默认不抽 jinmu
- [x] **H-STARTUP-SLEEP1** 开场立绘/像素入场**全部用 sleep1**（不占位 stand）；`mode=loading` **禁止走动**；资源与入场结束后再 `_begin_free_after_startup` 进入自由模式
- [x] **H-SLEEP-NO-SHY** 睡眠模式 / 休息睡眠语境：**连击不触发脸红**；非睡眠的面颊双击连击脸红仍保留
- [x] **H-SLEEP-YUQI** 睡眠语境（模式 quiet rest / 动作睡眠）：**多次双击**随机播 `Vpetvoice/Vpet/yuqi` 一条；保持睡眠（可 peek），不唤醒离模
- [x] **H-SLEEP-PEEK-ONLY** 睡眠模式连点：仅 `_rest_peek_sleep1` 短暂睁眼，**不离开关模式**（仍回 rest）
- [x] **H-QUIET-SLEEP-VOICE** 模式→睡眠与互动→动作→睡眠同源播 `sleep` 语音；切入 quiet 后延迟补播，避免模式切换 interrupt 掐声；已在睡眠时再点仍可补播
- [x] **H-MATE-TURN** 智能伴侣跟随朝向防抖：`MINI_PET_TURN_HOLD_MS` + 轴向迟滞，避免斜向/贴身狂切面
- [x] **H-WORK-FLAG-BOX** 工作：终点 **flag** 可拖；起点搬走一箱立刻再生成（持续到结束/箱数搬完）；送达后旗脚堆 **box**；层级：箱 < 旗 < 桌宠；箱点击穿透；旗/箱铺满画布并以 magenta 烘焙透明
- [x] **H-GAME-FALL-VIS** 采集：下落食物 / +3s / -3s / 晕眩物**必须可见**；点透不挡拖；叠在桌宠后但同 display_layer（禁止 `lower` 埋没）
- [x] **H-RPG-DIY-FILE** RPG DIY 底栏：保存 / 导出 / 删除 / 打开；`Ctrl+S` 覆盖保存，导出另存；删文件二次确认
- [x] **H-RPG-DIY-ERASE** DIY 可删除已放素材：底栏「清除」+ 左键擦、任意笔刷右键擦；楼梯/洞窟双层同步清
- [x] **H-RPG-TREE1** RPG 树木：两张 `tree` **横向并排**拼成一图，整体宽高**严格占一格**草地（逻辑仍一格）
- [x] **H-RPG-PORTAL** 地图有洞窟时楼梯仍可用：门户并存；加载修复双层对齐；穿越时同格类型强制一致
- [x] **H-RPG-INTRO-SLOW** RPG Start 页动画变慢（`intro_dur≈6.2`、`logo2_delay≈1.15`、`menu_fade_speed≈0.55`）
- [x] **H-RPG-STARTMUSIC** 点 START 先播 `startmusic`（相对循环 BGM 更响，`STARTMUSIC_VOLUME_MULT≈1.75`），再循环 `music`；可用音量键调节
- [x] **H-RPG-DIY-LAYER** DIY 双层：楼梯/洞窟画一格同步另一层；`Tab` 切地面/地下编辑与试玩穿越
- [x] **H-RPG-DIY-PRINCESS** DIY 底栏「公主」素材可拖放；落点写入 `goal`/`goal_layer`/`princess`
- [x] **H-RPG-DIY-START-CENTER** DIY 加载：未设合法 `start` 时镜头与出生点用地图中心；有起点则对准起点
- [x] **H-WORK-GAME-MUTEX** 工作模式与采集互斥：进入工作硬停采集（清 spawn/tick/HUD/下落窗）；进入采集硬停工作；倒计时结束若已在工作则不再开局
- [x] **H-FOOD-MORE** 背包展示 **全部 18 种**食物（含 ×0）；新增种类首次入库种子 `FOOD_NEW_KIND_SEED=3`；采集随机池同步扩展
- [x] **H-LOCAL-CACHE** 语音/音乐/打字音/工作道具优先本地+`data/` 缓存；天气联网失败回退 `weather_cache.json`；启动 `_seed_local_runtime_assets` 落盘缺文件

### I. 核对结果摘要（代码核验 · 2026-07-16）

| 结论 | 编号 |
|------|------|
| ✅ 已实现 | **A** UI-01～04；**B** P-UI / P-FEED / P-MATE；**C** V-BORDER5 + V-TEXT + V-PICK + D-TYPE；**D** V-CALL / V-HI；**E** V-MODE～V-ADDON；**G** 文档只读；**H** 全段（含 H-WORK-GAME-MUTEX、H-FOOD-MORE、H-LOCAL-CACHE、RPG DIY 双层/公主/起点、工作旗箱/采集可见） |
| ❌ / ⚠️ 未达标 | **G08** 对战失败仍全屏 clear；**M01** 晕眩 1.5s≠3s；**F07** wink 未接 `_show_wink_fx`；**E05** 暴露失败 toast 2.2s≠900ms+打字框 |

---

## 十三、相关文件索引

| 文件 | 用途 |
|------|------|
| `PRE_VOICE_BASELINE.md` | **本文件**：语音前基线 + 最终必做核对表 |
| `IMMUTABLE_FILES.md` | 禁止破坏的函数与语音接入规则 |
| `REQUIREMENTS.md` | 原始需求（只读） |
| `FEATURES.md` | 功能清单（只读） |
| `pet.py` | 主程序实现 |
| `voice_system.py` | 仅语音逻辑 |
| `bundled/Vpetgame/game.py` | Silent Oath RPG |
| `panel_decor.py` | 面板主题色（含不透明内色） |

**最后更新**：2026-07-16（H-WORK-GAME-MUTEX / H-FOOD-MORE / H-LOCAL-CACHE + RPG DIY 双层/公主/起点）
