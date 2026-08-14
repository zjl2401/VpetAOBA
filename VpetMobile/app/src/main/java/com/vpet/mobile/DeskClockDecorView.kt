package com.vpet.mobile

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.Typeface
import android.util.AttributeSet
import android.util.TypedValue
import android.view.View
import kotlin.math.max

/**
 * 桌面时钟装饰：数字框 + 沿边绕圈的小人（对照 desktop_clock.py / `_draw_desk_clock`）。
 */
class DeskClockDecorView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : View(context, attrs) {

    enum class WalkerStyle { WALK, WORK, MUSIC, SLEEP }

    var titleText: String = ""
        set(value) {
            field = value
            invalidate()
        }
    var timeText: String = "00:00"
        set(value) {
            field = value
            invalidate()
        }
    var accentArgb: Int = 0xFF88FFCC.toInt()
        set(value) {
            field = value
            invalidate()
        }
    /** 暂停时冻结绕圈进度用的已走毫秒。 */
    var progressMs: Long = 0L
        set(value) {
            field = value
            invalidate()
        }
    var walkerStyle: WalkerStyle = WalkerStyle.WALK
        set(value) {
            if (field != value) {
                field = value
                framesCache = null
                invalidate()
            }
        }

    private val padPx = dp(28f)
    private val innerW = dp(148f)
    private val innerH = dp(44f)
    private val walkerSize = dp(26f).toInt()
    private val lapMs = 6200f
    private val frameMs = 210L
    private val sleepFrameMs = 480L

