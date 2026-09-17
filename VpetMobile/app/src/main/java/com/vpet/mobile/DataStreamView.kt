package com.vpet.mobile

import android.content.Context
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.Typeface
import android.util.AttributeSet
import android.view.View
import kotlin.random.Random

/**
 * 开启页数据流背景：竖直下落的比特/十六进制字符雨。
 * 粉蓝主题，低透明度，不挡前景按钮。
 */
class DataStreamView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0,
) : View(context, attrs, defStyleAttr) {

    private data class Drop(
        var y: Float,
        var speed: Float,
        var glyphs: CharArray,
        var head: Int,
        var bright: Boolean,
    )

    private val columns = ArrayList<Drop>()
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        typeface = Typeface.MONOSPACE
        textAlign = Paint.Align.CENTER
    }
    private val rng = Random(System.nanoTime())
    private var colWidth = 0f
    private var running = false
    private var lastFrameMs = 0L

    private val glyphPool = (
        "0123456789ABCDEF" +
            "01アイウエオカキクケコサシスセソタチツテト" +
            "◇◆░▒▓※→←↑↓"
        ).toCharArray()

    private val tick = object : Runnable {
        override fun run() {
            if (!running) return
            val now = System.currentTimeMillis()
            val dt = ((now - lastFrameMs).coerceIn(8L, 48L)) / 16.5f
            lastFrameMs = now
            step(dt)
            invalidate()
            postOnAnimation(this)
        }
    }

    override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
        super.onSizeChanged(w, h, oldw, oldh)
        rebuildColumns(w, h)
    }

    private fun rebuildColumns(w: Int, h: Int) {
        columns.clear()
        if (w <= 0 || h <= 0) return
        val density = resources.displayMetrics.density
        colWidth = (14f * density).coerceAtLeast(12f)
        paint.textSize = colWidth * 0.85f
        val count = ((w / colWidth).toInt() + 1).coerceIn(8, 28)
        for (i in 0 until count) {
            columns += newDrop(h.toFloat(), spawnAbove = true)
        }
    }

    private fun newDrop(height: Float, spawnAbove: Boolean): Drop {
        val len = rng.nextInt(8, 18)
        val glyphs = CharArray(len) { glyphPool[rng.nextInt(glyphPool.size)] }
        val y = if (spawnAbove) {
            -rng.nextFloat() * height * 0.6f - len * colWidth
        } else {
            rng.nextFloat() * height
        }
        return Drop(
            y = y,
            speed = colWidth * (0.35f + rng.nextFloat() * 0.85f),
            glyphs = glyphs,
            head = rng.nextInt(glyphs.size),
            bright = rng.nextFloat() < 0.28f,
        )
    }

    private fun step(dt: Float) {
        val h = height.toFloat()
        if (h <= 0f || columns.isEmpty()) return
        for (i in columns.indices) {
            val d = columns[i]
            d.y += d.speed * dt
            if (rng.nextFloat() < 0.08f * dt) {
                d.head = (d.head + 1) % d.glyphs.size
                d.glyphs[d.head] = glyphPool[rng.nextInt(glyphPool.size)]
            }
            val trail = d.glyphs.size * colWidth
            if (d.y - trail > h + colWidth) {
                columns[i] = newDrop(h, spawnAbove = true)
            }
        }
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        if (columns.isEmpty() || colWidth <= 0f) return
        val h = height.toFloat()
        for (i in columns.indices) {
            val d = columns[i]
            val x = (i + 0.5f) * colWidth
            if (x > width + colWidth) continue
            val pinkish = d.bright
            for (g in d.glyphs.indices) {
                val gy = d.y - g * colWidth
                if (gy < -colWidth || gy > h + colWidth) continue
                val t = g.toFloat() / d.glyphs.size.coerceAtLeast(1)
                val alpha = when {
                    g == 0 -> 170
                    g == 1 -> 120
                    else -> (28 + (1f - t) * 70f).toInt().coerceIn(18, 100)
                }
                paint.color = if (pinkish && g <= 1) {
                    argb(alpha, 255, 126, 176)
                } else {
                    argb(alpha, 126, 200, 255)
                }
                canvas.drawText(d.glyphs[(d.head + g) % d.glyphs.size].toString(), x, gy, paint)
            }
        }
        // 轻扫描线：加强「数据流」感
        paint.strokeWidth = 1f
        paint.color = argb(18, 255, 255, 255)
        var sy = (System.currentTimeMillis() / 28L % height).toFloat()
        canvas.drawLine(0f, sy, width.toFloat(), sy, paint)
        sy = (sy + height * 0.37f) % height
        paint.color = argb(12, 255, 126, 176)
        canvas.drawLine(0f, sy, width.toFloat(), sy, paint)
    }

    private fun argb(a: Int, r: Int, g: Int, b: Int): Int =
        (a.coerceIn(0, 255) shl 24) or (r shl 16) or (g shl 8) or b

    fun start() {
        if (running) return
        running = true
        lastFrameMs = System.currentTimeMillis()
        postOnAnimation(tick)
    }

    fun stop() {
        running = false
        removeCallbacks(tick)
    }

    override fun onAttachedToWindow() {
        super.onAttachedToWindow()
        start()
    }

    override fun onDetachedFromWindow() {
        stop()
        super.onDetachedFromWindow()
    }

    override fun onVisibilityChanged(changedView: View, visibility: Int) {
        super.onVisibilityChanged(changedView, visibility)
        if (visibility == VISIBLE) start() else stop()
    }
}
