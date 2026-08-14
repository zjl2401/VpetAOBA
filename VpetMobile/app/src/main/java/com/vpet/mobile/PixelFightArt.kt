package com.vpet.mobile

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt

/** 莱姆 / RPG 判定用像素绘制（对照桌面 `_draw_pixel_die` / fighter / rps）。 */
object PixelFightArt {
    private val pips: Map<Int, List<Pair<Int, Int>>> = mapOf(
        1 to listOf(0 to 0),
        2 to listOf(-1 to -1, 1 to 1),
        3 to listOf(-1 to -1, 0 to 0, 1 to 1),
        4 to listOf(-1 to -1, 1 to -1, -1 to 1, 1 to 1),
        5 to listOf(-1 to -1, 1 to -1, 0 to 0, -1 to 1, 1 to 1),
        6 to listOf(-1 to -1, 1 to -1, -1 to 0, 1 to 0, -1 to 1, 1 to 1),
    )

    fun dieBitmap(sizePx: Int, value: Int): Bitmap {
        val size = sizePx.coerceAtLeast(24)
        val v = value.coerceIn(1, 6)
        val bmp = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp)
        val face = Color.parseColor("#F4F0E6")
        val pip = Color.parseColor("#222233")
        val edge = Color.parseColor("#888899")
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.FILL }
        paint.color = edge
        c.drawRect(1f, 1f, size - 1f, size - 1f, paint)
        paint.color = face
        c.drawRect(2f, 2f, size - 2f, size - 2f, paint)
        val pipR = max(2, size / 10).toFloat()
        val cx = size / 2f
        val step = size / 4f
        paint.color = pip
        for ((ox, oy) in pips.getValue(v)) {
            val x = cx + ox * step
            val y = cx + oy * step
            c.drawOval(RectF(x - pipR, y - pipR, x + pipR, y + pipR), paint)
        }
        return bmp
    }

    /** side: player | opponent | jinmu */
    fun fighterBitmap(sizePx: Int, side: String): Bitmap {
        val size = sizePx.coerceAtLeast(32)
        val bmp = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp)
        val px = max(3, size / 10)
        val (body, accent, eye) = when (side) {
            "jinmu" -> Triple("#2A6FC0", "#A8DCFF", "#FF66AA")
            "player" -> Triple("#88CCFF", "#FFFFFF", "#66F0FF")
            else -> Triple("#FF8844", "#FFDDAA", "#FF6644")
        }
        val paint = Paint().apply { style = Paint.Style.FILL; isAntiAlias = false }
        fun fill(hex: String) {
            paint.color = Color.parseColor(hex)
        }
        fun box(l: Int, t: Int, r: Int, b: Int, hex: String) {
            fill(hex)
            c.drawRect(l.toFloat(), t.toFloat(), r.toFloat(), b.toFloat(), paint)
        }
        val cx = size / 2
        val foot = size - px
        box(cx - px, foot - px * 4, cx + px, foot - px * 2, body)
        box(cx - px * 2, foot - px * 6, cx + px * 2, foot - px * 4, body)
        box(cx - px * 2, foot - px * 8, cx + px * 2, foot - px * 6, accent)
        box(cx - px, foot - px * 7, cx - px / 2, foot - px * 6, eye)
        box(cx + px / 2, foot - px * 7, cx + px, foot - px * 6, eye)
        if (side == "opponent") {
            box(cx - px * 3, foot - px * 9, cx - px, foot - px * 7, "#FF6644")
        }
        if (side == "jinmu") {
            box(cx - px * 3, foot - px * 9, cx - px * 2, foot - px * 8, "#66F0FF")
            box(cx + px * 2, foot - px * 9, cx + px * 3, foot - px * 8, "#FF4DB8")
        }
        return bmp
    }

    fun hpBarBitmap(
        width: Int,
        height: Int,
        current: Int,
        maximum: Int,
        fillHex: String,
        lowHex: String = "#FF4455",
    ): Bitmap {
        val w = width.coerceAtLeast(40)
        val h = height.coerceAtLeast(10)
        val bmp = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp)
        val paint = Paint().apply { style = Paint.Style.FILL; isAntiAlias = false }
        paint.color = Color.parseColor("#1A2233")
        c.drawRect(0f, 0f, w.toFloat(), h.toFloat(), paint)
        paint.color = Color.parseColor("#3A4A66")
        c.drawRect(0f, 0f, w.toFloat(), 1f, paint)
        c.drawRect(0f, (h - 1).toFloat(), w.toFloat(), h.toFloat(), paint)
        c.drawRect(0f, 0f, 1f, h.toFloat(), paint)
        c.drawRect((w - 1).toFloat(), 0f, w.toFloat(), h.toFloat(), paint)
        val maxHp = maximum.coerceAtLeast(1)
        val ratio = (current.toFloat() / maxHp).coerceIn(0f, 1f)
        val fw = ((w - 2) * ratio).roundToInt()
        if (fw > 0) {
            paint.color = Color.parseColor(if (ratio <= 0.28f) lowHex else fillHex)
            c.drawRect(1f, 1f, (1 + fw).toFloat(), (h - 1).toFloat(), paint)
        }
        paint.color = Color.parseColor("#0A0E18")
        for (i in 1..3) {
            val x = (w * i / 4f)
            c.drawRect(x, 1f, x + 1f, (h - 1).toFloat(), paint)
        }
        return bmp
    }

    /** 1石头 2剪刀 3布 */
    fun rpsBitmap(sizePx: Int, kind: Int, selected: Boolean = false): Bitmap {
        val size = sizePx.coerceAtLeast(48)
        val bmp = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp)
        val paint = Paint(Paint.ANTI_ALIAS_FLAG)
        val bg = if (selected) Color.parseColor("#2A4060") else Color.parseColor("#1A2233")
        paint.color = bg
        val pad = size * 0.06f
        c.drawRoundRect(RectF(pad, pad, size - pad, size - pad), size * 0.12f, size * 0.12f, paint)
        paint.color = Color.parseColor("#8899AA")
        paint.style = Paint.Style.STROKE
        paint.strokeWidth = max(2f, size * 0.03f)
        c.drawRoundRect(RectF(pad, pad, size - pad, size - pad), size * 0.12f, size * 0.12f, paint)
        paint.style = Paint.Style.FILL
        val cx = size / 2f
        val cy = size / 2f
        when (kind.coerceIn(1, 3)) {
            1 -> { // rock
                paint.color = Color.parseColor("#CCDDEE")
                c.drawCircle(cx, cy + size * 0.02f, size * 0.28f, paint)
                paint.color = Color.parseColor("#8899AA")
                c.drawCircle(cx - size * 0.08f, cy - size * 0.06f, size * 0.08f, paint)
            }
            2 -> { // scissors
                paint.color = Color.parseColor("#EEF2FF")
                paint.strokeWidth = max(3f, size * 0.06f)
                paint.style = Paint.Style.STROKE
                paint.strokeCap = Paint.Cap.ROUND
                c.drawLine(cx - size * 0.18f, cy + size * 0.2f, cx + size * 0.05f, cy - size * 0.22f, paint)
                c.drawLine(cx + size * 0.18f, cy + size * 0.2f, cx - size * 0.05f, cy - size * 0.22f, paint)
                paint.style = Paint.Style.FILL
                paint.color = Color.parseColor("#FFCC66")
                c.drawCircle(cx - size * 0.18f, cy + size * 0.2f, size * 0.07f, paint)
                c.drawCircle(cx + size * 0.18f, cy + size * 0.2f, size * 0.07f, paint)
            }
            else -> { // paper
                paint.color = Color.parseColor("#EEF6FF")
                val l = cx - size * 0.22f
                val t = cy - size * 0.28f
                c.drawRoundRect(RectF(l, t, l + size * 0.44f, t + size * 0.56f), 4f, 4f, paint)
                paint.color = Color.parseColor("#88AACC")
                paint.strokeWidth = max(2f, size * 0.03f)
                paint.style = Paint.Style.STROKE
                for (i in 0..2) {
                    val y = t + size * (0.16f + i * 0.12f)
                    c.drawLine(l + size * 0.08f, y, l + size * 0.36f, y, paint)
                }
            }
        }
        return bmp
    }

    fun difficultyT(label: String): Float = when (label) {
        "低" -> 0.15f
        "高" -> 0.85f
        else -> 0.5f
    }

    fun diceThreshold(action: String, difficultyT: Float): Int {
        val t = difficultyT.coerceIn(0f, 1f)
        val base = 2 + (t * 2).roundToInt() // 2..4
        return when (action) {
            "special", "defense" -> min(6, base + 1)
            else -> min(6, base)
        }
    }

    fun playerMult(label: String): Float = when (label) {
        "低" -> 1.15f
        "高" -> 0.9f
        else -> 1f
    }

    fun enemyMult(label: String): Float = when (label) {
        "低" -> 0.85f
        "高" -> 1.2f
        else -> 1f
    }
}
