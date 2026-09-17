package com.vpet.mobile

/** 共享所属人 / 档案核心。 */
object SharedPetProfileStore {
    private const val PREF = "vpet_profile"
    private const val KEY_JSON = "pet_profile_json"
    const val OWNER_NAME_MAX_LEN = 16
    const val OWNER_MISS_AFTER_MS = 3L * 24 * 3600 * 1000
    const val PET_BIRTHDAY_MONTH = 4
    const val PET_BIRTHDAY_DAY = 22

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

    private fun prefs() = PlatformStorage(PREF)

    fun profile(): SimpleJson {
        val raw = prefs().getString(KEY_JSON, null)
        if (!raw.isNullOrBlank()) {
            val o = SimpleJson.parse(raw)
            if (o.keys().isNotEmpty()) return o
        }
        return defaultProfile().also { saveProfile(it) }
    }

    private fun defaultProfile(): SimpleJson =
        SimpleJson()
            .put("owner_name", "")
            .put("owner_set_at", "")
            .put("owner_welcome_done", false)
            .put("last_launch_at", "")
            .put("created", PlatformClock.formatDateTime())
            .put("bless_month", 0)
            .put("bless_day", 0)
            .put("bless_message", "")
            .put("gift_text", "")
            .put("last_owner_bday_ymd", "")
            .put("last_pet_bday_ymd", "")
            .put("wear_flower", false)

    fun saveProfile(obj: SimpleJson) {
        prefs().putString(KEY_JSON, obj.encode())
    }

    fun ownerName(): String =
        profile().optString("owner_name", "").trim().take(OWNER_NAME_MAX_LEN)

    fun hasOwner(): Boolean = ownerName().isNotEmpty()

    fun setOwnerName(raw: String): Boolean {
        if (hasOwner()) return false
        val name = raw.trim().take(OWNER_NAME_MAX_LEN)
        if (name.isEmpty()) return false
        val p = profile()
        p.put("owner_name", name)
        p.put("owner_set_at", PlatformClock.formatDateTime())
        p.put("owner_welcome_done", false)
        saveProfile(p)
        return true
    }

    fun consumeLaunchGreeting(): String? {
        if (!hasOwner()) return null
        val p = profile()
        val name = ownerName()
        val now = PlatformClock.currentTimeMillis()
        val lastRaw = p.optString("last_launch_at", "")
        val lastMs = parseDateTimeMs(lastRaw)
        val line = when {
            !p.optBoolean("owner_welcome_done", false) -> {
                p.put("owner_welcome_done", true)
                WELCOME_LINES.random().replace("{name}", name)
            }
            lastMs > 0L && now - lastMs >= OWNER_MISS_AFTER_MS ->
                MISS_LINES.random().replace("{name}", name)
            else -> null
        }
        p.put("last_launch_at", PlatformClock.formatDateTime(now))
        saveProfile(p)
        return line
    }

    fun companionDays(): Int {
        val at = parseDateTimeMs(profile().optString("owner_set_at", ""))
        if (at <= 0L || !hasOwner()) return 0
        val days = (PlatformClock.currentTimeMillis() - at) / (24L * 3600_000L)
        return (days + 1).toInt().coerceAtLeast(1)
    }

    fun wearingFlower(): Boolean = profile().optBoolean("wear_flower", false)

    fun toggleWearFlower(): String {
        val p = profile()
        val on = p.optBoolean("wear_flower", false)
        return if (on) {
            p.put("wear_flower", false)
            saveProfile(p)
            SharedWalletStore.grantItem("flower_cut", 1)
            "已摘下头顶的花"
        } else {
            if (SharedWalletStore.itemCount("flower_cut") <= 0) return "还没有采下的花"
            if (!SharedWalletStore.consumeItem("flower_cut", 1)) return "还没有采下的花"
            p.put("wear_flower", true)
            saveProfile(p)
            "戴上了小花～"
        }
    }

    private fun parseDateTimeMs(raw: String): Long {
        if (raw.isBlank()) return 0L
        // expect yyyy-MM-dd HH:mm — rough parse
        return try {
            val parts = raw.trim().split(" ")
            val d = parts[0].split("-")
            val t = (parts.getOrNull(1) ?: "00:00").split(":")
            val y = d[0].toInt()
            val m = d[1].toInt()
            val day = d[2].toInt()
            val hh = t[0].toInt()
            val mm = t.getOrNull(1)?.toInt() ?: 0
            // approximate epoch via days since 1970 (no timezone lib in common)
            val days = civilToEpochDays(y, m, day)
            days * 86_400_000L + (hh * 3600L + mm * 60L) * 1000L
        } catch (_: Exception) {
            0L
        }
    }

    private fun civilToEpochDays(year: Int, month: Int, day: Int): Long {
        var y = year
        var m = month
        if (m <= 2) {
            y -= 1
            m += 12
        }
        val era = if (y >= 0) y / 400 else (y - 399) / 400
        val yoe = y - era * 400
        val doy = (153 * (m - 3) + 2) / 5 + day - 1
        val doe = yoe * 365L + yoe / 4 - yoe / 100 + doy
        return era * 146097L + doe - 719468L
    }
}
