package com.vpet.mobile

/**
 * 立绘点击分区：对照桌面 `_compute_pet_click_zones` / `PET_INTERJECTION_PARTS`。
 * 简化为不透明包围盒纵向 40% / 32% / 28%（脸/躯干/腿）。
 */
object PetClickZones {
    const val FACE = "face"
    const val BODY = "body"
    const val LEGS = "legs"

    fun partAt(localX: Float, localY: Float, width: Int, height: Int): String? {
        if (width <= 0 || height <= 0) return null
        if (localX < 0 || localY < 0 || localX > width || localY > height) return null
        val faceEnd = height * 0.40f
        val bodyEnd = height * 0.72f
        return when {
            localY < faceEnd -> FACE
            localY < bodyEnd -> BODY
            else -> LEGS
        }
    }
}
