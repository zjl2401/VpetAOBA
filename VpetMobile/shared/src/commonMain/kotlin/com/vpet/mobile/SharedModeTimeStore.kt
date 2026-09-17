package com.vpet.mobile

/** 模式时长累计（对照 achievements.stats.mode_seconds）。 */
object SharedModeTimeStore {
    private const val PREF = "vpet_mode_time"
    private const val KEY_SECONDS = "mode_seconds_json"
    private const val KEY_BUCKET = "active_bucket"
    private const val KEY_START = "bucket_start_elapsed"

    val KEYS = listOf("free", "follow", "stroll", "quiet", "work", "game", "music")

    private fun prefs() = PlatformStorage(PREF)

    fun secondsMap(): MutableMap<String, Double> {
        flush()
        return secondsMapRaw()
    }

    fun totalSeconds(): Long = secondsMap().values.sum().toLong()

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

    fun setBucket(key: String?) {
        flush()
        val p = prefs()
        if (key.isNullOrBlank() || key !in KEYS) {
            p.remove(KEY_BUCKET)
            p.remove(KEY_START)
        } else {
            p.putString(KEY_BUCKET, key)
            p.putLong(KEY_START, PlatformClock.elapsedRealtime())
        }
    }

    fun flush() {
        val p = prefs()
        val key = p.getString(KEY_BUCKET, null) ?: return
        val start = p.getLong(KEY_START, 0L)
        if (start <= 0L) return
        val now = PlatformClock.elapsedRealtime()
        val elapsed = ((now - start) / 1000.0).coerceAtLeast(0.0)
        if (elapsed > 0) {
            val map = secondsMapRaw()
            map[key] = (map[key] ?: 0.0) + elapsed
            saveMap(map)
        }
        p.putLong(KEY_START, now)
    }

    private fun secondsMapRaw(): MutableMap<String, Double> {
        val raw = prefs().getString(KEY_SECONDS, null)
        val map = KEYS.associateWith { 0.0 }.toMutableMap()
        if (!raw.isNullOrBlank()) {
            val o = SimpleJson.parse(raw)
            for (k in KEYS) map[k] = o.optDouble(k, 0.0).coerceAtLeast(0.0)
        }
        return map
    }

    private fun saveMap(map: Map<String, Double>) {
        val o = SimpleJson()
        for (k in KEYS) o.put(k, map[k] ?: 0.0)
        prefs().putString(KEY_SECONDS, o.encode())
    }
}
