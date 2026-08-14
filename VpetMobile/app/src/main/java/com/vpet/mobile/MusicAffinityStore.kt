package com.vpet.mobile

import android.content.Context
import org.json.JSONObject

/**
 * 听歌好感：对照桌面 music_affinity（每 5 分钟 +1，60 点一格）。
 */
object MusicAffinityStore {
    private const val PREFS = "music_affinity"
    private const val KEY_JSON = "points"
    private const val KEY_PEAK = "peak_lv"
    private const val KEY_LISTEN = "listen_seconds"
    const val TICK_MS = 5 * 60 * 1000L
    const val POINTS_PER_TICK = 1
    const val BAR_SEGMENT = 60

    private fun prefs(ctx: Context) =
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    fun points(ctx: Context, charId: String): Float {
        val o = load(ctx)
        return o.optDouble(charId, 0.0).toFloat()
    }

    fun addTick(ctx: Context, charId: String) {
        if (charId.isBlank()) return
        val o = load(ctx)
        val cur = o.optDouble(charId, 0.0) + POINTS_PER_TICK
        o.put(charId, cur)
        prefs(ctx).edit().putString(KEY_JSON, o.toString()).apply()
        val lv = (cur / BAR_SEGMENT).toInt()
        val peak = prefs(ctx).getInt(KEY_PEAK, 0)
        if (lv > peak) prefs(ctx).edit().putInt(KEY_PEAK, lv).apply()
        addListenSeconds(ctx, TICK_MS / 1000.0)
    }

    fun level(ctx: Context, charId: String): Int =
        (points(ctx, charId) / BAR_SEGMENT).toInt()

    fun barInSegment(ctx: Context, charId: String): Int =
        (points(ctx, charId) % BAR_SEGMENT).toInt()

    fun peakLevel(ctx: Context): Int = prefs(ctx).getInt(KEY_PEAK, 0)

    fun listenSeconds(ctx: Context): Double =
        prefs(ctx).getFloat(KEY_LISTEN, 0f).toDouble()

    private fun addListenSeconds(ctx: Context, sec: Double) {
        val cur = listenSeconds(ctx) + sec
        prefs(ctx).edit().putFloat(KEY_LISTEN, cur.toFloat()).apply()
        if (cur >= 3600.0) AppDataStore.unlock(ctx, "listen_hour")
    }

    fun summaryLine(ctx: Context, charId: String = "aoba"): String {
        val label = BundledMusic.charLabel(charId)
        val lv = level(ctx, charId)
        val bar = barInSegment(ctx, charId)
        val peak = peakLevel(ctx)
        return "听歌好感 $label Lv.$lv（$bar/$BAR_SEGMENT）· 历史最高 Lv.$peak"
    }

    private fun load(ctx: Context): JSONObject {
        val raw = prefs(ctx).getString(KEY_JSON, null) ?: return JSONObject()
        return try {
            JSONObject(raw)
        } catch (_: Exception) {
            JSONObject()
        }
    }
}
