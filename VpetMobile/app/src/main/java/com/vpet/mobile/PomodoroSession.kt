package com.vpet.mobile

import android.os.Handler
import android.os.Looper
import android.os.SystemClock

/**
 * 番茄钟：对照 `_start_pomodoro` —— 工作=运送，休息=睡眠，到点循环。
 * 满 4 轮额外提示；可随时结束。
 */
class PomodoroSession(private val host: Host) {
    interface Host {
        fun onPomoWorkStart(round: Int, workMs: Long)
        fun onPomoRestStart(round: Int, restMs: Long)
        fun onPomoTick(phase: String, round: Int, remainMs: Long)
        fun onPomoRoundDone(completed: Int, nextRound: Int)
        fun onPomoEnded(completed: Int)
        fun toast(msg: String)
    }

    companion object {
        fun formatRemain(ms: Long): String {
            val sec = (ms / 1000).coerceAtLeast(0)
            val m = sec / 60
            val s = sec % 60
            return "%d:%02d".format(m, s)
        }
    }

    var active = false
        private set
    var phase: String = ""
        private set
    var round = 1
        private set
    var completed = 0
        private set

    private var workMs = 25 * 60_000L
    private var restMs = 5 * 60_000L
    private var phaseEndsAt = 0L
    private val handler = Handler(Looper.getMainLooper())
    private var tick: Runnable? = null
    private var phaseJob: Runnable? = null

    fun start(workMinutes: Int, restMinutes: Int) {
        stop(internal = true)
        workMs = workMinutes.coerceIn(1, 180) * 60_000L
        restMs = restMinutes.coerceIn(1, 60) * 60_000L
        active = true
        round = 1
        completed = 0
        phase = "work"
        host.toast(
            "番茄钟 · 第1轮 · 工作${workMinutes}分 / 休息${restMinutes}分",
        )
        beginWork()
    }

    fun stop(internal: Boolean = false) {
        val was = active
        val done = completed
        active = false
        phase = ""
        clearJobs()
        if (was && !internal) host.onPomoEnded(done)
    }

    fun endFromMenu() {
        if (!active) return
        val done = completed
        stop(internal = true)
        host.onPomoEnded(done)
        host.toast("番茄钟已结束 · 完成 $done 轮")
    }

    private fun beginWork() {
        if (!active) return
        phase = "work"
        phaseEndsAt = SystemClock.elapsedRealtime() + workMs
        host.onPomoWorkStart(round, workMs)
        schedulePhaseEnd(workMs) { onWorkDone() }
        scheduleTick()
    }

    private fun beginRest() {
        if (!active) return
        phase = "rest"
        phaseEndsAt = SystemClock.elapsedRealtime() + restMs
        host.onPomoRestStart(round, restMs)
        schedulePhaseEnd(restMs) { onRestDone() }
        scheduleTick()
    }

    private fun onWorkDone() {
        if (!active || phase != "work") return
        host.toast("第 $round 轮工作结束，进入休息")
        beginRest()
    }

    private fun onRestDone() {
        if (!active || phase != "rest") return
        completed += 1
        val next = completed + 1
        round = next
        host.onPomoRoundDone(completed, next)
        host.toast("第 $completed 轮番茄完成 · 开始第 $next 轮")
        if (completed % 4 == 0) {
            handler.postDelayed({
                if (active) host.toast("本会话已完成 $completed 轮番茄，节奏不错！")
            }, 800L)
        }
        beginWork()
    }

    private fun schedulePhaseEnd(delay: Long, block: () -> Unit) {
        phaseJob?.let { handler.removeCallbacks(it) }
        phaseJob = Runnable { block() }
        handler.postDelayed(phaseJob!!, delay)
    }

    private fun scheduleTick() {
        tick?.let { handler.removeCallbacks(it) }
        tick = Runnable {
            if (!active) return@Runnable
            val remain = (phaseEndsAt - SystemClock.elapsedRealtime()).coerceAtLeast(0L)
            host.onPomoTick(phase, round, remain)
            scheduleTick()
        }
        handler.postDelayed(tick!!, 500L)
    }

    private fun clearJobs() {
        tick?.let { handler.removeCallbacks(it) }
        phaseJob?.let { handler.removeCallbacks(it) }
        tick = null
        phaseJob = null
    }
}
