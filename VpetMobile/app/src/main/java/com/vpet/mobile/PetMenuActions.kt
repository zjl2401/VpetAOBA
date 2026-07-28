package com.vpet.mobile

import android.content.Context
import android.widget.Toast

/**
 * 菜单项执行：READY 接能力；STUB「尚未开发完全」。
 */
class PetMenuActions(
    private val context: Context,
    private val animator: PetAnimator,
    private val hub: PetModeHub,
    private val onResize: (() -> Unit)? = null,
    private val onExitOverlay: (() -> Unit)? = null,
) {
    fun run(id: String): Boolean {
        when {
            id.startsWith("dialog_q_") -> {
                val i = id.removePrefix("dialog_q_").toIntOrNull() ?: return false
                val entry = PresetDialogs.all.getOrNull(i) ?: return false
                hub.playPresetDialog(entry)
            }
            else -> when (id) {
                "mode_free" -> hub.startFree()
                "mode_stroll", "act_walk" -> hub.startStroll()
                "mode_follow" -> hub.startFollow()
                "mode_quiet" -> hub.startQuiet()
                "act_sleep" -> hub.startSleepInteract()
                "mode_music" -> hub.startMusic()
                "act_stand" -> hub.playAction("act_stand")
                "act_hi" -> hub.playAction("act_hi")
                "act_squat", "act_kick", "act_yes", "act_no", "act_call", "act_eat", "act_judge",
                -> hub.playAction(id)
                "act_adult", "dialog_ai", "panel_invite" -> toast("尚未开发完全")
                "game_type", "game_vocab" -> toast("手机版跳过打字/背单词")
                "expr_happy", "expr_sad", "expr_shy", "expr_wink", "expr_like",
                "expr_angry", "expr_idea", "expr_question", "expr_bixin",
                -> hub.playExpression(id)
                "work_free", "act_work" -> hub.startWorkFree()
                "work_n3" -> hub.startWorkBoxes(3)
                "work_n5" -> hub.startWorkBoxes(5)
                "work_n8" -> hub.startWorkBoxes(8)
                "work_t1" -> hub.startWorkTimed(60_000L)
                "work_t3" -> hub.startWorkTimed(180_000L)
                "work_t5" -> hub.startWorkTimed(300_000L)
                "work_end" -> hub.endWork(fromMenu = true)
                "work_show_props" -> hub.toggleWorkShowProps()
                "work_show_stack" -> hub.toggleWorkShowStack()
                "tool_sw" -> hub.showStopwatch()
                "tool_timer_1" -> hub.showTimer(1)
                "tool_timer_5" -> hub.showTimer(5)
                "tool_timer_10" -> hub.showTimer(10)
                "tool_pomo_25_5" -> hub.startPomodoro(25, 5)
                "tool_pomo_15_5" -> hub.startPomodoro(15, 5)
                "tool_pomo_1_1" -> hub.startPomodoro(1, 1)
                "tool_pomo_end" -> hub.endPomodoro(silent = false)
                "tool_schedule", "tool_bday_set", "tool_archive", "sys_sync" -> hub.openTools()
                "panel_open" -> hub.openPanel()
                "panel_companion" -> hub.toggleCompanion()
                "panel_persona" -> hub.togglePersona()
                "panel_home" -> hub.openHome()
                "panel_rhyme" -> hub.openRhyme()
                "panel_expose" -> hub.openExpose()
                "game_collect" -> hub.openCollect()
                "game_rhythm" -> hub.openRhythm()
                "game_rpg" -> hub.openRpg()
                "sys_owner" -> hub.showOwnerInfo()
                "sys_diary" -> hub.openSystemPage("diary")
                "sys_achievements" -> hub.openSystemPage("achievements")
                "sys_gallery" -> hub.openSystemPage("gallery")
                "sys_phonograph" -> hub.openSystemPage("phonograph")
                "sys_settings_page" -> hub.openSystemPage("settings")
                "sys_about" -> hub.openSystemPage("about")
                "sys_feedback" -> hub.openSystemPage("feedback")
                "sys_submit" -> hub.openSystemPage("submit")
                "sys_guide" -> hub.openSystemPage("guide")
                "sys_reset" -> hub.openSystemPage("reset")
                "set_size_s" -> applySize("小")
                "set_size_m" -> applySize("中")
                "set_size_l" -> applySize("大")
                "set_font_s" -> applyFont("小")
                "set_font_m" -> applyFont("中")
                "set_font_l" -> applyFont("大")
                "set_font_xl" -> applyFont("特大")
                "set_sound" -> {
                    AppDataStore.setSoundOn(context, !AppDataStore.soundOn(context))
                    toast("音效：${if (AppDataStore.soundOn(context)) "开" else "关"}")
                }
                "set_voice" -> {
                    AppDataStore.setVoiceMode(context, !AppDataStore.voiceMode(context))
                    toast("语音模式：${if (AppDataStore.voiceMode(context)) "开" else "关"}")
                }
                "set_voice_vol_down" -> {
                    val v = (AppDataStore.voiceVolume(context) - 10).coerceAtLeast(0)
                    AppDataStore.setVoiceVolume(context, v)
                    toast("语音音量：$v")
                }
                "set_voice_vol_up" -> {
                    val v = (AppDataStore.voiceVolume(context) + 10).coerceAtMost(100)
                    AppDataStore.setVoiceVolume(context, v)
                    toast("语音音量：$v")
                }
                "set_diff_low" -> {
                    AppDataStore.setDifficulty(context, "低"); toast("难度：低")
                }
                "set_diff_mid" -> {
                    AppDataStore.setDifficulty(context, "中"); toast("难度：中")
                }
                "set_diff_high" -> {
                    AppDataStore.setDifficulty(context, "高"); toast("难度：高")
                }
                "set_layer" -> toast("手机悬浮已在系统叠加层，无需调整显示层级")
                "sys_exit" -> onExitOverlay?.invoke()
                else -> {
                    toast("（后期）${titleOf(id)}")
                    return false
                }
            }
        }
        return true
    }

    private fun titleOf(id: String): String {
        fun find(items: List<DesktopMenuCatalog.Item>): String? {
            for (it in items) {
                if (it.id == id) return it.title
                find(it.children)?.let { return it }
            }
            return null
        }
        return find(DesktopMenuCatalog.root) ?: id
    }

    private fun applySize(label: String) {
        PetPrefs.setSizeLabel(context, label)
        animator.applyDisplaySize()
        hub.refreshCompanionSize()
        onResize?.invoke()
        hub.playSizeDissolve()
        toast("大小：$label（${PetPrefs.sizePx(context)}px）")
    }

    private fun applyFont(label: String) {
        AppDataStore.setFontLabel(context, label)
        toast("字体：$label")
    }

    private fun toast(msg: String) {
        Toast.makeText(context, msg, Toast.LENGTH_SHORT).show()
    }
}
