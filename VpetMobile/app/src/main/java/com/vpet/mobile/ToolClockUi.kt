package com.vpet.mobile

import android.content.Context
import android.graphics.PixelFormat
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.util.TypedValue
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.Toast
import com.vpet.mobile.databinding.OverlayToolClockBinding

/**
 * 秒表 / 计时器：对照桌面 `_start_desk_clock` + ▶⏸⏹。
 */
class ToolClockUi(
    private val context: Context,
    private val windowManager: WindowManager? = null,
    private val roomHost: FrameLayout? = null,
) {
    enum class Kind { STOPWATCH, TIMER }

    private var binding: OverlayToolClockBinding? = null
    private var overlayLp: WindowManager.LayoutParams? = null
    private var kind = Kind.STOPWATCH
    private var running = false
    private var accumulatedMs = 0L
    private var segmentStart = 0L
    private var timerTargetMs = 5 * 60_000L
    private val handler = Handler(Looper.getMainLooper())
    private var tick: Runnable? = null
    private val overlayMode = windowManager != null && roomHost == null
    private var titleBase = "秒表"

    /** 工具秒表是否显示中（不含音乐自动秒表）。 */
    fun isToolStopwatchShowing(): Boolean =
        binding?.root?.visibility == View.VISIBLE &&
            kind == Kind.STOPWATCH &&
            titleBase == "秒表"

    fun isAnyShowing(): Boolean = binding?.root?.visibility == View.VISIBLE

    /** 菜单再点：开着则关（对齐桌面 `_toggle_tool_stopwatch`）。 */
    fun toggleStopwatch() {
        if (isToolStopwatchShowing()) {
            reset(keepUi = true)
            setVisible(false)
            Toast.makeText(context, "秒表已关闭", Toast.LENGTH_SHORT).show()
            return
        }
        showStopwatch()
    }

    fun showStopwatch() {
        kind = Kind.STOPWATCH
        titleBase = "秒表"
        reset(keepUi = false)
        ensureUi()
        applyButtonFonts()
        binding?.toolClockDecor?.apply {
            applyFontScale(context)
            walkerStyle = DeskClockDecorView.WalkerStyle.WALK
            accentArgb = 0xFF88FFCC.toInt()
            titleText = titleBase
        }
        updateDisplay()
        setVisible(true)
        AppDataStore.unlock(context, "timer_use")
        Toast.makeText(context, "秒表已开启（▶ 开始 · ⏸ 暂停 · ⏹ 结束 · 可拖动）", Toast.LENGTH_SHORT).show()
    }

    /** 音乐模式自动秒表（对照桌面 desk_clock music）。 */
    fun showMusicAutoStopwatch() {
        kind = Kind.STOPWATCH
        titleBase = "音乐"
        reset(keepUi = false)
        ensureUi()
        applyButtonFonts()
        binding?.toolClockDecor?.apply {
            applyFontScale(context)
            walkerStyle = DeskClockDecorView.WalkerStyle.MUSIC
            accentArgb = 0xFF9EC8E8.toInt()
            titleText = titleBase
        }
        updateDisplay()
        setVisible(true)
        start()
        AppDataStore.unlock(context, "timer_use")
    }

    fun hideMusicAutoStopwatch() {
        if (titleBase != "音乐") return
        reset(keepUi = true)
        setVisible(false)
    }

    /** @param durationMs 总倒计时毫秒，至少 1 秒。 */
    fun showTimerMs(durationMs: Long) {
        kind = Kind.TIMER
        timerTargetMs = durationMs.coerceAtLeast(1000L)
        titleBase = "计时器"
        reset(keepUi = false)
        ensureUi()
        applyButtonFonts()
        binding?.toolClockDecor?.apply {
            applyFontScale(context)
            walkerStyle = DeskClockDecorView.WalkerStyle.WALK
            accentArgb = 0xFFFFCC66.toInt()
            titleText = titleBase
        }
        updateDisplay()
        setVisible(true)
        AppDataStore.unlock(context, "timer_use")
        val label = formatDurationCn(timerTargetMs / 1000.0)
        Toast.makeText(context, "计时器 $label（点 ▶ 开始）", Toast.LENGTH_SHORT).show()
    }

    fun showTimer(minutes: Int = 5) {
        showTimerMs(minutes.coerceIn(1, 180) * 60_000L)
    }

    fun destroy() {
        stopTick()
        detach(binding?.root)
        binding = null
        overlayLp = null
    }

    /** 抬到当前宿主内靠前（仍应在桌宠/伴侣 restack 之前调用）。 */
    fun raiseLayer() {
        val v = binding?.root ?: return
        if (v.visibility != View.VISIBLE) return
        try {
            if (overlayMode) {
                val lp = overlayLp ?: return
                windowManager?.removeView(v)
                windowManager?.addView(v, lp)
            } else {
                v.bringToFront()
            }
        } catch (_: Exception) {
        }
    }

    private fun ensureUi() {
        if (binding != null) return
        val b = OverlayToolClockBinding.inflate(LayoutInflater.from(context))
        b.toolPlay.setOnClickListener { start() }
        b.toolPause.setOnClickListener { pause() }
        b.toolStop.setOnClickListener {
            reset(keepUi = true)
            setVisible(false)
        }
        enableDrag(b.root)
        binding = b
        if (overlayMode) {
            val lp = WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT,
            ).apply {
                gravity = Gravity.TOP or Gravity.END
                x = 24
                y = 120
            }
            overlayLp = lp
            windowManager?.addView(b.root, lp)
        } else {
            val lp = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,
                FrameLayout.LayoutParams.WRAP_CONTENT,
            ).apply {
                gravity = Gravity.TOP or Gravity.END
                topMargin = 120
                marginEnd = 16
            }
            roomHost?.addView(b.root, lp)
        }
    }

    fun refreshFonts() {
        applyButtonFonts()
        binding?.toolClockDecor?.applyFontScale(context)
    }

    private fun applyButtonFonts() {
        val sp = AppDataStore.fontClockBtnSp(context)
        binding?.toolPlay?.setTextSize(TypedValue.COMPLEX_UNIT_SP, sp)
        binding?.toolPause?.setTextSize(TypedValue.COMPLEX_UNIT_SP, sp)
        binding?.toolStop?.setTextSize(TypedValue.COMPLEX_UNIT_SP, sp)
    }

    private fun enableDrag(root: View) {
        var downRawX = 0f
        var downRawY = 0f
        var originX = 0
        var originY = 0
        root.setOnTouchListener { _, e ->
            if (!overlayMode) return@setOnTouchListener false
            val lp = overlayLp ?: return@setOnTouchListener false
            when (e.action) {
                MotionEvent.ACTION_DOWN -> {
                    downRawX = e.rawX
                    downRawY = e.rawY
                    originX = lp.x
                    originY = lp.y
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    lp.x = originX - (e.rawX - downRawX).toInt()
                    lp.y = originY + (e.rawY - downRawY).toInt()
                    try {
                        windowManager?.updateViewLayout(root, lp)
                    } catch (_: Exception) {
                    }
                    true
                }
                else -> false
            }
        }
    }

    private fun start() {
        if (running) return
        running = true
        segmentStart = SystemClock.elapsedRealtime()
        schedule()
        updateDisplay()
    }

    private fun pause() {
        if (running) {
            accumulatedMs += SystemClock.elapsedRealtime() - segmentStart
            running = false
        }
        stopTick()
        updateDisplay()
    }

    private fun reset(keepUi: Boolean) {
        pause()
        accumulatedMs = 0L
        if (keepUi) updateDisplay()
    }

    private fun schedule() {
        stopTick()
        tick = Runnable {
            updateDisplay()
            if (kind == Kind.TIMER) {
                val left = timerTargetMs - elapsedNow()
                if (left <= 0) {
                    pause()
                    accumulatedMs = timerTargetMs
                    updateDisplay()
                    binding?.toolClockDecor?.titleText = "时间到！"
                    Toast.makeText(context, "计时器时间到！", Toast.LENGTH_LONG).show()
                    return@Runnable
                }
            }
            if (running) schedule()
        }
        handler.postDelayed(tick!!, 80L)
    }

    private fun stopTick() {
        tick?.let { handler.removeCallbacks(it) }
        tick = null
    }

    private fun elapsedNow(): Long {
        var t = accumulatedMs
        if (running) t += SystemClock.elapsedRealtime() - segmentStart
        return t
    }

    private fun updateDisplay() {
        val decor = binding?.toolClockDecor ?: return
        val elapsed = elapsedNow()
        if (kind == Kind.STOPWATCH) {
            decor.timeText = formatClockMs(elapsed)
            decor.progressMs = elapsed
            decor.titleText = if (!running && elapsed > 0) "$titleBase · 暂停" else titleBase
        } else {
            val left = (timerTargetMs - elapsed).coerceAtLeast(0L)
            decor.timeText = formatClockMs(left)
            decor.progressMs = elapsed
            decor.titleText = if (!running) "$titleBase · 暂停" else titleBase
        }
    }

    private fun setVisible(v: Boolean) {
        binding?.root?.visibility = if (v) View.VISIBLE else View.GONE
    }

    private fun detach(v: View?) {
        if (v == null) return
        try {
            if (overlayMode) windowManager?.removeView(v)
            else roomHost?.removeView(v)
        } catch (_: Exception) {
        }
    }

    companion object {
        fun formatClockMs(ms: Long): String {
            val total = (ms / 1000).coerceAtLeast(0)
            val h = total / 3600
            val m = (total % 3600) / 60
            val s = total % 60
            return if (h > 0) "%02d:%02d:%02d".format(h, m, s) else "%02d:%02d".format(m, s)
        }

        fun formatDurationCn(seconds: Double): String {
            val sec = seconds.toInt().coerceAtLeast(0)
            val h = sec / 3600
            val m = (sec % 3600) / 60
            val s = sec % 60
            val parts = mutableListOf<String>()
            if (h > 0) parts += "${h}小时"
            if (m > 0) parts += "${m}分"
            if (s > 0 || parts.isEmpty()) parts += "${s}秒"
            return parts.joinToString("")
        }
    }
}
