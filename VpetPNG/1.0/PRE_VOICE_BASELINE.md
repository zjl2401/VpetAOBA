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
| M01 | 跟随 | 跟鼠标；频繁变向晕眩 **3s** +「我晕了……」/dizzy 语音 | `_follow_tick` / `_start_follow_dizzy` |
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
| D07 | 打招呼 | 关语音：HI_TEXT 扁平打字；开语音且有「你好」：**强制播**（失败回落打字框） | `_show_hi_dialog` / `_try_voice_hi` |
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
| F01 | 开心 | happy 上移 / stand 原位，0.28s×3 轮；身后像素小花钉原位 | 无 | `_play_happy` / `_show_happy_fx`；见 **J-HAPPY-BOUNCE** |
| F02 | 生气 | walkback 上移 + 怒 mark；整窗轻弹 **3** 次 | 有 | `_play_expression_angry`；见 **J-EXPR-BOUNCE** |
| F03 | 伤心 | 头上像素下雨；整窗轻弹 **3** 次 | 有 | `_play_expression_sad` / `_show_rain_fx`；见 **J-EXPR-BOUNCE** |
| F04 | 有主意 | 左上角灯泡亮 → eat2 | 无 | `_play_expression_idea` / `_show_bulb_fx` |
| F05 | 侧踢 | 粒子 3s | 有 banter | `_show_interact_fx` / `_interact_flair("kick")` |
| F06 | 点赞 | 背景像素发光 | 无 | `_show_like_fx` |
| F07 | wink | 爱心声波；仅停约 3s；自由不随机；点一下可恢复 | 无 | `_show_wink_fx` + `H-WINK-FREE-NO` |
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
| S06 | AI 对话 | 入口保留；目前 stub「尚未开发完全」 | `_open_ai_chat_stub` |
| S07 | 留声机 | 系统→我的→回忆→留声；音乐/音效播放与列表 | `_open_phonograph` |
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
- [x] **V-HI-02** 开语音且有「你好」资源：**强制播**；失败回落 HI_TEXT；动作结束不杀仍在播的语音框

### E. 语音规则与场景触发
- [x] **V-MODE** 设置里可开关；关=去掉电话语音轨，保留音效/音乐
- [x] **V-MIX** 音效与语音互斥；音乐与二者均可共存
- [x] **V-CHAIN-NUM** Vpet 数字前缀 → 有伴侣时接 Allmate 同号
- [x] **V-CHAIN-ALPHA** Allmate 字母前缀 → 接 Vpet normal 同字母
- [x] **V-CD** 整段会话结束后 ≥10s 再触发下一段（链式对答算一段）
- [x] **V-SCENE** eat/sleep/kick/call/hi/end 等专项优先于自由随机；有专用资源时**强制播**（不被 50/50 打字框整段盖掉）；interrupt 后延后补播；stop 作废旧异步回调防抢声道
- [x] **V-FREE** 自由：normal/forget/dizzy/jinmu；（有伴侣）+ren；error 长间隔
- [x] **V-WALK/WORK** walk / work 随机
- [x] **V-HUNGRY** 体力低 hungry（开语音且有资源时**强制播**）
- [x] **V-EMAIL** 点对话 email
- [x] **V-GAME** 关于 game；莱姆开始前 laimu open
- [x] **V-HURT** 游戏失败 hurt（**只附加**，原结算画面保留）— 采集（错过≥接住或 0 接）/打字 D·C / 音游 D·C / 背词错 / 暴露失败；延迟补播+可重试；`ignore_cooldown` **不得**误掐 hurt；**对战失败受 G08 牵连**
- [x] **V-DIZZY** 采集晕眩物 / 跟随急转晕眩：开语音播 `dizzy`（保留晕眩特效）
- [x] **V-END** 退出：`end` 与出场同步，时长由语音决定；结束后彻底退出（可超时强制退）
- [x] **V-ADDON** 语音附加层不得 `return` 跳过原动画/结算/特效

