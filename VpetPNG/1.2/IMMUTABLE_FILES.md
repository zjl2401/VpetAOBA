# 不可修改文件与模块说明

> **重要：以下文件/模块在接入语音、UI 边框等新功能时绝对不能改其既有行为。**  
> 新功能只能以**附加层**方式接入（独立窗口、独立声道、独立回调），不得删除、跳过或替换原有视觉/动画调用。

---

## 一、规格文档（只读对照）

| 文件 | 说明 |
|------|------|
| `PRE_VOICE_BASELINE.md` | **语音前功能基线 + 每次改动强制核对表**（必须逐条验收） |
| `REQUIREMENTS.md` | 功能与视觉规格原文，**禁止改写**其中已实现的动画/特效/对话框规则 |
| `FEATURES.md` | 功能清单，与 `REQUIREMENTS.md` 一致，**禁止删改**已列出的特效描述 |

修改需求时应**新增章节**或另建文档，不得覆盖上述文件中的既有条目。

---

## 二、视觉与动画核心（`pet.py` 内禁止破坏的函数）

以下函数定义了桌宠的全部视觉效果。接入语音、留声、边框等时**必须保留调用顺序与时机**，不得用 `return`、条件分支或新 UI 替代它们。

### 出场 / 入场
- `_draw_size_loading_frame`（含 `reverse` 逆向出场）
- `_run_exit_dissolve_at`
- `_hide_size_loading` / `_show_size_loading`

### 游戏结算动画
- `_show_game_clear` / `_hide_game_clear`
- `_draw_game_clear_frame` / `_spawn_game_clear_particles`

### 互动背景特效
- `_show_interact_fx` / `_hide_interact_fx`（侧踢粒子等）
- `_show_rain_fx` / `_hide_rain_fx`（伤心下雨）
- `_show_bulb_fx` / `_hide_bulb_fx`（有主意灯泡）
- `_show_like_fx` / `_hide_like_fx`（点赞发光）
- `_show_shy_fx` / `_hide_shy_fx`（脸红爱心）
- `_show_wink_fx` / `_hide_wink_fx`（wink 声波）
- `_show_happy_fx` / `_hide_happy_fx`
- `_show_food_fx` / `_hide_food_fx`
- `_start_music_wave_fx` / `_stop_music_wave_fx`
- `_show_follow_dizzy_fx` / `_hide_follow_dizzy_fx`

### 互动台词与打字对话框
- `_show_speech_dialog` / `_hide_speech_dialog` / `_speech_type_next`
- `_layout_speech_dialog` / `_compose_speech_border2`
- `_interact_flair`（**不得**因语音播放而跳过 `show_fx`）

### 暴露 QTE / 故障动画
- `_spawn_expose_glitch_round` / `_animate_glitch_fault`
- `_cancel_expose_qte`
- `_finish_expose_session`：**失败**时必须保留故障界面 + 打字对话框（或语音字幕叠加），**禁止**用全屏 `game_clear` 替代失败反馈
- `_resolve_expose_qte_hit`

### 动作与表情流程
- `_action_animate`、各 `_play_*` / `_after_*` 动作结束回调
- `_interrupt_current_interaction` 中清理 FX 的列表（可新增清理项，**不可删除**既有 `_hide_*_fx` 调用）

---

## 三、UI 资源（禁止替换或删改逻辑）

| 路径 | 用途 |
|------|------|
| `assets/ui/border.png` | 面板九宫格边框素材 |
| `assets/ui/border2.png` | 对话横条 / 语音字幕边框素材 |

边框绘制逻辑（`_nine_slice_border_image`、`_layout_panel_border`、`_speech_border2_*`）**禁止**为语音功能而简化或移除。

---

## 四、语音模块接入规则（`voice_system.py` + `pet.py` 挂钩）

`voice_system.py` 只负责**音频扫描、播放、链式触发**，不得包含 UI 逻辑。

在 `pet.py` 中接入语音时必须遵守：

1. **语音字幕**走 `_show_voice_subtitle` → 独立 `voice_subtitle_win`，**不得**调用 `_show_speech_dialog`（避免打断打字动画与互动台词）。
2. **游戏失败语音**走 `_play_game_fail_voice`，在**原结算/特效已显示之后**附加播放，不得提前 `return` 跳过 `_show_game_clear` 或暴露故障动画。
3. **音效互斥**仅影响 `sfx` 声道；**不得**用 `voice_player.is_busy()` 阻止背景 FX、粒子、game_clear 动画。
4. **练习对战战败**：保留对战界面约 1.6s 后关闭（`after(1600, _close_rhyme_fight)`），**禁止**用全屏结算替代战败画面。

---

## 五、允许修改的范围

- `voice_system.py`：语音目录、播放队列、缓存（不改 `pet.py` 视觉函数）
- `pet.py` 中 `_voice_*` / `_try_voice_*` / `_play_game_fail_voice` / `_show_voice_subtitle` 等**语音专用**挂钩
- `build_app.py` / `Vpet.spec`：打包配置
- `data/app_config.json`：用户配置项（如 `voice_mode`）

---

## 六、自检清单（改代码前）

**完整条目见 `PRE_VOICE_BASELINE.md` 第十二节**，每次发布前必须逐条打勾，不得跳过。

- [ ] 已打开 `PRE_VOICE_BASELINE.md` 并完成第十二节全部核对项？
