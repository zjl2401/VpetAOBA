package com.vpet.mobile

import android.os.Handler
import android.os.Looper
import android.os.SystemClock

/**
 * 睡眠模式：对照 `_enter_quiet_mode`。
 * 安静显示 sleep2；连点 ≥2（900ms 窗）peek 显示 sleep1。
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
    private val handler = Handler(Looper.getMainLooper())
    private var tick: Runnable? = null

    fun start(announce: Boolean = true) {
        stop(internal = true)
        active = true
        startedAt = SystemClock.elapsedRealtime()
        peekUntil = 0L
        clickCount = 0
        host.onQuietVisual(peek = false)
        if (announce) host.toast("睡眠模式 · 连点立绘偷看，菜单可结束")
        schedule()
    }

    fun stop(internal: Boolean = false) {
        val elapsed = if (active) (SystemClock.elapsedRealtime() - startedAt) / 1000L else 0L
        active = false
        tick?.let { handler.removeCallbacks(it) }
        tick = null
        if (!internal) host.onQuietEnded(elapsed)
    }

    fun endFromMenu() {
        if (!active) return
        val elapsed = (SystemClock.elapsedRealtime() - startedAt) / 1000L
        stop()
        host.toast("睡醒了 · 休息 ${formatDuration(elapsed)}")
    }

    /** 连点偷看：短暂 sleep1，不退出模式 */
    fun peek() {
        if (!active) return
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
        host.onQuietVisual(peek = true)
    }

    private fun schedule() {
        tick?.let { handler.removeCallbacks(it) }
        tick = Runnable {
            if (!active) return@Runnable
            val now = SystemClock.elapsedRealtime()
            if (now >= peekUntil) host.onQuietVisual(peek = false)
            host.onQuietTick((now - startedAt) / 1000L)
            schedule()
        }
        handler.postDelayed(tick!!, TICK_MS)
    }
}
