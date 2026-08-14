package com.vpet.mobile

import kotlin.math.abs
import kotlin.random.Random

/** 四轨谱面：对照桌面 `_build_rhythm_chart_random`（点+少量长按）。 */
object RhythmChart {
    const val LANES = 4
    const val BPM = 120
    const val TRAVEL_MS = 1400
    const val HIT_PERFECT_MS = 70
    const val HIT_GREAT_MS = 140
    const val HIT_GOOD_MS = 220
    const val HOLD_RELEASE_MS = 180
    const val SHORT_CAP_MS = 90_000

    data class Note(
        val t: Int,
        val end: Int,
        val lane: Int,
        val hold: Boolean,
        var hit: Boolean = false,
        var missed: Boolean = false,
        var headHit: Boolean = false,
        var holding: Boolean = false,
        var tailDone: Boolean = false,
    ) {
        fun isHold(): Boolean = hold && end - t >= 220
    }

    fun buildRandom(
        durationMs: Int,
        difficulty: String = "中",
        bpm: Float = BPM.toFloat(),
        seed: Int = Random.nextInt(),
    ): List<Note> {
        val dens = when (difficulty) {
            "低" -> 0.34f
            "高" -> 0.66f
            else -> 0.50f
        } * when {
            durationMs >= 180_000 -> 0.82f
            durationMs >= 120_000 -> 0.90f
            else -> 1f
        }
        val beat = 60_000f / bpm.coerceAtLeast(60f)
        val rng = Random(seed)
        val raw = ArrayList<Pair<Int, Int>>()
        var t = 2200f
        var lane = rng.nextInt(LANES)
        val endT = maxOf(4000, durationMs - 2500).toFloat()
        while (t < endT) {
            if (rng.nextFloat() < dens) {
                if (rng.nextFloat() < 0.10f) {
                    val a = rng.nextInt(LANES)
                    var b = rng.nextInt(LANES - 1)
                    if (b >= a) b++
                    raw += t.toInt() to a
                    raw += t.toInt() to b
                } else {
                    lane = (lane + listOf(-1, 1, 1, 2, -2).random(rng) + LANES * 4) % LANES
                    raw += t.toInt() to lane
                }
            }
            var step = beat * if (rng.nextFloat() < 0.22f) 0.5f else 1f
            if (rng.nextFloat() < 0.08f) step = beat * 1.5f
            t += step
        }
        raw.sortWith(compareBy({ it.first }, { it.second }))
        return annotateHolds(raw, difficulty, bpm, seed + 31)
    }

    private fun annotateHolds(
        taps: List<Pair<Int, Int>>,
        difficulty: String,
        bpm: Float,
        seed: Int,
    ): List<Note> {
        if (taps.isEmpty()) return emptyList()
        val rng = Random(seed)
        val holdP = when (difficulty) {
            "低" -> 0.10f
            "高" -> 0.22f
            else -> 0.16f
        }
        val beat = 60_000f / bpm.coerceAtLeast(60f)
        val holdLens = listOf(
            beat.toInt(),
            (beat * 1.5f).toInt(),
            (beat * 2f).toInt(),
            (beat * 2.5f).toInt(),
        )
        val byLane = Array(LANES) { ArrayList<Int>() }
        for ((t, lane) in taps) byLane[lane].add(t)
        val cursor = IntArray(LANES)
        val occupiedUntil = IntArray(LANES) { -1 }
        val out = ArrayList<Note>(taps.size)
        for ((t, lane) in taps) {
            cursor[lane]++
            val nxt = byLane[lane].getOrNull(cursor[lane])
            if (t < occupiedUntil[lane]) {
                out += Note(t = t, end = t, lane = lane, hold = false)
                continue
            }
            if (rng.nextFloat() < holdP) {
                var end = t + holdLens.random(rng)
                if (nxt != null) end = minOf(end, nxt - 140)
                if (end - t >= 260) {
                    occupiedUntil[lane] = end
                    out += Note(t = t, end = end, lane = lane, hold = true)
                    continue
                }
            }
            out += Note(t = t, end = t, lane = lane, hold = false)
        }
        return out.sortedWith(compareBy({ it.t }, { it.lane }))
    }

    fun judgment(deltaMs: Int): Pair<String, Int> {
        val ad = abs(deltaMs)
        return when {
            ad <= HIT_PERFECT_MS -> "Perfect" to RhythmGrades.SCORE_PERFECT
            ad <= HIT_GREAT_MS -> "Great" to RhythmGrades.SCORE_GREAT
            ad <= HIT_GOOD_MS -> "Good" to RhythmGrades.SCORE_GOOD
            else -> "Miss" to 0
        }
    }

    fun holdTailJudgment(deltaMs: Int): Pair<String, Int> {
        val ad = abs(deltaMs)
        return when {
            ad <= HIT_PERFECT_MS -> "Perfect" to RhythmGrades.SCORE_PERFECT
            ad <= HIT_GREAT_MS -> "Great" to RhythmGrades.SCORE_GREAT
            ad <= HOLD_RELEASE_MS -> "Good" to RhythmGrades.SCORE_GOOD
            else -> "Miss" to 0
        }
    }
}
