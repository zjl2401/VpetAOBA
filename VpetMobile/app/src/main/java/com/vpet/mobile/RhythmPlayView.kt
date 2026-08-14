package com.vpet.mobile

import android.content.Context
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.RectF
import android.util.AttributeSet
import android.view.View
import kotlin.math.max
import kotlin.math.min

/** 四轨下落 + 判定线 + 长按条；时间轴驱动（对照桌面 rhythm canvas）。 */
class RhythmPlayView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : View(context, attrs) {

    private val laneColors = intArrayOf(
        0xFF66CCFF.toInt(),
        0xFF88FFAA.toInt(),
        0xFFFFCC66.toInt(),
        0xFFFF88CC.toInt(),
    )
    private val bgPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFF0E141C.toInt() }
    private val lanePaint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val linePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = 0xE0FFFFFF.toInt()
        strokeWidth = 4f
    }
    private val notePaint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val holdPaint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val flashPaint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val judgePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        textAlign = Paint.Align.CENTER
        color = 0xFFFFEE88.toInt()
        textSize = 42f
        isFakeBoldText = true
    }
    private val comboPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        textAlign = Paint.Align.CENTER
        color = 0xFFFFFFFF.toInt()
        textSize = 28f
    }
    private val tmp = RectF()

    var notes: List<RhythmChart.Note> = emptyList()
    var nowMs: Int = 0
    var travelMs: Int = RhythmChart.TRAVEL_MS
    var keysDown: Set<Int> = emptySet()
    var laneFlashUntil: LongArray = LongArray(RhythmChart.LANES)
    var judgeText: String = ""
    var judgeUntilMs: Long = 0L
    var combo: Int = 0

    override fun onDraw(canvas: Canvas) {
        val w = width.toFloat()
        val h = height.toFloat()
        canvas.drawRect(0f, 0f, w, h, bgPaint)
        if (w <= 1f || h <= 1f) return

        val laneW = w / RhythmChart.LANES
        val hitY = h * 0.78f
        val topY = h * 0.06f
        val travelPx = hitY - topY

        for (i in 0 until RhythmChart.LANES) {
            val x0 = i * laneW
            lanePaint.color = 0x18FFFFFF
            canvas.drawRect(x0, 0f, x0 + laneW, h, lanePaint)
            val flashing = System.currentTimeMillis() < laneFlashUntil[i] || i in keysDown
            if (flashing) {
                flashPaint.color = (laneColors[i] and 0x00FFFFFF) or 0x44000000
                canvas.drawRect(x0, 0f, x0 + laneW, h, flashPaint)
            }
            lanePaint.color = (laneColors[i] and 0x00FFFFFF) or 0x33000000
            canvas.drawRect(x0 + 1f, 0f, x0 + 2.5f, h, lanePaint)
        }

        // 判定线
        canvas.drawLine(0f, hitY, w, hitY, linePaint)
        linePaint.color = 0x66FFFFFF
        canvas.drawLine(0f, hitY - 18f, w, hitY - 18f, linePaint)
        canvas.drawLine(0f, hitY + 18f, w, hitY + 18f, linePaint)
        linePaint.color = 0xE0FFFFFF.toInt()

        val lookAhead = travelMs + RhythmChart.HIT_GOOD_MS + 200
        val lookBehind = RhythmChart.HIT_GOOD_MS + 400
        for (n in notes) {
            if (n.hit || n.missed || n.tailDone) continue
            val t = n.t
            if (t > nowMs + lookAhead) break
            if (n.end < nowMs - lookBehind && !n.holding) continue

            val cx = n.lane * laneW + laneW * 0.5f
            val noteR = min(laneW * 0.28f, 28f)
            val yHead = yForTime(t, hitY, travelPx)
            val color = laneColors[n.lane]

            if (n.isHold()) {
                val yTail = yForTime(n.end, hitY, travelPx)
                val top = min(yHead, yTail)
                val bot = max(yHead, yTail)
                holdPaint.color = (color and 0x00FFFFFF) or 0x99000000.toInt()
                val half = noteR * 0.45f
                tmp.set(cx - half, top, cx + half, bot)
                canvas.drawRoundRect(tmp, half, half, holdPaint)
                if (n.holding) {
                    holdPaint.color = (color and 0x00FFFFFF) or 0xCC000000.toInt()
                    val holdBot = hitY
                    tmp.set(cx - half, min(yTail, holdBot), cx + half, holdBot)
                    canvas.drawRoundRect(tmp, half, half, holdPaint)
                }
            }

            if (!n.headHit) {
                notePaint.color = color
                canvas.drawCircle(cx, yHead, noteR, notePaint)
                notePaint.color = 0xEEFFFFFF.toInt()
                canvas.drawCircle(cx, yHead, noteR * 0.35f, notePaint)
            } else if (n.holding) {
                notePaint.color = color
                canvas.drawCircle(cx, hitY, noteR * 0.85f, notePaint)
            }
        }

        if (combo > 1) {
            canvas.drawText("${combo} COMBO", w * 0.5f, h * 0.12f, comboPaint)
        }
        if (judgeText.isNotEmpty() && System.currentTimeMillis() < judgeUntilMs) {
            judgePaint.color = when (judgeText) {
                "Perfect" -> 0xFFFF88CC.toInt()
                "Great" -> 0xFF88DD88.toInt()
                "Good" -> 0xFF4488FF.toInt()
                else -> 0xFFFF6666.toInt()
            }
            canvas.drawText(judgeText, w * 0.5f, hitY - 48f, judgePaint)
        }
    }

    private fun yForTime(t: Int, hitY: Float, travelPx: Float): Float {
        val dt = (t - nowMs).toFloat()
        return hitY - (dt / travelMs.coerceAtLeast(1)) * travelPx
    }

    fun hitLineY(): Float = height * 0.78f
}
