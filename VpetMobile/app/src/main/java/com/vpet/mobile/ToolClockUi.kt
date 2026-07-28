package com.vpet.mobile

import android.content.Context
import android.graphics.PixelFormat
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.FrameLayout
import com.vpet.mobile.databinding.OverlayToolClockBinding

/**
 * 秒表 / 计时器：对照 H-TOOL-CLOCK-CTRL。
 * 秒表：开始/暂停/结束；计时器：开始/暂停/关闭。
 */
class ToolClockUi(
    private val context: Context,
    private val windowManager: WindowManager? = null,
    private val roomHost: FrameLayout? = null,
) {
    enum class Kind { STOPWATCH, TIMER }

    private var binding: OverlayToolClockBinding? = null
    private var kind = Kind.STOPWATCH
    private var running = false
    private var accumulatedMs = 0L
    private var segmentStart = 0L
    private var timerTargetMs = 5 * 60_000L
    private val handler = Handler(Looper.getMainLooper())
    private var tick: Runnable? = null
    private val overlayMode = windowManager != null && roomHost == null
    private var onFinished: ((Kind) -> Unit)? = null

    fun showStopwatch() {
        kind = Kind.STOPWATCH
        reset(keepUi = false)
        ensureUi()
        binding?.toolTitle?.text = "秒表"
        binding?.toolPrimary?.text = "开始"
        binding?.toolSecondary?.text = "结束"
        updateDisplay()
        setVisible(true)
    }

    fun showTimer(minutes: Int = 5) {
        kind = Kind.TIMER
        timerTargetMs = minutes.coerceIn(1, 180) * 60_000L
        reset(keepUi = false)
        ensureUi()
        binding?.toolTitle?.text = "计时器 ${minutes}分"
        binding?.toolPrimary?.text = "开始"
        binding?.toolSecondary?.text = "关闭"
        updateDisplay()
        setVisible(true)
    }

    fun destroy() {
        stopTick()
        detach(binding?.root)
        binding = null
    }

    private fun ensureUi() {
        if (binding != null) return
        val b = OverlayToolClockBinding.inflate(LayoutInflater.from(context))
        b.toolPrimary.setOnClickListener { toggleRun() }
        b.toolSecondary.setOnClickListener {
            if (kind == Kind.STOPWATCH) {
                // 结束：清零并隐藏
                reset(keepUi = true)
                setVisible(false)
            } else {
                reset(keepUi = true)
                setVisible(false)
            }
        }
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

    private fun toggleRun() {
        if (running) {
            pause()
        } else {
            start()
        }
    }

    private fun start() {
        running = true
        segmentStart = SystemClock.elapsedRealtime()
        binding?.toolPrimary?.text = "暂停"
        schedule()
    }

    private fun pause() {
        if (running) {
            accumulatedMs += SystemClock.elapsedRealtime() - segmentStart
            running = false
        }
        stopTick()
        binding?.toolPrimary?.text = "开始"
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
                    binding?.toolTitle?.text = "时间到！"
                    onFinished?.invoke(Kind.TIMER)
                    return@Runnable
                }
            }
            if (running) schedule()
        }
        handler.postDelayed(tick!!, 200L)
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
        val b = binding ?: return
        if (kind == Kind.STOPWATCH) {
            b.toolTime.text = formatMs(elapsedNow())
        } else {
            val left = (timerTargetMs - elapsedNow()).coerceAtLeast(0L)
            b.toolTime.text = formatMs(left)
        }
    }

    private fun formatMs(ms: Long): String {
        val totalSec = ms / 1000
        val m = totalSec / 60
        val s = totalSec % 60
        val cs = (ms % 1000) / 10
        return "%02d:%02d.%02d".format(m, s, cs)
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
}
