package com.vpet.mobile

import android.content.Context

/** 难度参数：对照桌面 `_difficulty_params`（采集 / 暴露子集）。 */
object DifficultyParams {
    data class Params(
        val gameSpeed: Float,
        val gameSpawnMs: Long,
        val gameCatchDistDp: Float,
        val gameCatchBonus: Int, // unused; reserved
        val exposeZoneWidthFrac: Float, // 相对父宽
        val exposePointerSpeedDp: Float,
        val exposeHitsNeed: Int,
        val exposeFailStaminaPct: Float,
        val exposeFailMoodPct: Float,
        val exposeClearMood: Int,
    )

    fun of(ctx: Context): Params = ofLabel(AppDataStore.difficulty(ctx))

    fun ofLabel(label: String): Params = when (label) {
        "低" -> Params(
            gameSpeed = 4f,
            gameSpawnMs = 1350L,
            gameCatchDistDp = 58f,
            gameCatchBonus = 0,
            exposeZoneWidthFrac = 0.42f,
            exposePointerSpeedDp = 3.4f,
            exposeHitsNeed = 5,
            exposeFailStaminaPct = 0.30f,
            exposeFailMoodPct = 0.30f,
            exposeClearMood = 5,
        )
        "高" -> Params(
            gameSpeed = 7f,
            gameSpawnMs = 820L,
            gameCatchDistDp = 40f,
            gameCatchBonus = 0,
            exposeZoneWidthFrac = 0.22f,
            exposePointerSpeedDp = 6.2f,
            exposeHitsNeed = 5,
            exposeFailStaminaPct = 0.65f,
            exposeFailMoodPct = 0.65f,
            exposeClearMood = 5,
        )
        else -> Params( // 中
            gameSpeed = 5f,
            gameSpawnMs = 1100L,
            gameCatchDistDp = 48f,
            gameCatchBonus = 0,
            exposeZoneWidthFrac = 0.32f,
            exposePointerSpeedDp = 4.5f,
            exposeHitsNeed = 5,
            exposeFailStaminaPct = 0.50f,
            exposeFailMoodPct = 0.50f,
            exposeClearMood = 5,
        )
    }
}
