package com.vpet.mobile

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.UUID
import java.util.concurrent.TimeUnit

/**
 * 与桌面 `data/pet_profile.json` / `schedules.json` 字段对齐的本地档案。
 * 所属人：owner_name + owner_set_at（"yyyy-MM-dd HH:mm"）。
 */
object PetProfileStore {
    private const val PREF = "vpet_profile"
    private const val KEY_JSON = "pet_profile_json"
    private const val KEY_SCHEDULES = "schedules_json"
    private const val KEY_MUSIC_URI = "music_uri"
    private const val KEY_MUSIC_TITLE = "music_title"

    const val OWNER_NAME_MAX_LEN = 16
    const val PET_BIRTHDAY_MONTH = 4
    const val PET_BIRTHDAY_DAY = 22

    private val fmt = SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.CHINA)
    private val dayFmt = SimpleDateFormat("yyyy-MM-dd", Locale.CHINA)

    private fun prefs(ctx: Context) =
        ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE)

    fun profile(ctx: Context): JSONObject {
        val raw = prefs(ctx).getString(KEY_JSON, null)
        if (!raw.isNullOrBlank()) {
            try {
                return JSONObject(raw)
            } catch (_: Exception) {
            }
        }
        return defaultProfile().also { saveProfile(ctx, it) }
    }

    private fun defaultProfile(): JSONObject =
        JSONObject()
            .put("owner_name", "")
            .put("owner_set_at", "")
            .put("owner_welcome_done", false)
            .put("last_launch_at", "")
            .put("created", fmt.format(Date()))
            .put("bless_month", 0)
            .put("bless_day", 0)
            .put("bless_message", "")
            .put("gift_text", "")
            .put("last_owner_bday_ymd", "")
            .put("last_pet_bday_ymd", "")
            .put("wear_flower", false)
            .put("records", JSONObject())

    fun wearingFlower(ctx: Context): Boolean = profile(ctx).optBoolean("wear_flower", false)

    /** 戴花耗 1 朵；摘下还 1 朵。返回提示。 */
    fun toggleWearFlower(ctx: Context): String {
        val p = profile(ctx)
        val on = p.optBoolean("wear_flower", false)
        return if (on) {
            p.put("wear_flower", false)
            saveProfile(ctx, p)
            WalletStore.grantItem(ctx, "flower_cut", 1)
            "已摘下头顶的花"
        } else {
            if (WalletStore.itemCount(ctx, "flower_cut") <= 0) return "还没有采下的花"
            if (!WalletStore.consumeItem(ctx, "flower_cut", 1)) return "还没有采下的花"
            p.put("wear_flower", true)
            saveProfile(ctx, p)
            "戴上了小花～"
        }
    }

    fun saveProfile(ctx: Context, obj: JSONObject) {
        prefs(ctx).edit().putString(KEY_JSON, obj.toString()).apply()
    }

    fun ownerName(ctx: Context): String =
        profile(ctx).optString("owner_name", "").trim().take(OWNER_NAME_MAX_LEN)

    fun hasOwner(ctx: Context): Boolean = ownerName(ctx).isNotEmpty()

    fun setOwnerName(ctx: Context, raw: String): Boolean {
        if (hasOwner(ctx)) return false
        val name = raw.trim().take(OWNER_NAME_MAX_LEN)
        if (name.isEmpty()) return false
        val p = profile(ctx)
        p.put("owner_name", name)
        p.put("owner_set_at", fmt.format(Date()))
        p.put("owner_welcome_done", false)
        saveProfile(ctx, p)
        return true
    }

    /** 对照 OWNER_MISS_AFTER_SEC = 3 天。 */
    const val OWNER_MISS_AFTER_MS = 3L * 24 * 3600 * 1000

    private val WELCOME_LINES = listOf(
        "{name}！从今天起就拜托你啦～",
        "认主成功！你好呀，{name}～以后多多指教哦！",
        "{name}，我会一直在这里等你的。",
    )
    private val MISS_LINES = listOf(
        "{name}……好想你呀。",
        "好久不见，{name}！我等你好久了～",
        "{name}，你终于来看我了……",
        "太久没见了，{name}，我有一点点想你。",
    )

    /**
     * 启动问候：首次欢迎 / ≥3 天未见想念。
     * @return 台词；无则 null。会写回 last_launch_at / owner_welcome_done。
     */
    fun consumeLaunchGreeting(ctx: Context): String? {
        if (!hasOwner(ctx)) return null
        val p = profile(ctx)
        val name = ownerName(ctx)
        val now = System.currentTimeMillis()
        val lastRaw = p.optString("last_launch_at", "")
        val lastMs = try {
            if (lastRaw.isBlank()) 0L else fmt.parse(lastRaw)?.time ?: 0L
        } catch (_: Exception) {
            0L
        }
        val line = when {
            !p.optBoolean("owner_welcome_done", false) -> {
                p.put("owner_welcome_done", true)
                WELCOME_LINES.random().replace("{name}", name)
            }
            lastMs > 0L && now - lastMs >= OWNER_MISS_AFTER_MS ->
                MISS_LINES.random().replace("{name}", name)
            else -> null
        }
        p.put("last_launch_at", fmt.format(Date(now)))
        saveProfile(ctx, p)
        return line
    }

    fun ownerSetAtMs(ctx: Context): Long {
        val raw = profile(ctx).optString("owner_set_at", "")
        if (raw.isBlank()) return 0L
        return try {
            fmt.parse(raw)?.time ?: 0L
        } catch (_: Exception) {
            0L
        }
    }

    fun companionDays(ctx: Context): Int {
        val at = ownerSetAtMs(ctx)
        if (at <= 0L || !hasOwner(ctx)) return 0
        val days = TimeUnit.MILLISECONDS.toDays(System.currentTimeMillis() - at)
        return (days + 1).toInt().coerceAtLeast(1)
    }

    /** 导出与桌面兼容的 pet_profile.json 文本 */
    fun exportJson(ctx: Context): String {
        val p = profile(ctx)
        return p.toString(2)
    }

    /**
     * 从桌面 pet_profile.json 导入。
     * 若手机尚无所属人，采用文件中的 owner；若两边都有且不同，[forceOwner] 才覆盖手机。
     */
    fun importJson(ctx: Context, text: String, forceOwner: Boolean = false): String {
        val incoming = JSONObject(text)
        val cur = profile(ctx)
        val inName = incoming.optString("owner_name", "").trim().take(OWNER_NAME_MAX_LEN)
        val curName = cur.optString("owner_name", "").trim()

        when {
            curName.isEmpty() && inName.isNotEmpty() -> {
                cur.put("owner_name", inName)
                val setAt = incoming.optString("owner_set_at", "").ifBlank { fmt.format(Date()) }
                cur.put("owner_set_at", setAt)
                cur.put(
                    "owner_welcome_done",
                    incoming.optBoolean("owner_welcome_done", true),
                )
            }
            curName.isNotEmpty() && inName.isNotEmpty() && curName != inName -> {
                if (forceOwner) {
                    cur.put("owner_name", inName)
                    cur.put("owner_set_at", incoming.optString("owner_set_at", cur.optString("owner_set_at")))
                    if (incoming.has("owner_welcome_done")) {
                        cur.put("owner_welcome_done", incoming.optBoolean("owner_welcome_done"))
                    }
                }
            }
            curName.isEmpty() && inName.isEmpty() -> Unit
        }

        // 合并生日/礼物等非冲突字段
        listOf(
            "bless_month", "bless_day", "bless_message", "gift_text",
            "last_owner_bday_ymd", "last_pet_bday_ymd", "created",
            "last_launch_at", "owner_welcome_done",
        ).forEach { key ->
            if (incoming.has(key) && key != "owner_welcome_done") {
                cur.put(key, incoming.get(key))
            } else if (key == "owner_welcome_done" && incoming.has(key) && curName.isEmpty()) {
                cur.put(key, incoming.get(key))
            }
        }
        saveProfile(ctx, cur)
        return when {
            curName.isNotEmpty() && inName.isNotEmpty() && curName != inName && !forceOwner ->
                "已合并生日等字段；所属人保持手机「$curName」（与电脑「$inName」不同，可强制覆盖）"
            else -> "已导入档案 · 所属人=${ownerName(ctx)}"
        }
    }

    fun setBless(ctx: Context, month: Int, day: Int, message: String) {
        val p = profile(ctx)
        p.put("bless_month", month.coerceIn(1, 12))
        p.put("bless_day", day.coerceIn(1, 31))
        p.put("bless_message", message.trim().take(80))
        saveProfile(ctx, p)
    }

    fun setGiftText(ctx: Context, gift: String) {
        val p = profile(ctx)
        p.put("gift_text", gift.trim().take(40))
        saveProfile(ctx, p)
    }

    /** 启动时检查所属人生日 / 桌宠 4/22 礼物感谢 */
    fun checkBirthdayToasts(ctx: Context): List<String> {
        val p = profile(ctx)
        val today = dayFmt.format(Date())
        val cal = java.util.Calendar.getInstance()
        val m = cal.get(java.util.Calendar.MONTH) + 1
        val d = cal.get(java.util.Calendar.DAY_OF_MONTH)
        val out = mutableListOf<String>()
        val bm = p.optInt("bless_month", 0)
        val bd = p.optInt("bless_day", 0)
        if (bm == m && bd == d && p.optString("last_owner_bday_ymd") != today) {
            val msg = p.optString("bless_message", "").ifBlank { "生日快乐！" }
            out += "生日快乐，${ownerName(ctx)}；$msg"
            p.put("last_owner_bday_ymd", today)
        }
        if (m == PET_BIRTHDAY_MONTH && d == PET_BIRTHDAY_DAY &&
            p.optString("last_pet_bday_ymd") != today
        ) {
            val gift = p.optString("gift_text", "").trim()
            val name = ownerName(ctx).ifBlank { "你" }
            out += if (gift.isNotEmpty()) {
                "今天是苍叶生日～谢谢 $name 的「$gift」！"
            } else {
                "今天是苍叶生日（4/22）～"
            }
            p.put("last_pet_bday_ymd", today)
        }
        if (out.isNotEmpty()) saveProfile(ctx, p)
        return out
    }

    // —— 日程（对齐 schedules.json：id/time/text/weekdays?）——

    fun schedules(ctx: Context): JSONArray {
        val raw = prefs(ctx).getString(KEY_SCHEDULES, "[]") ?: "[]"
        return try {
            JSONArray(raw)
        } catch (_: Exception) {
            JSONArray()
        }
    }

    fun saveSchedules(ctx: Context, arr: JSONArray) {
        prefs(ctx).edit().putString(KEY_SCHEDULES, arr.toString()).apply()
    }

    fun addSchedule(ctx: Context, timeHm: String, text: String): Boolean {
        val t = normalizeTime(timeHm) ?: return false
        val txt = text.trim()
        if (txt.isEmpty()) return false
        val arr = schedules(ctx)
        arr.put(
            JSONObject()
                .put("id", UUID.randomUUID().toString())
                .put("time", t)
                .put("text", txt.take(60)),
        )
        saveSchedules(ctx, arr)
        return true
    }

    fun removeSchedule(ctx: Context, id: String) {
        val arr = schedules(ctx)
        val next = JSONArray()
        for (i in 0 until arr.length()) {
            val o = arr.getJSONObject(i)
            if (o.optString("id") != id) next.put(o)
        }
        saveSchedules(ctx, next)
    }

    fun normalizeTime(raw: String): String? {
        var text = raw.trim()
        if (text.length == 4 && text.all { it.isDigit() }) {
            text = "${text.substring(0, 2)}:${text.substring(2)}"
        }
        val parts = text.split(":")
        if (parts.size < 2) return null
        val h = parts[0].toIntOrNull() ?: return null
        val m = parts[1].toIntOrNull() ?: return null
        if (h !in 0..23 || m !in 0..59) return null
        return "%02d:%02d".format(h, m)
    }

    fun dueScheduleTexts(ctx: Context, nowHm: String): List<String> {
        val arr = schedules(ctx)
        val out = mutableListOf<String>()
        for (i in 0 until arr.length()) {
            val o = arr.getJSONObject(i)
            if (o.optString("time") == nowHm) {
                out += o.optString("text")
            }
        }
        return out
    }

    fun exportSchedulesJson(ctx: Context): String = schedules(ctx).toString(2)

    fun importSchedulesJson(ctx: Context, text: String): Int {
        val arr = JSONArray(text)
        saveSchedules(ctx, arr)
        return arr.length()
    }

    // —— 音乐本地 URI ——

    fun musicUri(ctx: Context): String? =
        prefs(ctx).getString(KEY_MUSIC_URI, null)?.takeIf { it.isNotBlank() }

    fun musicTitle(ctx: Context): String =
        prefs(ctx).getString(KEY_MUSIC_TITLE, "") ?: ""

    fun setMusic(ctx: Context, uri: String?, title: String?) {
        prefs(ctx).edit()
            .putString(KEY_MUSIC_URI, uri)
            .putString(KEY_MUSIC_TITLE, title ?: "")
            .apply()
    }
}