    private val innerFill = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.FILL
        // 中间黑底再透一点（对照桌面 DESK_CLOCK_FILL_STIPPLE）
        color = 0x8A162030.toInt()
    }
    private val innerStroke = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = dp(2f)
        color = 0xFF88CCFF.toInt()
    }
    private val titlePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = 0xFF8899AA.toInt()
        textSize = sp(11f)
        typeface = Typeface.MONOSPACE
    }
    private val timePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = accentArgb
        textSize = sp(18f)
        typeface = Typeface.create(Typeface.MONOSPACE, Typeface.BOLD)
        textAlign = Paint.Align.CENTER
    }

    private var framesCache: Map<String, List<Bitmap>>? = null

    /** 跟随系统「字体大小」设置。 */
    fun applyFontScale(ctx: Context = context) {
        titlePaint.textSize = sp(AppDataStore.fontClockTitleSp(ctx))
        timePaint.textSize = sp(AppDataStore.fontClockTimeSp(ctx))
        invalidate()
    }

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        val w = (innerW + padPx * 2).toInt()
        val h = (innerH + padPx * 2).toInt()
        setMeasuredDimension(w, h)
    }

    override fun onDraw(canvas: Canvas) {
        // 外层透明：只画数字框，不铺深色大底板
        val left = padPx
        val top = padPx
        canvas.drawRect(left, top, left + innerW, top + innerH, innerFill)
        canvas.drawRect(left, top, left + innerW, top + innerH, innerStroke)

        timePaint.color = accentArgb
        canvas.drawText(titleText, left + dp(8f), top + dp(14f), titlePaint)
        canvas.drawText(timeText, left + innerW / 2f, top + innerH / 2f + dp(10f), timePaint)

        val t = walkerProgress(progressMs)
        val (px, py, edge) = perimeterPoint(t, left, top, innerW, innerH)
        val bmp = pickWalkerBitmap(edge) ?: return
        val hw = bmp.width / 2f
        val hh = bmp.height / 2f
        canvas.drawBitmap(bmp, px - hw, py - hh, null)
    }

    private fun pickWalkerBitmap(edge: String): Bitmap? {
        val frames = ensureFrames()
        if (walkerStyle == WalkerStyle.SLEEP) {
            val list = frames["sleep"].orEmpty()
            if (list.isEmpty()) return null
            val i = ((progressMs / sleepFrameMs) % list.size).toInt()
            return list[i]
        }
        val facing = edgeToFacing(edge)
        val list = frames[facing].orEmpty().ifEmpty { frames["front"].orEmpty() }
        if (list.isEmpty()) return null
        val i = ((progressMs / frameMs) % list.size).toInt()
        return list[i]
    }

    private fun ensureFrames(): Map<String, List<Bitmap>> {
        framesCache?.let { return it }
        val map = mutableMapOf<String, List<Bitmap>>()
        when (walkerStyle) {
            WalkerStyle.SLEEP -> {
                map["sleep"] = listOfNotNull(
                    SpriteAssets.load(context, SpriteAssets.SLEEP1, walkerSize),
                    SpriteAssets.load(context, SpriteAssets.SLEEP2, walkerSize),
                )
            }
            WalkerStyle.WORK -> loadDirs(map, "work")
            WalkerStyle.MUSIC -> loadDirs(map, "music")
            WalkerStyle.WALK -> loadDirs(map, "walk")
        }
        if (walkerStyle != WalkerStyle.WALK && walkerStyle != WalkerStyle.SLEEP &&
            map.values.all { it.isEmpty() }
        ) {
            loadDirs(map, "walk")
        }
        framesCache = map
        return map
    }

    private fun loadDirs(map: MutableMap<String, List<Bitmap>>, prefix: String) {
        fun path(name: String) = "sprites/$name.png"
        fun load2(a: String, b: String, flip: Boolean = false): List<Bitmap> =
            listOfNotNull(
                SpriteAssets.load(context, path(a), walkerSize, flip),
                SpriteAssets.load(context, path(b), walkerSize, flip),
            )
        when (prefix) {
            "work" -> {
                map["front"] = load2("workfront1", "workfront2")
                map["back"] = load2("workback1", "workback2")
                map["left"] = load2("workleft1", "workleft2")
                map["right"] = load2("workleft1", "workleft2", flip = true)
            }
            "music" -> {
                map["front"] = load2("musicfront1", "musicfront2")
                map["back"] = load2("musicback1", "musicback2")
                map["left"] = load2("musicleft1", "musicleft2")
                map["right"] = load2("musicleft1", "musicleft2", flip = true)
            }
            else -> {
                map["front"] = load2("walkfront1", "walkfront2")
                map["back"] = load2("walkback1", "walkback2")
                map["left"] = load2("walkleft1", "walkleft2")
                map["right"] = load2("walkleft1", "walkleft2", flip = true)
            }
        }
    }

    companion object {
        fun walkerProgress(elapsedMs: Long, lapMs: Float = 6200f): Float {
            val lap = max(800f, lapMs)
            return ((elapsedMs.coerceAtLeast(0).toFloat()) / lap) % 1f
        }

        /** 沿矩形顺时针；返回 (x,y,edge)。对照 desktop_clock.perimeter_point。 */
        fun perimeterPoint(
            t: Float,
            left: Float,
            top: Float,
            width: Float,
            height: Float,
        ): Triple<Float, Float, String> {
            val w = max(1f, width)
            val h = max(1f, height)
            val peri = 2f * (w + h)
            var d = ((t % 1f + 1f) % 1f) * peri
            if (d <= w) return Triple(left + d, top, "top")
            d -= w
            if (d <= h) return Triple(left + w, top + d, "right")
            d -= h
            if (d <= w) return Triple(left + w - d, top + h, "bottom")
            d -= w
            return Triple(left, top + h - d, "left")
        }

        fun edgeToFacing(edge: String): String = when (edge) {
            "top" -> "right"
            "right" -> "front"
            "bottom" -> "left"
            "left" -> "back"
            else -> "front"
        }
    }

    private fun dp(v: Float): Float =
        TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v, resources.displayMetrics)

    private fun sp(v: Float): Float =
        TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_SP, v, resources.displayMetrics)
}
