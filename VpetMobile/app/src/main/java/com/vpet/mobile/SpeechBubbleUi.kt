package com.vpet.mobile

import android.content.Context
import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.graphics.Point
import android.graphics.drawable.BitmapDrawable
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
 * 系统→对话可用 border5；语音字幕为粉顶条扁平框；动作等为普通扁平框。
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
        const val PET_SPEECH_GAP = 6
        const val PET_SPEECH_FOLLOW_MS = 180L
        const val TYPEWRITER_MS = 70L
        const val HI_TYPEWRITER_MS = 130L
        /** 扁平气泡：最短/最长内容宽（dp） */
        private const val FLAT_MIN_DP = 56
        private const val FLAT_MAX_DP = 280
        private const val SPEECH_FG_VPET = 0xFF88CCFF.toInt()
        private const val SPEECH_FG_ALLMATE = 0xFF1A4A99.toInt()
        private const val SPEECH_TEXT_BG = 0xE0141824.toInt()
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
    private var voiceStyle = false
    private var voiceFg = SPEECH_FG_VPET

    fun show(text: String, autoHideMs: Long = 3200L, border5: Boolean = false) {
        showInternal(text, autoHideMs, typewriterMs = 0L, border5 = border5)
    }

    /** 语音字幕：瞬时全文，无打字音；粉顶条标题框。时长建议 = 语音时长 + 1s。 */
    fun showVoiceSubtitle(text: String, autoHideMs: Long = 3200L, source: String = "vpet") {
        voiceFg = if (source.equals("allmate", ignoreCase = true)) SPEECH_FG_ALLMATE else SPEECH_FG_VPET
        showInternal(
            text.ifBlank { "……" },
            autoHideMs.coerceAtLeast(800L),
            typewriterMs = 0L,
            border5 = false,
            asVoice = true,
        )
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

    /** 系统→对话（预设问答等）：border5 + 打字机。 */
    fun showDialog(text: String, autoHideMs: Long = 4200L, typewriterMs: Long = TYPEWRITER_MS) {
        showTypewriter(text, autoHideMs, typewriterMs, border5 = true)
    }

    private fun showInternal(
        text: String,
        autoHideMs: Long,
        typewriterMs: Long,
        border5: Boolean,
        asVoice: Boolean = false,
    ) {
        ensure()
        cancelType()
        useBorder5 = border5
        voiceStyle = asVoice && !border5
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
        // 打字机：按全文锁定 border5 尺寸
        if (border5) applyChrome(text)
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
                    if (!useBorder5) applyFlatChrome(text.take(i + 1).ifBlank { " " })
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

    /** 字体档位变更：气泡可见时立即改字号并重排。 */
    fun refreshFontScale() {
        val b = binding ?: return
        if (b.root.visibility != View.VISIBLE) return
        AppDataStore.applySp(b.speechText, AppDataStore.fontSp(context))
        applyChrome(b.speechText.text?.toString().orEmpty().ifBlank { " " })
        placeNow()
    }

    fun hide() {
        cancelType()
        hideJob?.let { handler.removeCallbacks(it) }
        hideJob = null
        stopFollow()
        binding?.root?.visibility = View.GONE
        useBorder5 = false
        voiceStyle = false
        borderPeak = 0 to 0
    }

    /** 抬到当前悬浮栈顶（统一图层重排用）。 */
    fun raiseLayer() {
        val root = binding?.root ?: return
        if (overlayMode) {
            val lp = wmLp ?: return
            try {
                windowManager?.removeView(root)
                windowManager?.addView(root, lp)
            } catch (_: Exception) {
            }
        } else {
            root.bringToFront()
        }
    }

    fun setVisible(visible: Boolean) {
        if (!visible) hide()
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
        b.speechBorder.scaleType = android.widget.ImageView.ScaleType.FIT_XY
        b.speechBorder.setBackgroundColor(0x00000000)
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
    }

    /** 扁平气泡：宽度随字数伸缩，长文自动换行。语音框带粉顶条 + 深蓝描边。 */
    private fun applyFlatChrome(fullText: String) {
        val b = binding ?: return
        b.speechBorder.visibility = View.GONE
        val padH = dp(12)
        val padV = dp(10)
        if (voiceStyle) {
            b.speechRoot.setPadding(padH, padV + dp(3), padH, padV)
            val body = android.graphics.drawable.GradientDrawable().apply {
                setColor(SPEECH_TEXT_BG)
                setStroke(dp(1), MenuDecor.THEME_BLUE_DEEP)
            }
            val layers = android.graphics.drawable.LayerDrawable(
                arrayOf(
                    android.graphics.drawable.GradientDrawable().apply {
                        setColor(MenuDecor.THEME_PINK)
                    },
                    body,
                ),
            )
            layers.setLayerInset(1, 0, dp(3), 0, 0)
            b.speechRoot.background = layers
            b.speechText.setTextColor(voiceFg)
        } else {
            b.speechRoot.setPadding(dp(10), dp(8), dp(10), dp(8))
            b.speechRoot.setBackgroundColor(0xEE1A1A22.toInt())
            b.speechText.setTextColor(0xFFFFFFFF.toInt())
        }
        val minW = dp(if (voiceStyle) 72 else FLAT_MIN_DP)
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
        b.root.visibility = View.GONE
    }
}
