package com.vpet.mobile

import android.content.Context
import android.content.SharedPreferences

/**
 * 大小档仍用独立 pref；所属人等走 [PetProfileStore]（与桌面 pet_profile.json 对齐）。
 * 首次读取时迁移旧版 SharedPreferences 所属人。
 */
object PetPrefs {
    private const val PREF = "vpet_mobile"
    private const val KEY_SIZE = "display_preset"
    private const val KEY_OWNER_LEGACY = "owner_name"
    private const val KEY_OWNER_AT_LEGACY = "owner_set_at_ms"
    private const val KEY_MIGRATED = "profile_migrated_v1"

    const val OWNER_NAME_MAX_LEN = PetProfileStore.OWNER_NAME_MAX_LEN

    val SIZE_PRESETS: Map<String, Int> = linkedMapOf(
        "小" to 96,
        "中" to 128,
        "大" to 176,
    )

    const val DEFAULT_SIZE_LABEL = "中"

    private fun prefs(ctx: Context): SharedPreferences =
        ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE)

    private fun migrateIfNeeded(ctx: Context) {
        val p = prefs(ctx)
        if (p.getBoolean(KEY_MIGRATED, false)) return
        val legacy = (p.getString(KEY_OWNER_LEGACY, "") ?: "").trim()
        if (legacy.isNotEmpty() && !PetProfileStore.hasOwner(ctx)) {
            val at = p.getLong(KEY_OWNER_AT_LEGACY, 0L)
            val profile = PetProfileStore.profile(ctx)
            profile.put("owner_name", legacy.take(OWNER_NAME_MAX_LEN))
            if (at > 0L) {
                val sdf = java.text.SimpleDateFormat("yyyy-MM-dd HH:mm", java.util.Locale.CHINA)
                profile.put("owner_set_at", sdf.format(java.util.Date(at)))
            } else {
                profile.put(
                    "owner_set_at",
                    java.text.SimpleDateFormat("yyyy-MM-dd HH:mm", java.util.Locale.CHINA)
                        .format(java.util.Date()),
                )
            }
            profile.put("owner_welcome_done", true)
            PetProfileStore.saveProfile(ctx, profile)
        }
        p.edit().putBoolean(KEY_MIGRATED, true).apply()
    }

    fun sizeLabel(ctx: Context): String {
        val v = prefs(ctx).getString(KEY_SIZE, DEFAULT_SIZE_LABEL) ?: DEFAULT_SIZE_LABEL
        return if (v in SIZE_PRESETS) v else DEFAULT_SIZE_LABEL
    }

    fun sizePx(ctx: Context): Int = SIZE_PRESETS.getValue(sizeLabel(ctx))

    fun setSizeLabel(ctx: Context, label: String) {
        val key = if (label in SIZE_PRESETS) label else DEFAULT_SIZE_LABEL
        prefs(ctx).edit().putString(KEY_SIZE, key).apply()
    }

    fun ownerName(ctx: Context): String {
        migrateIfNeeded(ctx)
        return PetProfileStore.ownerName(ctx)
    }

    fun hasOwner(ctx: Context): Boolean {
        migrateIfNeeded(ctx)
        return PetProfileStore.hasOwner(ctx)
    }

    fun setOwnerName(ctx: Context, raw: String): Boolean {
        migrateIfNeeded(ctx)
        return PetProfileStore.setOwnerName(ctx, raw)
    }

    fun companionDays(ctx: Context): Int {
        migrateIfNeeded(ctx)
        return PetProfileStore.companionDays(ctx)
    }
}
