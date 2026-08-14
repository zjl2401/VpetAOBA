package com.vpet.mobile

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.PixelFormat
import android.graphics.drawable.BitmapDrawable
import android.graphics.drawable.GradientDrawable
import android.os.Handler
import android.os.Looper
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.FrameLayout
import kotlin.math.cos
import kotlin.math.sin

/**
 * 对照桌面 panel_decor：菜单 chrome、像素小图标、点击粒子散开。
 */
object MenuDecor {
    val THEME_BLUE = Color.parseColor("#66CCFF")
    val THEME_PINK = Color.parseColor("#FF88CC")
    val THEME_BLUE_DEEP = Color.parseColor("#4488DD")
    val THEME_WHITE = Color.parseColor("#F4F8FF")
    val THEME_BLACK = Color.parseColor("#0A0C12")
    val MENU_BG = Color.parseColor("#E0141824")
    val MENU_FG = Color.parseColor("#EEF2FF")
    val MENU_ACTIVE = Color.parseColor("#E02A3558")
    val THEME_ITEM_BG = Color.parseColor("#E0181F34")

    private val glyphColors = intArrayOf(THEME_BLUE_DEEP, THEME_BLUE, THEME_PINK, THEME_BLACK, THEME_WHITE)
    private val glyphCache = HashMap<Pair<String, Int>, Bitmap>()

