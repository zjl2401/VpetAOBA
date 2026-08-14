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
    private val onFontChanged: (() -> Unit)? = null,
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
                "mode_stroll", "act_walk" -> {
                    if (hub.isStrollMode) hub.startFree()
                    else hub.startStroll()
                }
                "mode_follow" -> hub.toggleFollow()
                "mode_quiet" -> {
                    if (hub.isQuiet) hub.endQuiet(fromMenu = true)
                    else hub.startQuiet()
                }
                "act_sleep" -> hub.startSleepInteract()
                "mode_music" -> hub.startMusic()
                "act_stand" -> hub.playAction("act_stand")
                "act_hi" -> hub.playAction("act_hi")
                "act_squat", "act_kick", "act_yes", "act_no", "act_call", "act_judge",
                "act_adult",
                -> hub.playAction(id)
                "act_eat" -> hub.openEatFoodMenu()
                "panel_invite" -> toast("尚未开发完全")
                "panel_persona" -> hub.togglePersona()
                "expr_happy", "expr_sad", "expr_shy", "expr_wink", "expr_like",
                "expr_angry", "expr_idea", "expr_question", "expr_bixin",
                -> hub.playExpression(id)
                "work_free", "act_work" -> {
                    if (hub.isWorking && hub.isMenuChecked("work_free")) hub.endWork(fromMenu = true)
                    else hub.startWorkFree()
                }
                "work_custom" -> hub.openWorkCustomSetup()
                "work_end" -> hub.endWork(fromMenu = true)
                "work_show_props" -> hub.toggleWorkShowProps()
                "work_show_stack" -> hub.toggleWorkShowStack()
                "tool_sw" -> hub.showStopwatch()
                "tool_timer", "tool_timer_custom" -> hub.openTimerSetup()
                "tool_pomo_custom" -> hub.openPomodoroSetup()
                "tool_pomo_end" -> hub.endPomodoro(silent = false)
                "tool_schedule" -> hub.openScheduleSetup()
                "tool_bday_set" -> hub.openBirthdaySetup()
                "tool_archive", "sys_sync" -> hub.openTools()
                "panel_open" -> hub.openPanel()
                "panel_outfit" -> hub.openOutfitEditor()
                "panel_companion" -> hub.toggleCompanion()
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
                "set_voice_vol" -> hub.openVoiceVolumeSetup()
                "set_sfx_vol" -> hub.openSfxVolumeSetup()
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
                "set_layer" -> toast(
                    DesktopGuideCopy.DISPLAY_LAYER_HINT + "（手机悬浮在系统叠加层）",
                )
                "sys_exit" -> onExitOverlay?.invoke()
                else -> {
                    toast("（后期）${titleOf(id)}")
                    return false
                }
            }
        }
        return true
    }

    fun isChecked(id: String): Boolean = hub.isMenuChecked(id)

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
        hub.applyDisplaySizeToPetAndCompanion()
        onResize?.invoke()
        hub.playSizeDissolve()
        toast("大小：约$label（${PetPrefs.sizePx(context)}px）· 伴侣同步")
    }

    private fun applyFont(label: String) {
        AppDataStore.setFontLabel(context, label)
        hub.applyFontScaleToOverlay()
        onFontChanged?.invoke()
        toast("字体：$label")
    }

    private fun toast(msg: String) {
        Toast.makeText(context, msg, Toast.LENGTH_SHORT).show()
    }
}
