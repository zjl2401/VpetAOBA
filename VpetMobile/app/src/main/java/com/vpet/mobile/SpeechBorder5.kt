package com.vpet.mobile

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Paint
import kotlin.math.max
import kotlin.math.min

/**
 * 系统→对话 border5：对照桌面 `_compose_speech_border2`（左右帽+中段拉伸，非完整九宫格面板）。
 */
object SpeechBorder5 {
    private const val SRC_LEFT = 200
    private const val SRC_RIGHT = 130
    private const val MIN_H = 78
    private const val MIN_W = 236
    private const val MAX_W = 760
    private const val MAX_H = 420
    private const val UI_SCALE = 1.18f
    private const val TEXT_WRAP = 520
    private const val EDGE_SLACK = 12

    private var base: Bitmap? = null
    private val cache = mutableMapOf<Pair<Int, Int>, Bitmap>()

    fun ensureBase(context: Context): Bitmap? {
        base?.let { return it }
        return try {
            context.assets.open("ui/border5.jpg").use { stream ->
                val raw = BitmapFactory.decodeStream(stream) ?: return null
                // 对照桌面 _strip_border2_outer_white：抠掉贴边白圈
                base = stripNearBlackEdge(raw)
                cache.clear()
                base
            }
        } catch (_: Exception) {
            null
        }
    }

    fun compose(context: Context, contentW: Int, contentH: Int): Bitmap? {
        val src = ensureBase(context) ?: return null
        val (tw, th, padL, padT, padR, padB) = targetSize(contentW, contentH)
        val key = tw to th
        cache[key]?.let { return it }
        val scale = th / max(1, src.height).toFloat()
        val scaledW = max(1, (src.width * scale).toInt())
        val scaled = Bitmap.createScaledBitmap(src, scaledW, th, false)
        var left = min((SRC_LEFT * scale).toInt(), max(1, scaledW / 3))
        var right = min((SRC_RIGHT * scale).toInt(), max(1, scaledW / 4))
        if (left + right >= scaledW) {
            left = max(1, scaledW / 3)
            right = max(1, scaledW / 4)
        }
        val leftCap = Bitmap.createBitmap(scaled, 0, 0, left, th)
        val rightCap = Bitmap.createBitmap(scaled, scaledW - right, 0, right, th)
        val midSrc = Bitmap.createBitmap(scaled, left, 0, max(1, scaledW - left - right), th)
        val midW = max(8, tw - leftCap.width - rightCap.width)
        val mid = Bitmap.createScaledBitmap(midSrc, midW, th, false)
        val out = Bitmap.createBitmap(tw, th, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(out)
        val paint = Paint(Paint.FILTER_BITMAP_FLAG)
        canvas.drawBitmap(leftCap, 0f, 0f, paint)
        canvas.drawBitmap(mid, leftCap.width.toFloat(), 0f, paint)
        canvas.drawBitmap(rightCap, (tw - rightCap.width).toFloat(), 0f, paint)
        // 不透明内容底
        val fill = Paint().apply { color = 0xFF1A1A22.toInt() }
        canvas.drawRect(
            padL.toFloat(),
            padT.toFloat(),
            (tw - padR).toFloat(),
            (th - padB).toFloat(),
            fill,
        )
        if (cache.size > 48) cache.clear()
        cache[key] = out
        return out
    }

    fun padsFor(contentW: Int, contentH: Int): IntArray {
        val (_, _, padL, padT, padR, padB) = targetSize(contentW, contentH)
        return intArrayOf(padL, padT, padR, padB)
    }

    fun wrapFor(contentW: Int): Int = max(80, contentW - EDGE_SLACK)

    fun measureContent(text: String, textSizePx: Float): Pair<Int, Int> {
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply { textSize = textSizePx }
        val maxLine = TEXT_WRAP.toFloat()
        var w = 0f
        var lines = 1
        var lineW = 0f
        for (ch in text) {
            if (ch == '\n') {
                w = max(w, lineW)
                lineW = 0f
                lines++
                continue
            }
            val cw = paint.measureText(ch.toString())
            if (lineW + cw > maxLine && lineW > 0f) {
                w = max(w, lineW)
                lineW = cw
                lines++
            } else {
                lineW += cw
            }
        }
        w = max(w, lineW)
        val h = (paint.fontSpacing * lines + 8f).toInt()
        return max(40, w.toInt()) to max(24, h)
    }

    private data class Target(
        val w: Int,
        val h: Int,
        val padL: Int,
        val padT: Int,
        val padR: Int,
        val padB: Int,
    )

    private fun targetSize(contentW: Int, contentH: Int): Target {
        val keepInnerW = min(contentW, TEXT_WRAP)
        val srcH = max(1, base?.height ?: MIN_H)
        val scaleBase = maxOf(
            contentW / max(1f, (base?.width ?: MIN_W) - SRC_LEFT - SRC_RIGHT.toFloat()),
            contentH / max(1f, srcH - 35f - 28f),
            MIN_H / srcH.toFloat(),
        )
        val scale = scaleBase * UI_SCALE
        val left = max(14, (SRC_LEFT * scale).toInt())
        val right = max(18, (SRC_RIGHT * scale).toInt())
        val top = max(8, (35 * scale).toInt())
        val bottom = max(8, (28 * scale).toInt())
        val tw = max(MIN_W, min(MAX_W, contentW + left + right))
        var th = max(MIN_H, contentH + top + bottom)
        if (th > MAX_H) th = MAX_H
        return Target(tw, th, left, top, right, bottom)
    }

    private fun stripNearBlackEdge(src: Bitmap): Bitmap {
        // 桌面 border5 用外圈白色洪水填充透明（_strip_border2_outer_white）
        return stripOuterKey(src) { r, g, b, a ->
            a > 80 && r > 198 && g > 198 && b > 198
        }
    }

    /** 从四边洪水抠色为透明。 */
    private fun stripOuterKey(src: Bitmap, isKey: (r: Int, g: Int, b: Int, a: Int) -> Boolean): Bitmap {
        val w = src.width
        val h = src.height
        val out = src.copy(Bitmap.Config.ARGB_8888, true)
        val px = IntArray(w * h)
        out.getPixels(px, 0, w, 0, 0, w, h)
        fun key(i: Int): Boolean {
            val c = px[i]
            val a = (c ushr 24) and 0xFF
            val r = (c ushr 16) and 0xFF
            val g = (c ushr 8) and 0xFF
            val b = c and 0xFF
            return isKey(r, g, b, a)
        }
        val visited = BooleanArray(w * h)
        val q = ArrayDeque<Int>()
        fun enq(x: Int, y: Int) {
            if (x !in 0 until w || y !in 0 until h) return
            val i = y * w + x
            if (visited[i] || !key(i)) return
            visited[i] = true
            q.add(i)
        }
        for (x in 0 until w) {
            enq(x, 0); enq(x, h - 1)
        }
        for (y in 0 until h) {
            enq(0, y); enq(w - 1, y)
        }
        while (q.isNotEmpty()) {
            val i = q.removeFirst()
            px[i] = 0
            val x = i % w
            val y = i / w
            enq(x - 1, y); enq(x + 1, y); enq(x, y - 1); enq(x, y + 1)
        }
        out.setPixels(px, 0, w, 0, 0, w, h)
        return out
    }
}