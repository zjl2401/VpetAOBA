package com.vpet.mobile

import kotlin.math.roundToInt

/** 显示大小档（无 Context）；所属人走 SharedPetProfileStore。 */
object SharedPetPrefs {
    private const val PREF = "vpet_mobile"
    private const val KEY_SIZE = "display_preset"
    private const val KEY_SIZE_PX = "display_size_px"
    private const val KEY_SIZE_BUMP_DEFAULT = "size_default_large_v1"

    const val OWNER_NAME_MAX_LEN = SharedPetProfileStore.OWNER_NAME_MAX_LEN

    val SIZE_PRESETS: Map<String, Int> = linkedMapOf(
        "小" to 96,
        "中" to 128,
        "大" to 176,
    )

    const val SIZE_MIN_PX = 80
    const val SIZE_MAX_PX = 240
    const val SIZE_STEP_PX = 8
    const val DEFAULT_SIZE_LABEL = "大"
    val DEFAULT_SIZE_PX: Int = SIZE_PRESETS.getValue(DEFAULT_SIZE_LABEL)

    private fun prefs() = PlatformStorage(PREF)

    fun snapSizePx(px: Int): Int {
        val clamped = px.coerceIn(SIZE_MIN_PX, SIZE_MAX_PX)
        val stepped = SIZE_MIN_PX +
            ((clamped - SIZE_MIN_PX).toFloat() / SIZE_STEP_PX).roundToInt() * SIZE_STEP_PX
        return stepped.coerceIn(SIZE_MIN_PX, SIZE_MAX_PX)
    }

    fun nearestSizeLabel(px: Int): String {
        val target = snapSizePx(px)
        return SIZE_PRESETS.minByOrNull { kotlin.math.abs(it.value - target) }?.key
            ?: DEFAULT_SIZE_LABEL
    }

    fun sizePx(): Int {
        bumpDefaultOnce()
        val p = prefs()
        if (p.contains(KEY_SIZE_PX)) {
            return snapSizePx(p.getInt(KEY_SIZE_PX, DEFAULT_SIZE_PX))
        }
        val label = p.getString(KEY_SIZE, DEFAULT_SIZE_LABEL) ?: DEFAULT_SIZE_LABEL
        val fromLabel = SIZE_PRESETS[label] ?: DEFAULT_SIZE_PX
        p.putInt(KEY_SIZE_PX, fromLabel)
        return fromLabel
    }

    fun sizeLabel(): String = nearestSizeLabel(sizePx())

    fun setSizePx(px: Int) {
        val snapped = snapSizePx(px)
        val p = prefs()
        p.putInt(KEY_SIZE_PX, snapped)
        p.putString(KEY_SIZE, nearestSizeLabel(snapped))
        p.putBoolean(KEY_SIZE_BUMP_DEFAULT, true)
    }

    fun setSizeLabel(label: String) {
        setSizePx(SIZE_PRESETS[label] ?: DEFAULT_SIZE_PX)
    }

    private fun bumpDefaultOnce() {
        val p = prefs()
        if (p.getBoolean(KEY_SIZE_BUMP_DEFAULT, false)) return
        val cur = if (p.contains(KEY_SIZE_PX)) {
            p.getInt(KEY_SIZE_PX, DEFAULT_SIZE_PX)
        } else {
            SIZE_PRESETS[p.getString(KEY_SIZE, "中") ?: "中"] ?: 128
        }
        val next = if (cur == 128) DEFAULT_SIZE_PX else cur
        p.putInt(KEY_SIZE_PX, snapSizePx(next))
        p.putString(KEY_SIZE, nearestSizeLabel(next))
        p.putBoolean(KEY_SIZE_BUMP_DEFAULT, true)
    }

    fun ownerName(): String = SharedPetProfileStore.ownerName()
    fun hasOwner(): Boolean = SharedPetProfileStore.hasOwner()
    fun setOwnerName(raw: String): Boolean = SharedPetProfileStore.setOwnerName(raw)
    fun companionDays(): Int = SharedPetProfileStore.companionDays()
}
