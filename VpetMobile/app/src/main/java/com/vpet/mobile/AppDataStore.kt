package com.vpet.mobile

import android.content.Context
import android.content.SharedPreferences
import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.UUID

/** 日记 / 成就 / 应用设置（字体·声音·难度）。 */
object AppDataStore {
    private const val PREF = "vpet_appdata"
    private const val KEY_DIARY = "diary_json"
    private const val KEY_ACH = "achievements_json"
    private const val KEY_FONT = "font_label"
    private const val KEY_SOUND = "sound_on"
    private const val KEY_VOICE_MODE = "voice_mode"
    private const val KEY_VOICE_VOL = "voice_volume"
    private const val KEY_DIFF = "difficulty"

    val FONT_PRESETS = linkedMapOf("小" to 11f, "中" to 13f, "大" to 15f, "特大" to 17f)
    val DIFF_PRESETS = listOf("低", "中", "高")

    private fun prefs(ctx: Context): SharedPreferences =
        ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE)

    fun fontLabel(ctx: Context): String {
        val v = prefs(ctx).getString(KEY_FONT, "中") ?: "中"
        return if (v in FONT_PRESETS) v else "中"
    }

    fun fontSp(ctx: Context): Float = FONT_PRESETS.getValue(fontLabel(ctx))

    fun setFontLabel(ctx: Context, label: String) {
        val k = if (label in FONT_PRESETS) label else "中"
        prefs(ctx).edit().putString(KEY_FONT, k).apply()
    }

    /** 音效（打字音等）；对照桌面 sfx，与语音分离。 */
    fun soundOn(ctx: Context): Boolean = prefs(ctx).getBoolean(KEY_SOUND, true)

    fun setSoundOn(ctx: Context, on: Boolean) {
        prefs(ctx).edit().putBoolean(KEY_SOUND, on).apply()
    }

    /** 语音模式；对照桌面 voice_mode。默认开（兼容旧「声音含语音」习惯）。 */
    fun voiceMode(ctx: Context): Boolean = prefs(ctx).getBoolean(KEY_VOICE_MODE, true)

    fun setVoiceMode(ctx: Context, on: Boolean) {
        prefs(ctx).edit().putBoolean(KEY_VOICE_MODE, on).apply()
    }

    /** 语音音量 0–100；对照 voice_volume。 */
    fun voiceVolume(ctx: Context): Int = prefs(ctx).getInt(KEY_VOICE_VOL, 80).coerceIn(0, 100)

    fun setVoiceVolume(ctx: Context, v: Int) {
        prefs(ctx).edit().putInt(KEY_VOICE_VOL, v.coerceIn(0, 100)).apply()
    }

    fun voiceVolumeF(ctx: Context): Float = voiceVolume(ctx) / 100f

    fun difficulty(ctx: Context): String {
        val v = prefs(ctx).getString(KEY_DIFF, "中") ?: "中"
        return if (v in DIFF_PRESETS) v else "中"
    }

    fun setDifficulty(ctx: Context, d: String) {
        val k = if (d in DIFF_PRESETS) d else "中"
        prefs(ctx).edit().putString(KEY_DIFF, k).apply()
    }

    // —— 工作显示设置（对齐 show_props / show_stack）——
    private const val KEY_WORK_PROPS = "work_show_props"
    private const val KEY_WORK_STACK = "work_show_stack"
    private const val KEY_PERSONA = "persona" // default | jinmu
    private const val KEY_STAMINA = "stamina"
    private const val KEY_MOOD = "mood"
    private const val KEY_COMPANION = "companion_enabled"

    fun workShowProps(ctx: Context): Boolean = prefs(ctx).getBoolean(KEY_WORK_PROPS, true)
    fun setWorkShowProps(ctx: Context, v: Boolean) {
        prefs(ctx).edit().putBoolean(KEY_WORK_PROPS, v).apply()
    }
    fun workShowStack(ctx: Context): Boolean = prefs(ctx).getBoolean(KEY_WORK_STACK, true)
    fun setWorkShowStack(ctx: Context, v: Boolean) {
        prefs(ctx).edit().putBoolean(KEY_WORK_STACK, v).apply()
    }

    fun persona(ctx: Context): String =
        prefs(ctx).getString(KEY_PERSONA, "default") ?: "default"

    fun isJinmu(ctx: Context): Boolean = persona(ctx) == "jinmu"

    fun togglePersona(ctx: Context): String {
        val next = if (isJinmu(ctx)) "default" else "jinmu"
        prefs(ctx).edit().putString(KEY_PERSONA, next).apply()
        return next
    }

    fun stamina(ctx: Context): Int = prefs(ctx).getInt(KEY_STAMINA, 80).coerceIn(0, 100)
    fun mood(ctx: Context): Int = prefs(ctx).getInt(KEY_MOOD, 80).coerceIn(0, 100)
    fun setStamina(ctx: Context, v: Int) {
        prefs(ctx).edit().putInt(KEY_STAMINA, v.coerceIn(0, 100)).apply()
    }
    fun setMood(ctx: Context, v: Int) {
        prefs(ctx).edit().putInt(KEY_MOOD, v.coerceIn(0, 100)).apply()
    }
    fun addStaminaMood(ctx: Context, ds: Int, dm: Int) {
        setStamina(ctx, stamina(ctx) + ds)
        setMood(ctx, mood(ctx) + dm)
    }

    fun companionEnabled(ctx: Context): Boolean = prefs(ctx).getBoolean(KEY_COMPANION, false)
    fun setCompanionEnabled(ctx: Context, on: Boolean) {
        prefs(ctx).edit().putBoolean(KEY_COMPANION, on).apply()
    }

    fun diaries(ctx: Context): JSONArray {
        return try {
            JSONArray(prefs(ctx).getString(KEY_DIARY, "[]"))
        } catch (_: Exception) {
            JSONArray()
        }
    }

    fun addDiary(ctx: Context, text: String): Boolean {
        val t = text.trim()
        if (t.isEmpty()) return false
        val arr = diaries(ctx)
        val fmt = SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.CHINA)
        arr.put(
            JSONObject()
                .put("id", UUID.randomUUID().toString())
                .put("ts", fmt.format(Date()))
                .put("text", t.take(200)),
        )
        prefs(ctx).edit().putString(KEY_DIARY, arr.toString()).apply()
        unlock(ctx, "diary_first")
        return true
    }

    fun clearDiaries(ctx: Context) {
        prefs(ctx).edit().putString(KEY_DIARY, "[]").apply()
    }

    fun achievements(ctx: Context): Set<String> {
        val raw = prefs(ctx).getString(KEY_ACH, "[]") ?: "[]"
        return try {
            val arr = JSONArray(raw)
            buildSet {
                for (i in 0 until arr.length()) add(arr.getString(i))
            }
        } catch (_: Exception) {
            emptySet()
        }
    }

    fun unlock(ctx: Context, id: String) {
        val set = achievements(ctx).toMutableSet()
        if (set.add(id)) {
            val arr = JSONArray()
            set.forEach { arr.put(it) }
            prefs(ctx).edit().putString(KEY_ACH, arr.toString()).apply()
        }
    }

    fun achievementCatalog(): List<Triple<String, String, String>> = listOf(
        Triple("owner_named", "认主成功", "填写所属人昵称"),
        Triple("companion_on", "莲来作伴", "开启智能伴侣"),
        Triple("diary_first", "落笔成忆", "写下第一条日记"),
        Triple("memory_open", "翻开回忆", "打开画廊或留声"),
        Triple("home_visit", "回家看看", "进入家园"),
        Triple("farm_open", "田园生活", "开启家园经营"),
        Triple("music_play", "耳机不离", "进入音乐模式"),
        Triple("work_done", "搬运工", "完成一次运送"),
        Triple("rpg_play", "誓言启程", "打开 Silent Oath"),
        Triple("pomo_done", "番茄达人", "完成一轮番茄"),
    )

    /** 重置：保留所属人，清日记/成就标记/设置等到默认（对齐桌面保留所属人）。 */
    fun resetKeepOwner(ctx: Context) {
        val ownerName = PetProfileStore.ownerName(ctx)
        val ownerAt = PetProfileStore.profile(ctx).optString("owner_set_at")
        prefs(ctx).edit().clear().apply()
        // 重建 profile，仅保留所属人
        val p = JSONObject()
            .put("owner_name", ownerName)
            .put("owner_set_at", ownerAt)
            .put("owner_welcome_done", ownerName.isNotEmpty())
            .put("created", ownerAt.ifBlank {
                SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.CHINA).format(Date())
            })
            .put("bless_month", 0)
            .put("bless_day", 0)
            .put("bless_message", "")
            .put("gift_text", "")
            .put("records", JSONObject())
        PetProfileStore.saveProfile(ctx, p)
        PetProfileStore.saveSchedules(ctx, JSONArray())
        PetProfileStore.setMusic(ctx, null, null)
        PetPrefs.setSizeLabel(ctx, PetPrefs.DEFAULT_SIZE_LABEL)
    }
}
