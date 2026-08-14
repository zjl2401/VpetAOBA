package com.vpet.mobile

import android.os.Handler
import android.os.Looper
import android.os.SystemClock

/**
 * 睡眠模式：对照 `_enter_quiet_mode`。
 * 进入：sleep1 →（过渡）sleep2 + zzz；偷看：短暂 sleep1。
 * 视觉仅在状态变化时回调；偷看结束用一次性定时器，避免 tick 对齐造成闪一下。
 */
class QuietSession(private val host: Host) {
    interface Host {
        fun onQuietVisual(peek: Boolean)
        fun onQuietTick(elapsedSec: Long)
        fun onQuietEnded(elapsedSec: Long)
        fun toast(msg: String)
    }

    companion object {
        const val PEEK_MS = 1000L
        const val TICK_MS = 500L
        const val ENTER_TRANSITION_MS = 600L
        const val REST_PEEK_CLICKS = 2
        const val REST_CLICK_WINDOW_MS = 900L

        fun formatDuration(sec: Long): String {
            val m = sec / 60
            val s = sec % 60
            return if (m > 0) "${m}分${s}秒" else "${s}秒"
        }
    }

    var active = false
        private set
    private var startedAt = 0L
    private var peekUntil = 0L
    private var clickCount = 0
    private var clickWindowStart = 0L
    private var lastVisualPeek: Boolean? = null
    private val handler = Handler(Looper.getMainLooper())
    private var tick: Runnable? = null
    private var enterJob: Runnable? = null
    private var peekEndJob: Runnable? = null

    fun start(announce: Boolean = true) {
        stop(internal = true)
        active = true
        startedAt = SystemClock.elapsedRealtime()
        peekUntil = 0L
        clickCount = 0
        lastVisualPeek = null
        emitVisual(peek = true)
        enterJob = Runnable {
            enterJob = null
            if (!active) return@Runnable
            emitVisual(peek = false)
        }
        handler.postDelayed(enterJob!!, ENTER_TRANSITION_MS)
        if (announce) host.toast("睡眠模式 · 连点立绘偷看，菜单可结束")
        schedule()
    }

    fun stop(internal: Boolean = false) {
        val elapsed = if (active) (SystemClock.elapsedRealtime() - startedAt) / 1000L else 0L
        active = false
        clearJobs()
        lastVisualPeek = null
        if (!internal) host.onQuietEnded(elapsed)
    }

    fun endFromMenu() {
        if (!active) return
        val elapsed = (SystemClock.elapsedRealtime() - startedAt) / 1000L
        clearJobs()
        emitVisual(peek = true)
        active = false
        handler.postDelayed({
            host.onQuietEnded(elapsed)
            host.toast("睡醒了 · 休息 ${formatDuration(elapsed)}")
        }, ENTER_TRANSITION_MS)
    }

    /** 连点偷看：短暂 sleep1，不退出模式 */
    fun peek() {
        if (!active) return
        // 入场过渡中不响应偷看，避免状态打架
        if (enterJob != null) return
        val now = SystemClock.elapsedRealtime()
        if (now - clickWindowStart > REST_CLICK_WINDOW_MS) {
            clickWindowStart = now
            clickCount = 1
        } else {
            clickCount++
        }
        if (clickCount < REST_PEEK_CLICKS) return
        clickCount = 0
        peekUntil = now + PEEK_MS
        emitVisual(peek = true)
        peekEndJob?.let { handler.removeCallbacks(it) }
        peekEndJob = Runnable {
            peekEndJob = null
            if (!active) return@Runnable
            if (SystemClock.elapsedRealtime() >= peekUntil) {
                emitVisual(peek = false)
            }
        }
        handler.postDelayed(peekEndJob!!, PEEK_MS)
    }

    private fun clearJobs() {
        enterJob?.let { handler.removeCallbacks(it) }
        enterJob = null
        peekEndJob?.let { handler.removeCallbacks(it) }
        peekEndJob = null
        tick?.let { handler.removeCallbacks(it) }
        tick = null
    }

    private fun emitVisual(peek: Boolean) {
        if (lastVisualPeek == peek) return
        lastVisualPeek = peek
        host.onQuietVisual(peek)
    }

    private fun schedule() {
        tick?.let { handler.removeCallbacks(it) }
        tick = Runnable {
            if (!active) return@Runnable
            val now = SystemClock.elapsedRealtime()
            host.onQuietTick((now - startedAt) / 1000L)
            schedule()
        }
        handler.postDelayed(tick!!, TICK_MS)
    }
}