### F. 基线动画 / 特效 / 暴露 / 出场
- [x] B01–B11 / M02–M08 / G01–G07 与基线表大体一致（2026-07-16 代码抽检）
- [x] **G08** 练习对战失败：保留对战界面 ~1.6s 后关闭（非全屏 clear）；hurt 附加
- [x] **M01** 跟随晕眩 **3s**（`FOLLOW_DIZZY_STAND_MS=3000`）
- [x] **F07** wink 专用特效 `_show_wink_fx`（爱心声波；点赞仍 `_show_like_fx`）；**仅停约 3s**（`WINK_DURATION_MS=3000`）；**自由模式不随机触发**；卡住时**点一下**强制恢复；结束后恢复站立/走动
- [x] **H-WINK-3S** wink：无 banter；声波特效点击穿透；自由随机/心情池**排除 wink**；菜单可手动 wink；点一下/`_force_end_wink_like`/看门狗恢复
- [x] **E05** 暴露失败：故障界面保留约 **900ms** + 打字「暴露失败…」；hurt 无字幕（H-EXPOSE-NOSUB）
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
- [x] **H-DRAG-YUQI** 拖动 move 超过 **3s** 强制随机播 `yuqi` 一条（长拖可再触发）；无资源退回台词框
- [x] **H-VOICE-PRELOAD** 特定触发（`yuqi`/eat/kick/sleep/hurt/hungry/work/walk/dizzy/call/你好/end）与 **normal 整组**一并 `preload_priority_clips` 提前缓存
- [x] **H-VOICE-TRIM-CACHE** 语音**只去开头静音**（保留结尾）+ loudnorm，写入 `*_p4.wav`；**处理过一次后直接读缓存，不再二次 ffmpeg**；声音设置可调 `voice_volume` 并持久化
- [x] **H-SIZE-ALLMATE** 设置桌宠大小：**七档按钮**（特小/小/中小/中/中大/大/特大，**无滑条**）；主宠与 Allmate **并行预热、同帧切换**；有 Allmate 时一起缩放
- [x] **H-KEYOUT** 精灵抠图**只扣与外圈连通**的键色（边缘泛洪，不伤内色）
- [x] **H-LOAD-FIXED** 入场/出场/加载像素动画**固定风格**（溶解 `radial`、加载 `pulse`），禁止随机换场
- [x] **H-EXPOSE-NOSUB** 暴露失败：hurt 语音**无字幕**；故障反馈不得被全屏 clear 替代
- [x] **H-INTERJECT** 点击脸/躯干/腿触发 `interjection` 部位语音（开语音模式）
- [x] **H-CALL** = V-CALL-01（先 ring 无框 → 非 ring 有框）
- [x] **H-HI** = V-HI-01/02（关：HI_TEXT；开且有「你好」资源时**强制播**，失败回落打字框）
- [x] **H-MUSIC-WAVE** 音乐模式脚下光圈：**自主 phase 律动**，不跟曲目 BPM/响度；恢复像素环+底部条（走动 lite 可用）
- [x] **H-PERSONA-JINMU** 面板「人格切换」↔ 金目（`nc*` / `ncstand`）；金目自由随机语音走 `Vpet/jinmu`；默认不抽 jinmu
- [x] **H-STARTUP-SLEEP1** 开场立绘/像素入场**全部用 sleep1**（不占位 stand）；`mode=loading` **禁止走动**；资源与入场结束后再 `_begin_free_after_startup` 进入自由模式
- [x] **H-SLEEP-NO-SHY** 睡眠模式 / 休息睡眠语境：**连击不触发脸红**；非睡眠的面颊双击连击脸红仍保留
- [x] **H-SLEEP-YUQI** 睡眠语境（模式 quiet rest / 动作睡眠）：**多次双击**随机播 `Vpetvoice/Vpet/yuqi` 一条；保持睡眠（可 peek），不唤醒离模
- [x] **H-SLEEP-PEEK-ONLY** 睡眠模式连点：仅 `_rest_peek_sleep1` 短暂睁眼，**不离开关模式**（仍回 rest）
- [x] **H-QUIET-SLEEP-VOICE** 模式→睡眠与互动→动作→睡眠同源播 `sleep` 语音；切入 quiet 后延迟补播，避免模式切换 interrupt 掐声；已在睡眠时再点仍可补播
- [x] **H-MATE-TURN** 智能伴侣跟随朝向防抖：`MINI_PET_TURN_HOLD_MS` + 轴向迟滞，避免斜向/贴身狂切面
- [x] **H-WORK-FLAG-BOX** 工作：旗/箱 **Tk magenta 色键抠外围**（禁止露玫红/深蓝底）；先设色键再分层；点透只拨 `WS_EX_TRANSPARENT`
- [x] **H-GAME-FALL-VIS** 采集：Pillow 食物放大（~size/5）；特殊物裁边；`_force_chroma_key_rgb` 去粉边；色键同旗箱
- [x] **H-WIN32-MAGENTA-KEY** 色键建窗设一次即可；**禁止**每帧 clear→重设 `-transparentcolor`（会闪玫红）；采集热路径只 `lift`；工作：拖宠/到站不重建旗面、起点箱 withdraw 复用、桌面钟增量重绘
- [x] **H-RPG-DIY-FILE** RPG DIY 底栏：保存 / 导出 / 删除 / 打开；`Ctrl+S` 覆盖保存，导出另存；删文件二次确认
- [x] **H-RPG-DIY-ERASE** DIY 可删除已放素材：底栏「清除」+ 左键擦、任意笔刷右键擦；楼梯/洞窟双层同步清
- [x] **H-RPG-TREE1** RPG 树木：两张 `tree` **横向并排**拼成一图，整体宽高**严格占一格**草地（逻辑仍一格）
- [x] **H-RPG-PORTAL** 地图有洞窟时楼梯仍可用：门户并存；加载修复双层对齐；穿越时同格类型强制一致
- [x] **H-RPG-INTRO-SLOW** RPG Start 页动画变慢（`intro_dur≈6.2`、`logo2_delay≈1.15`、`menu_fade_speed≈0.55`）
- [x] **H-RPG-STARTMUSIC** 点 START（战役）立刻播 `startmusic`（文件已响度归一；播放音量≈0.95），结束后循环 `music`（默认约 **0.05**）；可用音量键调节循环音量
- [x] **H-RPG-DIY-LAYER** DIY 双层：楼梯/洞窟画一格同步另一层；**首次放置后新增左侧「地下」层页面**；`Tab`/点页签切地面/地下
- [x] **H-RPG-KIND-SELECT** 加载 DIY / 试玩前选角页三选一：**knight** / **Vpet(下方文字 aoba)** / **Allmate(下方文字 ren)**；立绘**抠除外圈背景**；游玩中 **C** 切换；Vpet 用 `assets/vpet` 行走图，Allmate 用 `assets/allmate` 行走图
- [x] **H-RPG-CHEST-SFX** 打开宝箱：本关宝箱数 +1，并播放获得奖励音效（`sfx_reward.wav`，缺则合成）
- [x] **H-RPG-DIY-PRINCESS** DIY 底栏「公主」可拖放；落点写入 `goal`/`goal_layer`/`princess=True`（到公主通关）；右键/清除擦公主格 → `princess=False` 自由探索、不通关；新 DIY 默认无公主
- [x] **H-RPG-DIY-START-CENTER** DIY 加载：未设合法 `start` 时镜头与出生点用地图中心；有起点则对准起点
- [x] **H-RPG-DIY-START-BLUE** DIY 起点用**蓝框**标记操控小人出生格（底栏「起点」笔刷同色；编辑器地图上半透明蓝填充+蓝描边）
- [x] **H-RPG-ALLMATE-SHEET** Allmate(ren) 操控小人：`assets/allmate` 的 petstand/petfront/petback/petleft（抠绿底）
- [x] **H-WORK-GAME-MUTEX** 工作模式与采集互斥：进入工作硬停采集（清 spawn/tick/HUD/下落窗）；进入采集硬停工作；倒计时结束若已在工作则不再开局
- [x] **H-FOOD-MORE** 背包展示 **全部 18 种**食物（含 ×0）；新增种类首次入库种子 `FOOD_NEW_KIND_SEED=3`；采集随机池同步扩展
- [x] **H-LOCAL-CACHE** 语音/音乐/打字音/工作道具优先本地+`data/` 缓存；天气联网失败回退 `weather_cache.json`；启动 `_seed_local_runtime_assets` 落盘缺文件
- [x] **H-DEMO-GUIDES** 录实况可用 `DEMO_ALWAYS_SHOW_GUIDES=True`；**正式/公开包为 `False`**（仅首次弹操作说明）
- [x] **H-HINT-TOAST** 玩法说明 / RPG 宝箱·小屋·关卡等**说明类**文案用 toast，不对白文本框打断操作；角色台词/系统对话仍可走文本框
- [x] **H-STARTUP-WARMUP-HINT** 首次启动：留出预热时段并显示**给人看的**等待文案（非提示词腔）；开场预热（时钟/工作/采集/语音/多尺寸/自由走动）错开执行
- [x] **H-VOICE-FORCE-SCENE** 开语音且有资源时强制播：`hurt`（游戏失败）/`dizzy`（采集晕眩·跟随晕眩）/`call`/`你好`/`eat`/`hungry`（不再 50/50 丢掉）
- [x] **H-ABOUT-FREE** 操作说明 / 关于标明**免费**；署名用「**作者**：翛然而往」（不用「作者菌」），更小字贴在面板**下方角落**
- [x] **H-RPG-DIY-NOMUSIC** 加载 DIY / 自建地图试玩（`campaign=False`）**不放**冒险 BGM；仅战役 START 播音乐
- [x] **H-RPG-PLAYER-KIND** 游玩中 **C** 切换：**knight / aoba(Vpet·`assets/vpet`)** / **ren(Allmate·`assets/allmate`)**；WASD 可控移动
- [x] **H-RPG-SPAWN-WALK** 出生/起点/读档落点若在湖/墙等不可走格，自动挪到最近可走格；DIY 放起点同规则
- [x] **H-WINK-3S** wink 仅停约 **3s**；**自由模式不随机 wink**；卡住时点一下恢复；看门狗 `_force_end_wink_like` 兜底
- [x] **H-WINK-FREE-NO** 自由：心情池与 `_try_free_random_action` **不抽 wink**；互动菜单「wink」仍可用
- [x] **H-OWNER-ONCE** 去掉桌宠编号（正式包 `PET_ID_FEATURE=False`）；改为**所属人昵称**：启动后强制弹窗填写，**不可跳过**；仅可填一次、不可更改；重置也**不得**改动所属人
- [x] **H-OWNER-FRONT** 所属人取名窗必须置顶可见：禁止 `transient` 到无边框主窗；强制 `-topmost`；不参与底部层级下压；`_keep_owner_name_win_front` 防启动刷新盖住
- [x] **H-OWNER-THEN-GUIDE** 启动顺序：**先所属人 → 填完后再弹首次操作说明**；取名确认后**强制**弹一次（忽略旧包已写的 `seen_hints.operation_guide`）；另用 `post_owner_guide` 保证「已取名但未走过取名后说明」的老存档补弹一次；之后启动不再弹；**所属人与操作说明仅首次出现**
- [x] **H-BDAY-SET** 互动→工具→生日祝福→**设定日期**：月/日 + 祝福语；到日触发文本框「生日快乐，+祝福语」（同日最多一次）
- [x] **H-BDAY-GIFT** 互动→工具→生日祝福→**赠送礼物**：输入礼物文本；每年 **4/22**（桌宠生日）触发俏皮感谢（含所属人昵称、第几个生日、礼物名；同日最多一次）
- [x] **H-RESET-OWNER** 恢复初始：清空设置/存档/生日礼物等，**仅保留所属人**（及登记时间）
- [x] **H-NO-LEADERBOARD** 模式→游戏菜单**去掉「持有者排名」**（无编号公开包不再入口）
- [x] **H-MEMORIES-UNDER-MY** 回忆（画廊/留声）在 **系统→我的→回忆**，不在系统根菜单
- [x] **H-DAILY-LOGIN-COIN** 每天首次打开桌宠登录礼 **+1 金币**（`wallet.last_daily_coin_ymd`，同日仅一次）
- [x] **H-OWNER-STATS** 我的→所属人：显示**相伴天数**、**相伴时长**（各模式合计）；可点「查看详细」展开一起听歌/工作/跟随/漫步/自由/睡眠/游戏；须有 `owner_set_at` 登记时间；时长靠 `achievements.stats.mode_seconds` 累计
- [x] **H-OWNER-LAUNCH-GREET** 启动问候：首次认主欢迎词；约超 3 天未开则「好想你」类台词（走生日问候链路 `_maybe_owner_launch_greeting`）
- [x] **H-COMMUNITY-MENU** 系统→社区：**关于 / 问题反馈 / 投稿创意 / 操作说明**；「投稿与创意」改名「投稿创意」；操作说明不在系统根菜单（F1 仍可开）
- [x] **H-TOOL-CLOCK-CTRL** 互动→工具打开的秒表：**开始/暂停/结束**；计时器：**开始/暂停/关闭**；默认暂停待点开始；睡眠/音乐/工作自动时钟**不加**按钮；**暂停/开始须真实可用**
- [x] **H-TOOL-POMODORO** 互动→工具→番茄钟：设定工作/休息分钟；工作=定时运送，休息=睡眠+倒计时，循环；轮次 toast（满 4 轮额外提示）；任一阶段可「结束」；再点菜单可取消；休息倒计时小人与睡眠模式秒表小人一致
- [x] **H-WORK-REWARD-BOX** 生涯累计每满 25 箱发 `work_reward_box` 进背包；点击开启随机金币/经营物资；toast 带进度与分档（小收获/不错/好运）
- [x] **H-HOME-UI-HANDY** 家园左栏：区切/模式/经营工具固定；「更多」折叠存档·移动·配色；室内「去经营」；记住上次编辑模式；导出开创作导出中心
- [x] **H-CLOCK-WALKER-GREEN** 秒表/计时器绕圈小人抠掉与边缘连通的**绿色外圈**（`desktop_clock._remove_outer_green`）
- [x] **H-AI-INVITE-STUB** 互动→对话→AI 对话、面板→邀请：现阶段 toast「尚未开发完全」（完整版见 **K**）
- [x] **H-FARM-TOOLS-V2** 家园经营：1锄2种3浇4收5砍6钓7采；草地锄两下成田；成熟度100/时+5；浇水每天≤2、浇后1h×2；砍树掷骰；水面钓鱼；采花可插室内花瓶；锄地无「锄」字特效
- [x] **H-HOME-UI-SPLIT** 家园面板：窗口加大、格 32px；左栏操作 / 右栏房间
- [x] **H-RPG-DIY-EXPORT** RPG DIY：编辑器保存/导出、Ctrl+S / Shift+S；副本 `%LOCALAPPDATA%\Vpet\userdata\exports\`
- [x] **H-RPG-DIY-PICKUPS** DIY 笔刷：金币 / 加速蘑菇 / 无敌星；开局收成 pickups（有放置则不随机刷）
- [x] **H-RPG-TRAP-FAINT** RPG 陷阱：游玩默认极淡，踩中后显示完整；编辑器始终完整
- [x] **H-RPG-PALETTE-GREEN** DIY 底部素材栏：地物/公主/自创画抠外圈绿幕→透明（`flood_key` 清成 0,0,0,0；缩放后再抠；预览用棋盘格显透明底）
- [x] **H-CREATOR-UPLOAD** 投稿创意：分模块勾选 +「仅打包新增」；首次弹投稿包说明；**zip 直接放到本机桌面**；文件名含致谢署名（若有）与内容模块；自行上传反馈通道（大文件可发网盘链接）；操作说明有「导出与投稿」专题；像素画「取色」自选颜色；**投稿即默认同意无偿公开**
- [x] **H-WORK-DEST-FOOT** 工作运送：**旗脚 = 实际终点**（`work_end` 存旗脚屏幕坐标）；拖旗则终点跟着变；送达以脚底靠近旗脚判定
- [x] **H-WORK-FREE-END** 工作·**自由**：持续运送；有「结束」键，贴旗脚旁并随旗/终点移动；点结束回自由；模式/互动入口相同；结束键中间方块为**白色**
- [x] **H-WORK-CUSTOM-AUTO** 工作·**自定义**：箱数或时间二选一；**无**结束键；到量/到点自动回自由；模式/互动入口相同；终点同样跟旗脚
- [x] **H-WORK-PROPS-SETTING** 仅 **模式→工作→设置** 可开关「显示目的地（旗）」「显示运送货物（箱）」
- [x] **H-WORK-DRAG-HANDLE** 可拖旗时提供实心「终点（可拖）」拖柄（色键旗窗点不到时仍可拖）；拖柄/旗/结束钮叠在桌宠之上；**进工作瞬间旗与可拖终点须贴桌宠**（禁止甩在屏幕左上角）
- [x] **H-MODE-WAIT-HINT** 切模式 / 进工作 / 启动等须先刷出等待条；文案为**使用者语言**（如「切换模式中」），禁止「请耐心等待…」提示词腔
- [x] **H-MODE-TOTAL-PERSIST** 模式累计时长（工作/睡眠/音乐等）写入成就 default 并加载合并，禁止更新后从头丢弃；可用 `mode_seconds` 回填

### J. 2026-07-26 之后会话追加（写入必做 · 逐条核对）

> 下列为正式发布前陆续提出的**最终规格**。打包前须核对；**缺项不得按已完成发布。**

#### J1. 场景检测 / 音乐 / 伴侣
- [x] **J-SCENE-GAME-VIDEO** 检测到使用者在**玩游戏 / 刷视频**时切对应原地动画（`play_game*` / `watch_video*`，外圈绿幕抠图；游戏/视频侧道具位与滑动换色效果按既定资源）；**非独立菜单模式**，是检测切换
- [x] **J-MUSIC-HOLD** 环境识别为音乐后须**持续留在音乐模式**；放完一首换下一首**不得**因此退出；暂停时桌宠与智能伴侣音乐背景特效暂时去掉，恢复播放再回来
- [x] **J-MATE-HEART** 多次开启智能伴侣：送爱心飞向莲；送完后再触发开心等正向表情；开伴侣时的开心不得掐断莲的加载
- [x] **J-HOLD-ALLMATE** 多次点伴侣抱起：桌宠**先走到伴侣身后**再切抱姿图；移速与切图速度保持既定，不额外变慢/加快；约 3s 恢复
- [x] **J-SPEECH-LAYER** 对话/语音文本框在桌宠与智能伴侣**下层**；禁止频闪；叠层规则稳定

#### J2. 语音 / 设置 / 性能
- [x] **J-VOICE-INTERVAL** 语音触发间隔设置（含约 10s 等档）须真实生效；档位拉开；改档清冷却；自由走路也可触发；到点优先于表情
- [x] **J-VOICE-STICKY** 语音模式开启后不得无故静默失效（需再到设置重开）；异常时自愈或明确可感知状态
- [x] **J-META-DARK** Meta「屏幕暗了」类台词：仅灭屏/变暗/屏保后触发；订阅显示器电源；亮屏闲置不得乱说
- [x] **J-SIZE-7BTN** 桌宠大小：**七档按钮**即时切换（无滑条）；点一下就要开始切；可先停自由再切完恢复；切尺寸可用 sleep 类替位；预热优先
- [x] **J-SETTINGS-PREWARM** 设置相关（大小/字体等）启动期预热；改字体后面板须能看出变化且尽量不卡
- [x] **J-STARTUP-PERF** 首次启动可加长预热并出文案；自由走动帧预热；右键菜单不得把桌宠「卡没」；操作说明滚动/取名输入须可操作
- [x] **J-STARTUP-SLEEP-BUDGET** 首次预热可约十几秒；**非首次** sleep 占位目标 **15s 内**（走动帧齐即结束；硬上限 `STARTUP_REPEAT_TO_FREE_CAP_MS`）
- [x] **J-STARTUP-SFX-TYPE** 开场音效与打字机动画须保留/可恢复
- [x] **J-GUIDE-COPY** 操作说明专题文案简洁、像说明书不像提示语；转换/等待 toast 用给人看的话

#### J3. 装扮 / 家园 / RPG 素材
- [x] **J-OUTFIT-USER-ART** 装扮可选**全部**自创画（RPG/装扮/礼物/家园来源均持久保存）；禁止栏目只留一张、后画覆盖前画；装扮页浅色底
- [x] **J-RPG-PALETTE-SCROLL** RPG 地图编辑底栏素材可用左右键滑动选择；自创画**不要草地底**；自创画可命名（非只能默认名）；点选须对应正确素材（禁止点 A 出 B）
- [x] **J-HOME-COLOR** 家园家具：**每个家具单独改色** + 自选色显示且可用；室外场景底不要透明；画素材底栏按钮随字体放大
- [x] **J-HOME-ACTION-TIP** 家园床/椅等动作提示贴家园窗旁 + 小人头顶，不居中 toast；自由/操控均可随机动作表情
- [x] **J-THEME-PAGES** 家园 / 装扮 / 日程 / 所属人 / 生日祝福等页：纸质功能向背景（对齐日记）；日程可加闹钟暗纹；生日可加蛋糕暗纹；赠送礼物背景按既定恢复

#### J4. 工具 / 暴露 / 莱姆 / 其它互动
- [x] **J-CLOCK-LOOK** 时间工具底轻微透明（勿过透）；音乐栏按钮略透；绕圈小人后有蓝色像素流星尾迹；音乐模式时钟勿被光圈挡住
  - 时钟 Z 序：桌宠背景特效之上、立绘之下（`_restack_display_z`）
  - 音乐时钟 `glass=DESK_CLOCK_BTN_TRANSPARENCY`（禁止未定义变量导致「界面异常已拦截」）
- [x] **J-SCHEDULE-FIRE** 日程提醒须在设定时间**真实提醒**
- [x] **J-DIARY-FLIP** 日记顶装订圆环；过往页单页翻页；报讯时勿异常红字
- [x] **J-SLEEP-ZZZ** 睡眠模式背景 Zzz 效果须在
- [x] **J-EXPOSE-BLUE** 暴露故障窗：蓝色；开局数量约 **12**、完美通关可再加、上限约 **28**；散落更密；成功结算去掉「故障清光」那行
  - 常量：`EXPOSE_TAPS_FIRST=12` / `EXPOSE_TAPS_MAX=28` / `EXPOSE_FAULT_START=12` / `EXPOSE_FAULT_MAX=28`
- [x] **J-RHYME-PACING** 莱姆：单次作用点数加大、对局勿过久；开场语音保留；减少卡顿
- [x] **J-YESNO-KEY** 判断「是/否」立绘：`no.jpg` 与 `yes.jpg` **同样**抠外圈青草绿幕（禁止「否」留绿底）
- [x] **J-HAPPY-BOUNCE** 开心：多段上下跳动须可用（勿被音乐/场景门禁整段掐掉）
  - **切图**：`happy` ↔ `stand`（`sprites.happy[0]` / `sprites.stand`；缺 happy 时回退 `happy.jpg`）
  - **位移**：切 happy 时 `happy_bounce_offset = -HAPPY_BOUNCE_PX`（14px），切 stand 时回 0；与切图同帧；无需额外动态缓动
  - **节奏**：每张 `HAPPY_HALF_MS=280`；共 `HAPPY_CYCLES=3` 轮（交替 3 次）
  - **实现**：`_place_window(light=True)` 只移立绘；背景小花不跟 `happy_bounce`；禁止完整 place/lift 把位移冲掉
  - **锚点**：`_play_happy` / `_happy_bounce_up` / `_happy_bounce_down`
- [x] **J-EXPR-BOUNCE** 表情弹动次数：开心 / 伤心 / 生气 = **3 次**；其余表情（疑问/有主意/点赞/比心/wink/脸红等）= **1 次**
  - 伤心/生气：`_play_expression_pop(times=3)`（`click_bounce_offset`）
  - 其余走 `_play_expression_pop()` 或 wink/shy 专用单次弹
- [x] **J-IDLE-QUICK** 动作/表情/模式等结束后尽快回自由走动（`_resume_idle(quick=True)`）；减卡顿不得靠砍功能；常态站立间隔略缩短（`STAND_IDLE_*`）
- [x] **J-WINK-BOUNCE** wink：触发时整窗弹跳一下
- [x] **J-SHY-BOUNCE** 脸红：出现与连点加深时均弹跳一下
- [x] **J-GALLERY-LOOK** 画廊：画展墙/地板背景；预览与缩略金色像素画框
- [x] **J-PHONO-LOOK** 留声：点播不整表刷新；音乐厅背景 + 像素留声机顶栏
- [x] **J-EMOTE-RATE** 各类动作/表情触发频率可略提高（含家园）
- [x] **J-CLEAN-PACK** 公开干净包：无手机版、无个人路径/隐私信息；打包前关旧进程

#### J5. 手机版（并行工程 · 对照电脑必做项）
- [x] **J-MOBILE-DEMO** 手机版可展示 demo；**千粉后**再正式制作完整版（产品节奏，非本桌面包阻塞项）
- [ ] **J-MOBILE-ALIGN** 手机与电脑对齐的剩余项：伴侣正面/侧面抠图同高、开心跳起显示完整、看视频/听音乐为**检测切换**非菜单模式、面板按电脑整理等（见 `VpetMobile` 清单；未齐项打包前在手机侧单独核对）

#### J6. 2026-08-14 会话追加（启动体感 / 开心节奏 / 时间显示 / 干净包）

- [x] **J-SPAWN-FEEDBACK** 点快捷方式/托盘出宠：立刻「正在打开桌宠…」反馈；首次 spawn **不**空等 1.4s（仅连点错开）
  - 锚点：`vpet_launcher._show_spawn_feedback` / `spawn_pet`
- [x] **J-STARTUP-ENTRANCE** 开场原地加载动画须可见：像素聚拢 + 早摆窗脉冲；资源就绪后可提前收束，但禁止 0 帧掐掉
  - 最短可见：`STARTUP_ENTRANCE_VISIBLE_MIN_MS` / `STARTUP_MIN_MS`；`abort` 至少先画若干帧
- [x] **J-STARTUP-SLEEP-BUDGET**（见上）非首次 sleep 占位目标 **15s 内**
- [x] **J-HAPPY-BOUNCE**（见上）happy↔stand、0.28s×3、只移立绘
- [x] **J-CLOCK-GLASS** 音乐时钟媒体键须定义 `glass`；未定义会炸 toast「界面异常已拦截」
- [x] **J-CLEAN-ZIP** 干净电脑版：`build_app.py --zip` → 桌面 `Vpet_update_时间戳.zip`（已 scrub 个人存档）

#### J7. 2026-08-14 切模式/动作清背景特效

- [x] **J-FX-CLEAR-ON-SWITCH** 切模式、切动作/表情/功能时，须去掉**前一**模式/动作/表情/功能的背景特效（开心花、雨、灯泡、点赞/害羞/眨眼/比心、互动粒子、晕眩、礼物像素、喂食粒子等）；音乐光圈随音乐开停；佩戴花常驻不随打断销毁
  - 锚点：`_clear_all_action_fx`（补 happy/food）；`_mode_switch_light_prepare` 轻量切模式也清特效；`_interrupt_current_interaction` 统一走清特效
- [x] **J-TIMERS-OFF** 设置「时间显示」关：去掉睡眠/音乐/工作（自由）**秒表面**（数字+绕圈小人）；工具秒表/计时器/番茄与自定义·番茄倒计时仍可用
  - 锚点：`_set_timers_display` / `_sync_auto_desk_clocks`
- [x] **J-MUSIC-MEDIA-KEEP** 音乐模式关「时间显示」时：**只关秒表，保留**下方媒体键 ⏮ ⏯ ⏭ ⏹；开显示则秒表+媒体键同窗
  - 锚点：`_start_desk_clock(show_timer_face=…)` / `_sync_auto_desk_clocks`
- [x] **J-DIFFICULTY-SETTING** 设置页「游戏难度」滑条 + 低/中/高可调，写入 `difficulty_t` 并 `_apply_difficulty_runtime`（接食物/暴露/对战等）

### K. 完整版目标（必做 · 尚未完成）

> 菜单可先占位，但下列为**最终要实现**的功能，未完成前不得对外宣称「已完整」。

- [ ] **K-AI-CHAT** AI 对话完整版（非 stub toast）
- [ ] **K-INVITE** 跨电脑邀请 / 联机相关完整版（非 stub toast）
- [ ] **K-RHYME-ONLINE** 莱姆真·联机对战（房间匹配与状态同步）
- [ ] **K-CLOUD-SAVE** 整包云端存档（若产品确认要做）
- [ ] **K-GAME-HISTORY** 个人游戏历史明细页
- [ ] **K-VIDEO-ASR** 视频 ASR 自动抽词进词库（可选增强）
- [ ] **K-RHYME-SPRITE** 莱姆独立立绘精灵

### I. 核对结果摘要（代码核验 · 2026-08-14）

| 结论 | 编号 |
|------|------|
| ✅ 已写入必做 | **A～H**；**J1～J4**；**J6**；**J7**（切模式清特效 / 时间显示关秒表留媒体键 / 难度设置） |
| ✅ 本轮已修对齐 | **J-EXPOSE-BLUE**；**J-CLOCK-LOOK**；**J-CLOCK-GLASS**；**J-TIMERS-OFF**；**J-MUSIC-MEDIA-KEEP** |
| ⚠️ 手机对齐 | **J-MOBILE-ALIGN**（手机工程持续对照） |
| ❌ 完整版未做 | **K-AI-CHAT** / **K-INVITE** / **K-RHYME-ONLINE** / **K-CLOUD-SAVE** / **K-GAME-HISTORY** / **K-VIDEO-ASR** / **K-RHYME-SPRITE** |
| 公开包 | `DEMO_ALWAYS_SHOW_GUIDES=False`、`PET_ID_FEATURE=False`；干净包无个信、默认无手机版 |

---

## 十三、相关文件索引

| 文件 | 用途 |
|------|------|
| `PRE_VOICE_BASELINE.md` | **本文件**：语音前基线 + 最终必做核对表（含 H / J / K） |
| `IMMUTABLE_FILES.md` | 禁止破坏的函数与语音接入规则 |
| `REQUIREMENTS.md` | 原始需求（只读） |
| `FEATURES.md` | 功能清单；暂未实现与必做维护指针 |
| `pet.py` | 主程序实现 |
| `desktop_clock.py` | 桌面秒表/计时器绘制 |
| `vpet_launcher.py` | 托盘启动器 / spawn 反馈 |
| `build_app.py` | 打包；`--zip` 干净电脑版 |
| `voice_system.py` | 仅语音逻辑 |
| `bundled/Vpetgame/game.py` | Silent Oath RPG |
| `panel_decor.py` | 面板主题色（含不透明内色） |
| `VpetMobile/` | 手机并行工程（J5 / 千粉正式版节奏） |

**最后更新**：2026-08-14（J7：切模式清特效；时间显示关秒表留音乐媒体键；难度设置）