    fun dp(ctx: Context, v: Float): Int =
        TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v, ctx.resources.displayMetrics).toInt()

    fun chromeOuterBg(): GradientDrawable = GradientDrawable().apply {
        setColor(THEME_BLUE)
    }

    fun menuItemBg(pressed: Boolean = false): GradientDrawable = GradientDrawable().apply {
        setColor(if (pressed) MENU_ACTIVE else THEME_ITEM_BG)
        cornerRadius = 2f
    }

    fun moduleBtnBg(selected: Boolean): GradientDrawable = GradientDrawable().apply {
        setColor(if (selected) MENU_ACTIVE else MENU_BG)
        setStroke(1, if (selected) THEME_PINK else THEME_BLUE_DEEP)
        cornerRadius = 2f
    }

    fun glyphDrawable(ctx: Context, label: String, sizeDp: Float = 14f): BitmapDrawable {
        val px = dp(ctx, sizeDp).coerceAtLeast(8)
        val bmp = glyphBitmap(label, px)
        return BitmapDrawable(ctx.resources, bmp).apply {
            setBounds(0, 0, px, px)
        }
    }

    fun glyphBitmap(label: String, sizePx: Int): Bitmap {
        val key = label to sizePx
        glyphCache[key]?.let { return it }
        val seed = label.hashCode() and 0xFFFF
        val img = makeGlyph8(seed)
        val out = Bitmap.createScaledBitmap(img, sizePx, sizePx, false)
        glyphCache[key] = out
        return out
    }

    private fun makeGlyph8(seed: Int): Bitmap {
        val base = Bitmap.createBitmap(8, 8, Bitmap.Config.ARGB_8888)
        val pts = glyphPattern(seed)
        for ((x, y, col) in pts) {
            if (x in 0 until 8 && y in 0 until 8) base.setPixel(x, y, col)
        }
        val out = Bitmap.createBitmap(8, 8, Bitmap.Config.ARGB_8888)
        for (y in 0 until 8) for (x in 0 until 8) {
            val p = base.getPixel(x, y)
            if (Color.alpha(p) == 0) continue
            for ((dx, dy) in listOf(-1 to 0, 1 to 0, 0 to -1, 0 to 1)) {
                val nx = x + dx
                val ny = y + dy
                if (nx in 0 until 8 && ny in 0 until 8 && Color.alpha(base.getPixel(nx, ny)) == 0) {
                    out.setPixel(nx, ny, Color.argb(220, 10, 12, 18))
                }
            }
            out.setPixel(x, y, p)
        }
        return out
    }

    private fun glyphPattern(seed: Int): List<Triple<Int, Int, Int>> {
        val colors = glyphColors
        val c0 = colors[seed % colors.size]
        val c1 = colors[(seed + 1) % colors.size]
        val c2 = colors[(seed + 2) % colors.size]
        val style = seed % 6
        val pts = ArrayList<Triple<Int, Int, Int>>()
        when (style) {
            0 -> { // 菱形
                for ((x, y) in listOf(3 to 1, 2 to 2, 4 to 2, 1 to 3, 5 to 3, 2 to 4, 4 to 4, 3 to 5)) {
                    pts += Triple(x, y, if ((x + y) % 2 == 0) c0 else c1)
                }
                pts += Triple(3, 3, c2)
            }
            1 -> { // 星点
                for ((x, y) in listOf(
                    3 to 0, 3 to 1, 2 to 2, 3 to 2, 4 to 2,
                    1 to 3, 2 to 3, 3 to 3, 4 to 3, 5 to 3,
                    3 to 4, 3 to 5, 3 to 6,
                )) {
                    pts += Triple(x, y, if (y < 3) c0 else c1)
                }
                pts += Triple(3, 3, THEME_WHITE)
            }
            2 -> { // 心
                for ((x, y) in listOf(
                    2 to 1, 4 to 1,
                    1 to 2, 2 to 2, 3 to 2, 4 to 2, 5 to 2,
                    1 to 3, 2 to 3, 3 to 3, 4 to 3, 5 to 3,
                    2 to 4, 3 to 4, 4 to 4, 3 to 5,
                )) {
                    pts += Triple(x, y, if (y < 4) THEME_PINK else c0)
                }
            }
            3 -> { // 对勾
                for ((x, y) in listOf(1 to 3, 2 to 4, 3 to 5, 4 to 4, 5 to 3, 6 to 2)) {
                    pts += Triple(x, y, c0)
                }
                pts += Triple(3, 3, c1)
            }
            4 -> { // 方框宝石
                for (x in 1..6) {
                    pts += Triple(x, 1, c0)
                    pts += Triple(x, 6, c1)
                }
                for (y in 2..5) {
                    pts += Triple(1, y, c0)
                    pts += Triple(6, y, c1)
                }
                pts += Triple(3, 3, THEME_PINK)
                pts += Triple(4, 3, THEME_WHITE)
                pts += Triple(3, 4, THEME_WHITE)
                pts += Triple(4, 4, THEME_BLUE)
            }
            else -> { // 波浪
                val wave = listOf(
                    1 to 3, 2 to 2, 3 to 1, 4 to 2, 5 to 3, 6 to 4, 2 to 5, 4 to 5, 5 to 5,
                )
                wave.forEachIndexed { i, (x, y) ->
                    pts += Triple(x, y, colors[i % colors.size])
                }
            }
        }
        return pts
    }

    /** 粉蓝像素分隔条（对照 draw_pixel_divider）。 */
    fun drawPixelDivider(canvas: Canvas, width: Int, height: Int = 5) {
        val p = Paint(Paint.ANTI_ALIAS_FLAG)
        val w = width.coerceAtLeast(40)
        for (i in 0 until w step 8) {
            p.color = THEME_PINK
            canvas.drawRect(i.toFloat(), 0f, (i + 4).toFloat(), (height - 1).toFloat(), p)
            p.color = THEME_BLUE
            canvas.drawRect((i + 4).toFloat(), 1f, (i + 8).toFloat(), height.toFloat(), p)
        }
        p.color = THEME_WHITE
        canvas.drawRect(0f, (height - 1).toFloat(), w.toFloat(), height.toFloat(), p)
    }
}

