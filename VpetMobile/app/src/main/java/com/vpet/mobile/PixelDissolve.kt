package com.vpet.mobile

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import android.os.Handler
import android.os.Looper
import android.view.View
import android.widget.ImageView
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin

/**
 * 像素块进出场溶解。对照桌面 `_run_pixel_block_dissolve_animation`（radial 固定风格）。
 * reverse=false 入场；reverse=true 出场。
 *
 * 抓屏后 letterbox 成正方形再切块（勿把非正方形直接 sx/sy 拉扁）。
 */
object PixelDissolve {
    const val FRAME_MS = 28L
    const val FRAMES = 32

    private data class Spec(
        val tx: Float,
        val ty: Float,
        val color: Int,
        val driftX: Float,
        val driftY: Float,
        val delay: Float,
        val wobble: Float,
        val spin: Float,
    )

    fun play(
        target: ImageView,
        reverse: Boolean,
        totalMs: Long? = null,
        onDone: (() -> Unit)? = null,
    ) {
        if (target.width <= 0 || target.height <= 0) {
            target.post { play(target, reverse, totalMs, onDone) }
            return
        }
        val captured = capture(target) ?: run {
            onDone?.invoke()
            return
        }
        val side = max(captured.width, captured.height).coerceAtLeast(1)
        val square = letterboxToSquare(captured, side)
        if (square !== captured) {
            try {
                captured.recycle()
            } catch (_: Exception) {
            }
        }
        val (bs, specs) = buildSpecs(square, side)
        try {
            square.recycle()
        } catch (_: Exception) {
        }
        if (specs.isEmpty()) {
            onDone?.invoke()
            return
        }
        val parent = target.parent as? android.view.ViewGroup ?: run {
            onDone?.invoke()
            return
        }
        val frames = if (totalMs != null && totalMs > 0) {
            max(16, min(64, (totalMs / FRAME_MS).toInt()))
        } else {
            FRAMES
        }
        val ms = if (totalMs != null && totalMs > 0) {
            max(10L, totalMs / frames)
        } else {
            FRAME_MS
        }
        // 叠层对齐 ImageView 中心（letterbox 后边长可能 ≥ 视图边）
        val left = target.left + (target.width - side) / 2
        val top = target.top + (target.height - side) / 2
        val overlay = object : View(target.context) {
            private var phase = 0
            private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
            private val handler = Handler(Looper.getMainLooper())
            private val self = this
            private val tick = object : Runnable {
                override fun run() {
                    invalidate()
                    phase++
                    if (phase < frames) {
                        handler.postDelayed(this, ms)
                    } else {
                        try {
                            parent.removeView(self)
                        } catch (_: Exception) {
                        }
                        target.visibility = View.VISIBLE
                        onDone?.invoke()
                    }
                }
            }

            override fun onDraw(canvas: Canvas) {
                drawFrame(canvas, specs, bs, side, phase, frames, reverse, paint)
            }

            fun start() {
                target.visibility = View.INVISIBLE
                handler.post(tick)
            }
        }
        val lp = android.widget.FrameLayout.LayoutParams(side, side)
        if (parent is android.widget.FrameLayout) {
            lp.gravity = android.view.Gravity.TOP or android.view.Gravity.START
            lp.leftMargin = left
            lp.topMargin = top
        }
        parent.addView(overlay, lp)
        overlay.start()
    }

