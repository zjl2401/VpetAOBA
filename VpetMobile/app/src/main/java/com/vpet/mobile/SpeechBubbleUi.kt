package com.vpet.mobile

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.ColorFilter
import android.graphics.Paint
import android.graphics.Path
import android.graphics.PixelFormat
import android.graphics.Point
import android.graphics.RectF
import android.graphics.drawable.BitmapDrawable
import android.graphics.drawable.Drawable
import android.os.Handler
import android.os.Looper
import android.util.TypedValue
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.FrameLayout
import com.vpet.mobile.databinding.OverlaySpeechBinding

/**
 * 对话/台词气泡。定位对照桌面：桌宠正下方。
 * 默认微信风：蓝色半透明圆角气泡 + 上指小三角。
 */
class SpeechBubbleUi(
    private val context: Context,
    private val windowManager: WindowManager? = null,
    private val roomHost: FrameLayout? = null,
    private val petTopLeft: () -> Point = { Point(80, 280) },
    private val petSize: () -> Int = { PetPrefs.sizePx(context) },
    private val screenSize: () -> Point = {
        val dm = context.resources.displayMetrics
        Point(dm.widthPixels, dm.heightPixels)
    },
) {
    companion object {
        const val PET_SPEECH_GAP = 4
        const val PET_SPEECH_FOLLOW_MS = 180L
        const val TYPEWRITER_MS = 70L
        const val HI_TYPEWRITER_MS = 130L
        private const val FLAT_MIN_DP = 48
        private const val FLAT_MAX_DP = 260
        /** 深蓝字配浅蓝气泡 */
        private const val SPEECH_FG = 0xFF0A1F3D.toInt()
        /** 浅蓝底（再浅一档，避免发闷） */
        private const val SPEECH_BUBBLE_FILL = 0xF5E8F4FF.toInt()
        private const val SPEECH_BUBBLE_STROKE = 0xFFB8DCFF.toInt()
        private const val SPEECH_BUBBLE_SHADOW = 0x227EC8FF
    }

    private var binding: OverlaySpeechBinding? = null
    private var wmLp: WindowManager.LayoutParams? = null
    private var roomLp: FrameLayout.LayoutParams? = null
    private val handler = Handler(Looper.getMainLooper())
    private var hideJob: Runnable? = null
    private var followJob: Runnable? = null
    private var typeJob: Runnable? = null
    private val overlayMode = windowManager != null && roomHost == null
    private val typeSound = TypeSoundPlayer(context)
    private var borderPeak: Pair<Int, Int> = 0 to 0
    private var useBorder5 = false

    fun show(text: String, autoHideMs: Long = 3200L, border5: Boolean = false) {
        showInternal(text, autoHideMs, typewriterMs = 0L, border5 = border5)
    }

    /** 语音字幕：瞬时全文，无打字音。 */
    fun showVoiceSubtitle(text: String, autoHideMs: Long = 3200L) {
        showInternal(text.ifBlank { "……" }, autoHideMs.coerceAtLeast(800L), typewriterMs = 0L, border5 = false)
    }

    fun showTypewriter(
        text: String,
        autoHideMs: Long = 3200L,
        typewriterMs: Long = TYPEWRITER_MS,
        border5: Boolean = false,
    ) {
        showInternal(text, autoHideMs, typewriterMs = typewriterMs.coerceAtLeast(1L), border5 = border5)
    }

    fun showHiTypewriter(text: String, autoHideMs: Long = 4200L) {
        showTypewriter(text, autoHideMs, HI_TYPEWRITER_MS, border5 = false)
    }

    /** 系统→对话：蓝气泡 + 打字机。 */
    fun showDialog(text: String, autoHideMs: Long = 4200L, typewriterMs: Long = TYPEWRITER_MS) {
        showTypewriter(text, autoHideMs, typewriterMs, border5 = false)
    }

    private fun showInternal(text: String, autoHideMs: Long, typewriterMs: Long, border5: Boolean) {
        if (!AppDataStore.speechTextOn(context)) {
            hide()
            return
        }
        ensure()
        cancelType()
        useBorder5 = border5
        if (!border5) borderPeak = 0 to 0
        AppDataStore.applySp(binding?.speechText, AppDataStore.fontSp(context))
        applyChrome(text.ifBlank { " " })
        binding?.root?.visibility = View.VISIBLE
        placeNow()
        startFollow()
        hideJob?.let { handler.removeCallbacks(it) }
        if (typewriterMs <= 0L) {
            binding?.speechText?.text = text
            applyChrome(text)
            if (autoHideMs > 0L) {
                hideJob = Runnable { hide() }
                handler.postDelayed(hideJob!!, autoHideMs)
            }
            return
        }
        binding?.speechText?.text = ""
        if (border5) applyChrome(text) else applyChrome(text)
        var i = 0
        typeJob = object : Runnable {
            override fun run() {
                if (i >= text.length) {
                    typeJob = null
                    if (autoHideMs > 0L) {
                        hideJob = Runnable { hide() }
                        handler.postDelayed(hideJob!!, autoHideMs)
                    }
                    return
                }
                val ch = text[i]
                binding?.speechText?.append(ch.toString())
                if (!ch.isWhitespace()) typeSound.tick()
                i++
                val delay = if (ch == '\n') typewriterMs * 2 else typewriterMs
                if (i % 4 == 0 || ch == '\n') {
                    if (!useBorder5) applyChrome(binding?.speechText?.text?.toString().orEmpty())
                    placeNow()
                }
                handler.postDelayed(this, delay)
            }
        }
        handler.post(typeJob!!)
    }

    fun reposition() {
        if (binding?.root?.visibility == View.VISIBLE) placeNow()
    }

    fun hide() {
        cancelType()
        hideJob?.let { handler.removeCallbacks(it) }
        hideJob = null
        stopFollow()
        binding?.root?.visibility = View.GONE
        useBorder5 = false
        borderPeak = 0 to 0
    }

    fun destroy() {
        hide()
        typeSound.release()
        val root = binding?.root ?: return
        try {
            if (overlayMode) windowManager?.removeView(root)
            else roomHost?.removeView(root)
        } catch (_: Exception) {
        }
        binding = null
        wmLp = null
        roomLp = null
    }

    private fun applyChrome(fullText: String) {
        val b = binding ?: return
        val sp = AppDataStore.fontSp(context)
        val textPx = TypedValue.applyDimension(
            TypedValue.COMPLEX_UNIT_SP, sp, context.resources.displayMetrics,
        )
        if (!useBorder5) {
            applyFlatChrome(fullText)
            return
        }
        var (cw, ch) = SpeechBorder5.measureContent(fullText, textPx)
        cw = maxOf(cw, borderPeak.first)
        ch = maxOf(ch, borderPeak.second)
        borderPeak = cw to ch
        val bmp: Bitmap = SpeechBorder5.compose(context, cw, ch) ?: run {
            useBorder5 = false
            applyChrome(fullText)
            return
        }
        val pads = SpeechBorder5.padsFor(cw, ch)
        b.speechRoot.setBackgroundColor(0x00000000)
        b.speechRoot.setPadding(0, 0, 0, 0)
        b.speechBorder.visibility = View.VISIBLE
        b.speechBorder.setImageDrawable(BitmapDrawable(context.resources, bmp))
        b.speechBorder.layoutParams = FrameLayout.LayoutParams(bmp.width, bmp.height)
        val tp = FrameLayout.LayoutParams(
            maxOf(40, bmp.width - pads[0] - pads[2]),
            maxOf(16, bmp.height - pads[1] - pads[3]),
        ).apply {
            leftMargin = pads[0]
            topMargin = pads[1]
        }
        b.speechText.layoutParams = tp
        b.speechText.setBackgroundColor(0x00000000)
        b.speechText.setTextColor(SPEECH_FG)
    }

    /** 近白浅蓝气泡 + 上指三角（对照桌面文本框对比）。 */
    private fun applyFlatChrome(fullText: String) {
        val b = binding ?: return
        b.speechBorder.visibility = View.GONE
        val padH = dp(12)
        val padV = dp(9)
        val tailH = dp(7)
        val shadowPad = dp(2)
        b.speechRoot.setPadding(padH + shadowPad, padV + tailH + shadowPad, padH + shadowPad, padV + shadowPad)
        b.speechRoot.background = WeChatBubbleDrawable(
            fillColor = SPEECH_BUBBLE_FILL,
            strokeColor = SPEECH_BUBBLE_STROKE,
            cornerRadius = dp(10).toFloat(),
            tailWidth = dp(12).toFloat(),
            tailHeight = tailH.toFloat(),
            shadowColor = SPEECH_BUBBLE_SHADOW,
            shadowDy = dp(1).toFloat(),
        )
        b.speechRoot.elevation = 0f
        b.speechText.setTextColor(SPEECH_FG)
        val minW = dp(FLAT_MIN_DP)
        val maxW = minOf(dp(FLAT_MAX_DP), (screenSize().x * 0.72f).toInt().coerceAtLeast(minW))
        val tv = b.speechText
        AppDataStore.applySp(tv, AppDataStore.fontSp(context))
        val paint = tv.paint
        var natural = 0f
        for (line in fullText.split('\n')) {
            natural = maxOf(natural, paint.measureText(line.ifEmpty { " " }))
        }
        val contentW = (natural + dp(2)).toInt().coerceIn(minW, maxW)
        tv.maxWidth = contentW
        tv.layoutParams = FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.WRAP_CONTENT,
            FrameLayout.LayoutParams.WRAP_CONTENT,
        )
    }

    private fun dp(v: Int): Int =
        TypedValue.applyDimension(
            TypedValue.COMPLEX_UNIT_DIP, v.toFloat(), context.resources.displayMetrics,
        ).toInt()

    private fun cancelType() {
        typeJob?.let { handler.removeCallbacks(it) }
        typeJob = null
    }

    private fun startFollow() {
        stopFollow()
        followJob = object : Runnable {
            override fun run() {
                if (binding?.root?.visibility != View.VISIBLE) return
                placeNow()
                handler.postDelayed(this, PET_SPEECH_FOLLOW_MS)
            }
        }
        handler.postDelayed(followJob!!, PET_SPEECH_FOLLOW_MS)
    }

    private fun stopFollow() {
        followJob?.let { handler.removeCallbacks(it) }
        followJob = null
    }

    private fun placeNow() {
        val root = binding?.root ?: return
        root.measure(
            View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED),
            View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED),
        )
        val bw = root.measuredWidth.coerceAtLeast(1)
        val bh = root.measuredHeight.coerceAtLeast(1)
        val pet = petTopLeft()
        val size = petSize()
        val scr = screenSize()
        var x = pet.x + size / 2 - bw / 2
        var y = pet.y + size + PET_SPEECH_GAP
        x = x.coerceIn(0, (scr.x - bw).coerceAtLeast(0))
        y = y.coerceIn(0, (scr.y - bh).coerceAtLeast(0))
        if (overlayMode) {
            val lp = wmLp ?: return
            lp.gravity = Gravity.TOP or Gravity.START
            lp.x = x
            lp.y = y
            try {
                windowManager?.updateViewLayout(root, lp)
            } catch (_: Exception) {
            }
        } else {
            val lp = roomLp ?: return
            lp.gravity = Gravity.TOP or Gravity.START
            lp.leftMargin = x
            lp.topMargin = y
            root.layoutParams = lp
        }
    }

    private fun ensure() {
        if (binding != null) return
        val b = OverlaySpeechBinding.inflate(LayoutInflater.from(context))
        binding = b
        if (overlayMode) {
            wmLp = WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT,
            ).apply {
                gravity = Gravity.TOP or Gravity.START
            }
            windowManager?.addView(b.root, wmLp)
        } else {
            roomLp = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,
                FrameLayout.LayoutParams.WRAP_CONTENT,
            ).apply {
                gravity = Gravity.TOP or Gravity.START
            }
            roomHost?.addView(b.root, roomLp)
        }
        b.root.setBackgroundColor(0x00000000)
        b.root.visibility = View.GONE
    }

    /** 浅蓝底气泡：圆角矩形 + 顶部居中小三角（指向桌宠）。 */
    private class WeChatBubbleDrawable(
        private val fillColor: Int,
        private val strokeColor: Int,
        private val cornerRadius: Float,
        private val tailWidth: Float,
        private val tailHeight: Float,
        private val shadowColor: Int,
        private val shadowDy: Float,
    ) : Drawable() {
        private val fillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.FILL
            color = fillColor
        }
        private val strokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
            color = strokeColor
            strokeWidth = 2f
        }
        private val shadowPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.FILL
            color = shadowColor
        }
        private val path = Path()
        private val body = RectF()

        override fun draw(canvas: Canvas) {
            val b = bounds
            if (b.width() <= 0 || b.height() <= 0) return
            val left = b.left.toFloat()
            val top = b.top.toFloat()
            val right = b.right.toFloat()
            val bottom = b.bottom.toFloat()
            val th = tailHeight.coerceAtMost((bottom - top) * 0.35f)
            val tw = tailWidth.coerceAtMost((right - left) * 0.4f)
            val cx = (left + right) * 0.5f
            val r = cornerRadius.coerceAtMost(minOf(right - left, bottom - top - th) * 0.5f)

            fun build(target: Path, dy: Float) {
                target.reset()
                body.set(left, top + th + dy, right, bottom + dy)
                target.addRoundRect(body, r, r, Path.Direction.CW)
                target.moveTo(cx - tw * 0.5f, top + th + dy + 0.5f)
                target.lineTo(cx, top + dy)
                target.lineTo(cx + tw * 0.5f, top + th + dy + 0.5f)
                target.close()
            }

            if (shadowDy > 0f) {
                build(path, shadowDy)
                canvas.drawPath(path, shadowPaint)
            }
            build(path, 0f)
            canvas.drawPath(path, fillPaint)
            canvas.drawPath(path, strokePaint)
        }

        override fun setAlpha(alpha: Int) {
            fillPaint.alpha = alpha
            strokePaint.alpha = alpha
            shadowPaint.alpha = (alpha * 0.35f).toInt().coerceIn(0, 255)
            invalidateSelf()
        }

        override fun setColorFilter(colorFilter: ColorFilter?) {
            fillPaint.colorFilter = colorFilter
            strokePaint.colorFilter = colorFilter
            invalidateSelf()
        }

        @Deprecated("Deprecated in Java")
        override fun getOpacity(): Int = PixelFormat.TRANSLUCENT
    }
}
