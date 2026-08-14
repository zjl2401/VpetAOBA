package com.vpet.mobile

import android.content.Context
import android.content.SharedPreferences
import kotlin.math.roundToInt

/**
 * 大小档仍用独立 pref；所属人等走 [PetProfileStore]（与桌面 pet_profile.json 对齐）。
 * 首次读取时迁移旧版 SharedPreferences 所属人。
 * 桌宠大小支持连续像素（对照桌面 SIZE_MIN/MAX + snap）。
 */
object PetPrefs {
    private const val PREF = "vpet_mobile"
    private const val KEY_SIZE = "display_preset"
    private const val KEY_SIZE_PX = "display_size_px"
    private const val KEY_OWNER_LEGACY = "owner_name"
    private const val KEY_OWNER_AT_LEGACY = "owner_set_at_ms"
    private const val KEY_MIGRATED = "profile_migrated_v1"

    const val OWNER_NAME_MAX_LEN = PetProfileStore.OWNER_NAME_MAX_LEN

    /**
     * 命名锚点：新「小」≈原「中」、新「中」≈原「大」、新「大」再放大。
     * 设置页可在 [SIZE_MIN_PX]…[SIZE_MAX_PX] 间连续调节。
     */
    val SIZE_PRESETS: Map<String, Int> = linkedMapOf(
        "小" to 192,
        "中" to 264,
        "大" to 360,
    )

    const val SIZE_MIN_PX = 144
    const val SIZE_MAX_PX = 420
    const val SIZE_STEP_PX = 8
    const val DEFAULT_SIZE_LABEL = "中"
    val DEFAULT_SIZE_PX: Int = SIZE_PRESETS.getValue(DEFAULT_SIZE_LABEL)

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

    fun snapSizePx(px: Int): Int {
        val clamped = px.coerceIn(SIZE_MIN_PX, SIZE_MAX_PX)
        val stepped = SIZE_MIN_PX +
            ((clamped - SIZE_MIN_PX).toFloat() / SIZE_STEP_PX).roundToInt() * SIZE_STEP_PX
        return stepped.coerceIn(SIZE_MIN_PX, SIZE_MAX_PX)
    }

    /** 最近命名档（仅展示用）。 */
    fun nearestSizeLabel(px: Int): String {
        val target = snapSizePx(px)
        return SIZE_PRESETS.minByOrNull { kotlin.math.abs(it.value - target) }?.key
            ?: DEFAULT_SIZE_LABEL
    }

    fun sizeLabel(ctx: Context): String = nearestSizeLabel(sizePx(ctx))

    fun sizePx(ctx: Context): Int {
        val p = prefs(ctx)
        if (p.contains(KEY_SIZE_PX)) {
            return snapSizePx(p.getInt(KEY_SIZE_PX, DEFAULT_SIZE_PX))
        }
        val label = p.getString(KEY_SIZE, DEFAULT_SIZE_LABEL) ?: DEFAULT_SIZE_LABEL
        val fromLabel = SIZE_PRESETS[label] ?: DEFAULT_SIZE_PX
        p.edit().putInt(KEY_SIZE_PX, fromLabel).apply()
        return fromLabel
    }

    fun setSizePx(ctx: Context, px: Int) {
        val snapped = snapSizePx(px)
        val label = nearestSizeLabel(snapped)
        prefs(ctx).edit()
            .putInt(KEY_SIZE_PX, snapped)
            .putString(KEY_SIZE, label)
            .apply()
    }

    fun setSizeLabel(ctx: Context, label: String) {
        val px = SIZE_PRESETS[label] ?: DEFAULT_SIZE_PX
        setSizePx(ctx, px)
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