/** 点击短促像素粒子（对照 play_pixel_click_burst）。 */
class PixelClickBurst(
    private val context: Context,
    private val windowManager: WindowManager? = null,
    private val roomHost: ViewGroup? = null,
) {
    private val handler = Handler(Looper.getMainLooper())

    fun play(anchor: View) {
        val loc = IntArray(2)
        anchor.getLocationOnScreen(loc)
        val aw = anchor.width.coerceAtLeast(20)
        val ah = anchor.height.coerceAtLeast(16)
        val size = MenuDecor.dp(context, 56f)
        val cxScreen = loc[0] + aw / 2
        val cyScreen = loc[1] + ah / 2

        val burst = BurstView(context)
        val overlay = windowManager != null && roomHost == null
        if (overlay) {
            val wm = windowManager ?: return
            val lp = WindowManager.LayoutParams(
                size, size,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT,
            ).apply {
                gravity = Gravity.TOP or Gravity.START
                x = cxScreen - size / 2
                y = cyScreen - size / 2
            }
            try {
                wm.addView(burst, lp)
            } catch (_: Exception) {
                return
            }
            burst.onFinished = {
                try {
                    wm.removeView(burst)
                } catch (_: Exception) {
                }
            }
        } else {
            val host = roomHost ?: (anchor.rootView as? ViewGroup) ?: return
            val hostLoc = IntArray(2)
            host.getLocationOnScreen(hostLoc)
            val lp = FrameLayout.LayoutParams(size, size).apply {
                leftMargin = (cxScreen - hostLoc[0] - size / 2).coerceAtLeast(0)
                topMargin = (cyScreen - hostLoc[1] - size / 2).coerceAtLeast(0)
            }
            host.addView(burst, lp)
            burst.onFinished = {
                try {
                    host.removeView(burst)
                } catch (_: Exception) {
                }
            }
        }
        burst.start()
    }

    private class BurstView(context: Context) : View(context) {
        var onFinished: (() -> Unit)? = null
        private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
        private val particles = ArrayList<Particle>()
        private var frame = 0
        private val handler = Handler(Looper.getMainLooper())
        private var tick: Runnable? = null
        private val colors = intArrayOf(
            MenuDecor.THEME_BLUE_DEEP,
            MenuDecor.THEME_BLUE,
            MenuDecor.THEME_PINK,
            MenuDecor.THEME_BLACK,
            MenuDecor.THEME_WHITE,
        )

        fun start() {
            val cx = width.takeIf { it > 0 }?.div(2f) ?: MenuDecor.dp(context, 28f).toFloat()
            val cy = height.takeIf { it > 0 }?.div(2f) ?: MenuDecor.dp(context, 28f).toFloat()
            particles.clear()
            val all = colors + colors
            all.forEachIndexed { i, col ->
                val ang = (i / 10.0) * (Math.PI * 2)
                particles += Particle(
                    x = cx, y = cy,
                    vx = (2.4 * cos(ang)).toFloat(),
                    vy = (2.4 * sin(ang)).toFloat(),
                    col = col,
                    life = 10 + (i % 4),
                )
            }
            frame = 0
            post { tickLoop() }
        }

        private fun tickLoop() {
            invalidate()
            var alive = false
            for (p in particles) {
                if (p.life <= 0) continue
                alive = true
                p.x += p.vx
                p.y += p.vy
                p.vy += 0.18f
                p.life -= 1
            }
            frame++
            if (alive && frame < 18) {
                tick = Runnable { tickLoop() }
                handler.postDelayed(tick!!, 28L)
            } else {
                onFinished?.invoke()
            }
        }

        override fun onDraw(canvas: Canvas) {
            for (p in particles) {
                if (p.life <= 0) continue
                val s = if (p.life > 5) 3f else 2f
                paint.color = p.col
                canvas.drawRect(p.x, p.y, p.x + s, p.y + s, paint)
                if (p.life > 6) {
                    paint.color = MenuDecor.THEME_WHITE
                    canvas.drawRect(p.x + 1, p.y - 2, p.x + 2, p.y - 1, paint)
                }
            }
        }

        override fun onDetachedFromWindow() {
            tick?.let { handler.removeCallbacks(it) }
            super.onDetachedFromWindow()
        }

        private data class Particle(
            var x: Float, var y: Float,
            var vx: Float, var vy: Float,
            val col: Int, var life: Int,
        )
    }
}

/** 粉蓝像素分隔条 View。 */
class PixelDividerView @JvmOverloads constructor(
    context: Context,
    attrs: android.util.AttributeSet? = null,
) : View(context, attrs) {
    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        val h = MenuDecor.dp(context, 5f)
        val w = MeasureSpec.getSize(widthMeasureSpec).takeIf { MeasureSpec.getMode(widthMeasureSpec) != MeasureSpec.UNSPECIFIED }
            ?: MenuDecor.dp(context, 220f)
        setMeasuredDimension(w, h)
    }

    override fun onDraw(canvas: Canvas) {
        MenuDecor.drawPixelDivider(canvas, width, height)
    }
}