    /** 按 ImageView 实际绘制抓屏（含 scaleType），避免 drawable.setBounds 二次拉伸。 */
    private fun capture(iv: ImageView): Bitmap? {
        val w = iv.width.coerceAtLeast(1)
        val h = iv.height.coerceAtLeast(1)
        if (iv.drawable == null) return null
        val bmp = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp)
        iv.draw(c)
        return bmp
    }

    /** 保持宽高比贴入正方形，空白透明（对照桌面已是 size×size 的 rgba）。 */
    private fun letterboxToSquare(src: Bitmap, side: Int): Bitmap {
        if (src.width == side && src.height == side) return src
        val out = Bitmap.createBitmap(side, side, Bitmap.Config.ARGB_8888)
        val c = Canvas(out)
        val left = (side - src.width) / 2f
        val top = (side - src.height) / 2f
        c.drawBitmap(src, left, top, null)
        return out
    }

    private fun buildSpecs(img: Bitmap, size: Int): Pair<Int, List<Spec>> {
        // 图像已是 size×size：按桌面直接用格点坐标采样，禁止 sx/sy 非等比拉伸
        val bs = max(3, max(4, size / 18) - 1)
        val cols = max(1, (size + bs - 1) / bs)
        val rows = max(1, (size + bs - 1) / bs)
        val mid = size * 0.5f
        val specs = ArrayList<Spec>(cols * rows)
        for (row in 0 until rows) {
            for (col in 0 until cols) {
                val x0 = col * bs
                val y0 = row * bs
                val x1 = min(size, x0 + bs)
                val y1 = min(size, y0 + bs)
                val color = avgColor(img, x0, y0, x1, y1) ?: continue
                val cx = x0 + bs * 0.5f
                val cy = y0 + bs * 0.5f
                val fromCx = cx - mid
                val fromCy = cy - mid
                val radial = hypot(fromCx.toDouble(), fromCy.toDouble()).toFloat().coerceAtLeast(1f)
                val ang = atan2(fromCy, fromCx)
                val spin = if ((row + col) % 2 == 0) 1.1f else -1.1f
                val mag = 1.1f * bs * 1.4f
                val driftX = fromCx / radial * bs * 0.95f + cos(ang) * mag * 0.35f
                val driftY = fromCy / radial * bs * 0.85f + sin(ang) * mag * 0.35f
                val delay = min(0.8f, (row / max(1, rows - 1).toFloat()) * 0.3f)
                val wobble = ((row * 0.37f + col * 0.21f) % (Math.PI.toFloat() * 2f))
                specs.add(Spec(x0.toFloat(), y0.toFloat(), color, driftX, driftY, delay, wobble, spin))
            }
        }
        return bs to specs
    }

    private fun avgColor(img: Bitmap, x0: Int, y0: Int, x1: Int, y1: Int): Int? {
        val l = x0.coerceIn(0, img.width - 1)
        val t = y0.coerceIn(0, img.height - 1)
        val r = x1.coerceIn(l + 1, img.width)
        val b = y1.coerceIn(t + 1, img.height)
        var sr = 0L; var sg = 0L; var sb = 0L; var sa = 0L; var n = 0
        var y = t
        while (y < b) {
            var x = l
            while (x < r) {
                val c = img.getPixel(x, y)
                val a = Color.alpha(c)
                if (a > 24) {
                    sr += Color.red(c); sg += Color.green(c); sb += Color.blue(c); sa += a; n++
                }
                x++
            }
            y++
        }
        if (n == 0) return null
        return Color.argb((sa / n).toInt(), (sr / n).toInt(), (sg / n).toInt(), (sb / n).toInt())
    }

    private fun drawFrame(
        canvas: Canvas,
        specs: List<Spec>,
        blockSize: Int,
        size: Int,
        phase: Int,
        total: Int,
        reverse: Boolean,
        paint: Paint,
    ) {
        canvas.drawColor(Color.TRANSPARENT)
        val tGlobal = phase / max(1, total - 1).toFloat()
        val home = blockSize * 0.5f
        for (s in specs) {
            val stagger = s.delay * 0.42f
            val denom = max(0.16f, 1f - stagger * 0.45f)
            val tLocal = min(1f, max(0f, (tGlobal - stagger * 0.28f) / denom))
            val (remain, alpha, scale) = if (reverse) {
                val te = tLocal * tLocal * tLocal
                Triple(te, 1f - te, 1f - te * 0.3f)
            } else {
                val te = if (tLocal < 0.5f) {
                    2f * tLocal * tLocal
                } else {
                    val u = -2f * tLocal + 2f
                    1f - u * u / 2f
                }
                Triple(1f - te, te, 0.5f + te * 0.5f)
            }
            if (alpha < 0.05f) continue
            val ox = sin(s.wobble + (1f - remain) * Math.PI.toFloat()) * blockSize * 0.1f * remain
            val oy = ox * 0.45f
            var cx = s.tx + home + s.driftX * remain + ox
            var cy = s.ty + home + s.driftY * remain + oy
            if (reverse) cy -= (1f - alpha) * blockSize * 0.15f
            val half = blockSize * scale * 0.5f
            val x1 = (cx - half).toInt()
            val y1 = (cy - half).toInt()
            val x2 = (cx + half).toInt()
            val y2 = (cy + half).toInt()
            if (x2 <= 0 || y2 <= 0 || x1 >= size || y1 >= size) continue
            paint.color = s.color
            paint.alpha = (alpha * Color.alpha(s.color)).toInt().coerceIn(0, 255)
            canvas.drawRect(Rect(x1, y1, x2, y2), paint)
        }
    }
}
