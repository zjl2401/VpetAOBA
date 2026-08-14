package com.vpet.mobile

/** 音游评级：对照 RHYTHM_GRADE_TIERS / coin_map。 */
object RhythmGrades {
    const val SCORE_PERFECT = 300
    const val SCORE_GREAT = 200
    const val SCORE_GOOD = 100

    data class Result(
        val grade: String,
        val label: String,
        val colorHex: String,
        val accuracy: Int,
        val coinGain: Int,
    )

    fun accuracy(perfect: Int, great: Int, good: Int, miss: Int): Int {
        val total = perfect + great + good + miss
        if (total <= 0) return 0
        val acc = 100.0 * (perfect * 1.0 + great * 0.8 + good * 0.5) / total
        return acc.toInt().coerceIn(0, 100)
    }

    fun gradeOf(acc: Int): Result {
        val (g, label, color) = when {
            acc >= 95 -> Triple("S", "完美", "#FF88CC")
            acc >= 85 -> Triple("A", "优秀", "#88DD88")
            acc >= 70 -> Triple("B", "良好", "#4488FF")
            acc >= 50 -> Triple("C", "及格", "#FFAA44")
            else -> Triple("D", "加油", "#FF6666")
        }
        val coins = when (g) {
            "S" -> 12
            "A" -> 8
            "B" -> 5
            "C" -> 3
            else -> 1
        }
        return Result(g, label, color, acc, coins)
    }
}
