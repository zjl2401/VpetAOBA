package com.vpet.mobile

import android.content.Context
import android.os.SystemClock
import org.json.JSONArray
import org.json.JSONObject

/**
 * 模式时长：对照 achievements.stats.mode_seconds。
 * 手机成就解锁仍用 id 集合；互导时与桌面 achievements.json 合并 stats。
 */
object ModeTimeStore {
    private const val PREF = "vpet_mode_time"
    private const val KEY_SECONDS = "mode_seconds_json"
    private const val KEY_BUCKET = "active_bucket"
    private const val KEY_START = "bucket_start_elapsed"

    val KEYS = listOf("free", "follow", "stroll", "quiet", "work", "game", "music", "video")

    private fun prefs(ctx: Context) = ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE)

    fun secondsMap(ctx: Context): MutableMap<String, Double> {
        PersistVault.bootstrap(ctx)
        flush(ctx)
        val raw = prefs(ctx).getString(KEY_SECONDS, null)
        val map = KEYS.associateWith { 0.0 }.toMutableMap()
        if (!raw.isNullOrBlank()) {
            try {
                val o = JSONObject(raw)
                for (k in KEYS) map[k] = o.optDouble(k, 0.0).coerceAtLeast(0.0)
            } catch (_: Exception) {
            }
        }
        return map
    }

    fun totalSeconds(ctx: Context): Long =
        secondsMap(ctx).values.sum().toLong()

    fun formatDuration(totalSec: Long): String {
        val h = totalSec / 3600
        val m = (totalSec % 3600) / 60
        val s = totalSec % 60
        return when {
            h > 0 -> "${h}小时${m}分"
            m > 0 -> "${m}分${s}秒"
            else -> "${s}秒"
        }
    }

    fun detailText(ctx: Context): String {
        val m = secondsMap(ctx)
        val labels = mapOf(
            "free" to "自由",
            "follow" to "跟随",
            "stroll" to "漫步",
            "quiet" to "睡眠",
            "work" to "工作",
            "game" to "游戏",
            "music" to "音乐",
            "video" to "视频",
        )
        return buildString {
            appendLine("相伴时长合计：${formatDuration(totalSeconds(ctx))}")
            for (k in KEYS) {
                val sec = m[k]?.toLong() ?: 0L
                if (sec > 0) appendLine("· ${labels[k]}：${formatDuration(sec)}")
            }
        }.trimEnd()
    }

    /** 切换模式桶；null=暂停累计。 */
    fun setBucket(ctx: Context, key: String?) {
        flush(ctx)
        val ed = prefs(ctx).edit()
        if (key.isNullOrBlank() || key !in KEYS) {
            ed.remove(KEY_BUCKET).remove(KEY_START)
        } else {
            ed.putString(KEY_BUCKET, key)
                .putLong(KEY_START, SystemClock.elapsedRealtime())
        }
        ed.apply()
    }

    fun flush(ctx: Context) {
        val p = prefs(ctx)
        val key = p.getString(KEY_BUCKET, null) ?: return
        val start = p.getLong(KEY_START, 0L)
        if (start <= 0L) return
        val now = SystemClock.elapsedRealtime()
        val elapsed = ((now - start) / 1000.0).coerceAtLeast(0.0)
        if (elapsed > 0) {
            val map = secondsMapRaw(ctx)
            map[key] = (map[key] ?: 0.0) + elapsed
            saveMap(ctx, map)
        }
        prefs(ctx).edit().putLong(KEY_START, now).apply()
    }

    private fun secondsMapRaw(ctx: Context): MutableMap<String, Double> {
        val raw = prefs(ctx).getString(KEY_SECONDS, null)
        val map = KEYS.associateWith { 0.0 }.toMutableMap()
        if (!raw.isNullOrBlank()) {
            try {
                val o = JSONObject(raw)
                for (k in KEYS) map[k] = o.optDouble(k, 0.0).coerceAtLeast(0.0)
            } catch (_: Exception) {
            }
        }
        return map
    }

    private fun saveMap(ctx: Context, map: Map<String, Double>) {
        val o = JSONObject()
        for (k in KEYS) o.put(k, map[k] ?: 0.0)
        prefs(ctx).edit().putString(KEY_SECONDS, o.toString()).apply()
        PersistVault.snapshot(ctx)
    }

    /** 导出可合并进桌面 achievements.json 的片段。 */
    fun exportAchievementsPatch(ctx: Context): String {
        flush(ctx)
        val stats = JSONObject().put("mode_seconds", JSONObject().also { o ->
            for ((k, v) in secondsMap(ctx)) o.put(k, v)
        })
        val unlocked = JSONObject()
        AppDataStore.achievements(ctx).forEach { unlocked.put(it, true) }
        return JSONObject()
            .put("unlocked", unlocked)
            .put("stats", stats)
            .toString(2)
    }

    fun importAchievementsJson(ctx: Context, text: String): String {
        flush(ctx)
        val incoming = JSONObject(text)
        val stats = incoming.optJSONObject("stats")
        val modeSec = stats?.optJSONObject("mode_seconds")
        if (modeSec != null) {
            val map = secondsMapRaw(ctx)
            for (k in KEYS) {
                if (modeSec.has(k)) {
                    map[k] = modeSec.optDouble(k, 0.0).coerceAtLeast(0.0)
                }
            }
            saveMap(ctx, map)
        }
        val unlocked = incoming.optJSONObject("unlocked")
        if (unlocked != null) {
            unlocked.keys().forEach { id ->
                if (unlocked.optBoolean(id, false) || unlocked.opt(id) != null) {
                    AppDataStore.unlock(ctx, id)
                }
            }
        } else {
            val arr = incoming.optJSONArray("unlocked")
            if (arr != null) {
                for (i in 0 until arr.length()) AppDataStore.unlock(ctx, arr.getString(i))
            }
        }
        return "已导入模式时长 · 合计 ${formatDuration(totalSeconds(ctx))}"
    }
}
