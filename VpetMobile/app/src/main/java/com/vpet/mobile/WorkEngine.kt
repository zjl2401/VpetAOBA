package com.vpet.mobile

import android.graphics.Point
import android.os.Handler
import android.os.Looper
import kotlin.math.hypot
import kotlin.random.Random

/**
 * 工作运送核心：对照桌面 `_start_work_impl` / `_work_move_step` / `_work_arrived`。
 * continuous=true 为自由运送（点结束才停）；否则送到 workTotal 箱结束。
 */
class WorkEngine(
    private val host: Host,
    continuous: Boolean = true,
    total: Int = WORK_BOX_TOTAL_DEFAULT,
) {
    interface Host {
        fun screenSize(): Point
        fun petSize(): Int
        fun petTopLeft(): Point
        fun setPetTopLeft(x: Int, y: Int)
        fun onWorkVisual(carrying: Boolean, useWorkSprites: Boolean)
        fun onWorkDir(dir: SpriteAssets.Dir)
        fun onProps(startBoxVisible: Boolean, flagX: Int, flagY: Int, startX: Int, startY: Int, stack: Int)
        fun onProgress(delivered: Int, total: Int, continuous: Boolean)
        fun onWorkFinished(delivered: Int, continuousEnd: Boolean)
        fun toast(msg: String)
        fun onFlagMovedFar() {}
        fun onBoxDelivered() {}
        /** 对照 `_try_voice_work`：每 [WORK_VOICE_STEP_INTERVAL] 步抽检一次。 */
        fun onWorkVoiceTick() {}
    }

    companion object {
        const val WORK_ARRIVE_DIST = 18
        const val WORK_MIN_SPAN = 300
        const val WORK_BOX_TOTAL_DEFAULT = 5
        const val WORK_MOVE_INTERVAL_MS = 55L
        const val WORK_PROP_SIZE = 96
        const val WORK_STACK_OFFSET = 64
        const val WORK_VOICE_STEP_INTERVAL = 24
        const val MOVE_STEP = 2
    }

    enum class Phase { TO_START, TO_END, FINISH }

    var active = false
        private set
    private val continuous = continuous
    val isContinuous: Boolean get() = continuous
    private val workTotal = total.coerceIn(1, 30)
    private var phase = Phase.TO_START
    private var delivered = 0
    private var carrying = false
    private var stack = 0
    private var startX = 0
    private var startY = 0
    private var endFootX = 0
    private var endFootY = 0
    private var voiceSteps = 0
    private val handler = Handler(Looper.getMainLooper())
    private var tick: Runnable? = null

    fun start() {
        stop(internal = true)
        val scr = host.screenSize()
        val pet = host.petSize()
        val margin = 80
        val maxX = (scr.x - pet - margin).coerceAtLeast(margin)
        val maxY = (scr.y - pet - margin).coerceAtLeast(margin)
        startX = Random.nextInt(margin, maxX + 1)
        startY = Random.nextInt(margin, maxY + 1)
        val startCx = startX + pet / 2
        val startCy = startY + pet / 2
        var bestDist = -1.0
        var bestEx = margin
        var bestEy = margin
        repeat(40) {
            val ex = Random.nextInt(margin, maxX + 1)
            val ey = Random.nextInt(margin, maxY + 1)
            val d = hypot(
                (ex + pet / 2 - startCx).toDouble(),
                (ey + pet / 2 - startCy).toDouble(),
            )
            if (d >= WORK_MIN_SPAN && d > bestDist) {
                bestDist = d
                bestEx = ex
                bestEy = ey
            }
        }
        endFootX = bestEx + pet / 2
        endFootY = bestEy + pet
        delivered = 0
        carrying = false
        stack = 0
        voiceSteps = 0
        phase = Phase.TO_START
        active = true
        host.setPetTopLeft(startX, startY)
        host.onWorkVisual(carrying = false, useWorkSprites = false)
        syncProps()
        host.onProgress(delivered, workTotal, continuous)
        host.toast(if (continuous) "自由运送中 · 菜单可结束" else "运送 ${workTotal} 箱")
        schedule()
    }

    fun stop(internal: Boolean = false) {
        active = false
        tick?.let { handler.removeCallbacks(it) }
        tick = null
        if (!internal) {
            host.onWorkVisual(carrying = false, useWorkSprites = false)
            host.onProps(false, 0, 0, 0, 0, 0)
            host.onWorkFinished(delivered, continuousEnd = continuous)
        }
    }

    fun endFromMenu() {
        if (!active) return
        stop()
        host.toast("运送结束 · 共 $delivered 箱")
    }

    /** 对照 `_work_set_end_from_flag_foot`：旗脚挪到哪，终点跟到哪。 */
    fun moveEndFoot(footX: Int, footY: Int) {
        if (!active) return
        val scr = host.screenSize()
        val pet = host.petSize()
        val margin = 80
        val maxX = (scr.x - pet - margin).coerceAtLeast(margin)
        val maxY = (scr.y - pet - margin).coerceAtLeast(margin)
        val minFx = margin + pet / 2
        val maxFx = maxX + pet / 2
        val minFy = margin + pet
        val maxFy = maxY + pet
        endFootX = footX.coerceIn(minFx, maxFx)
        endFootY = footY.coerceIn(minFy, maxFy)
        syncProps()
    }

    /** 拖旗松手：本地堆箱从新旗脚重计（对照 work_local_stack=0）。 */
    fun onFlagDragReleased(movedPx: Int) {
        if (!active) return
        stack = 0
        syncProps()
        if (movedPx >= 40) host.onFlagMovedFar()
    }

    fun endFoot(): Point = Point(endFootX, endFootY)

    private fun schedule() {
        tick?.let { handler.removeCallbacks(it) }
        tick = Runnable { step() }
        handler.postDelayed(tick!!, WORK_MOVE_INTERVAL_MS)
    }

    private fun step() {
        if (!active) return
        val pet = host.petSize()
        val stepPx = MOVE_STEP

        when (phase) {
            Phase.FINISH -> {
                stop()
                host.toast("运完了！共 $delivered 箱")
                return
            }
            Phase.TO_START -> {
                // 对照桌面：中心点走到起点中心
                val tx = startX + pet / 2
                val ty = startY + pet / 2
                syncProps()
                if (distCenterTo(tx, ty) <= WORK_ARRIVE_DIST) {
                    arrivedStart()
                } else {
                    moveToward(tx, ty, stepPx)
                    host.onWorkVisual(carrying = false, useWorkSprites = false)
                    maybeVoiceTick()
                }
            }
            Phase.TO_END -> {
                val feet = feetNow()
                syncProps()
                if (hypot((endFootX - feet.x).toDouble(), (endFootY - feet.y).toDouble()) <= WORK_ARRIVE_DIST) {
                    arrivedEnd()
                } else {
                    // 寻路目标：脚踩旗脚时的中心（_work_dest_center_xy）
                    val tx = endFootX
                    val ty = endFootY - pet / 2
                    moveToward(tx, ty, stepPx)
                    host.onWorkVisual(carrying = true, useWorkSprites = true)
                    maybeVoiceTick()
                }
            }
        }
        if (active) schedule()
    }

    private fun maybeVoiceTick() {
        voiceSteps += 1
        if (voiceSteps % WORK_VOICE_STEP_INTERVAL == 0) {
            host.onWorkVoiceTick()
        }
    }

    private fun feetNow(): Point {
        val tl = host.petTopLeft()
        val pet = host.petSize()
        return Point(tl.x + pet / 2, tl.y + pet)
    }

    private fun distCenterTo(tx: Int, ty: Int): Double {
        val tl = host.petTopLeft()
        val pet = host.petSize()
        val cx = tl.x + pet / 2
        val cy = tl.y + pet / 2
        return hypot((tx - cx).toDouble(), (ty - cy).toDouble())
    }

    private fun moveToward(tx: Int, ty: Int, stepPx: Int) {
        val tl = host.petTopLeft()
        val pet = host.petSize()
        val cx = tl.x + pet / 2
        val cy = tl.y + pet / 2
        val dx = tx - cx
        val dy = ty - cy
        val dir = when {
            kotlin.math.abs(dx) >= kotlin.math.abs(dy) && dx != 0 ->
                if (dx < 0) SpriteAssets.Dir.LEFT else SpriteAssets.Dir.RIGHT
            dy != 0 ->
                if (dy < 0) SpriteAssets.Dir.BACK else SpriteAssets.Dir.FRONT
            else -> SpriteAssets.Dir.FRONT
        }
        host.onWorkDir(dir)
        val mx = dir.dx * stepPx
        val my = dir.dy * stepPx
        val scr = host.screenSize()
        val nx = (tl.x + mx).coerceIn(0, (scr.x - pet).coerceAtLeast(0))
        val ny = (tl.y + my).coerceIn(0, (scr.y - pet).coerceAtLeast(0))
        host.setPetTopLeft(nx, ny)
    }

    private fun arrivedStart() {
        if (!continuous && delivered >= workTotal && !carrying) {
            phase = Phase.FINISH
            return
        }
        if (!carrying) {
            // 搬走起点箱；若未达总量，立刻再生成下一箱（_work_should_keep_start_box）
            carrying = true
        }
        phase = Phase.TO_END
        syncProps()
        host.onWorkVisual(true, true)
    }

    private fun arrivedEnd() {
        if (carrying) {
            carrying = false
            delivered += 1
            stack += 1
            host.onProgress(delivered, workTotal, continuous)
            host.onBoxDelivered()
        }
        if (continuous) {
            phase = Phase.TO_START
        } else if (delivered >= workTotal) {
            phase = Phase.FINISH
        } else {
            phase = Phase.TO_START
        }
        syncProps()
        host.onWorkVisual(false, false)
    }

    /** 对照 `_work_should_keep_start_box`。 */
    private fun shouldKeepStartBox(): Boolean {
        if (phase == Phase.FINISH) return false
        if (continuous) return true
        val carry = if (carrying) 1 else 0
        return (delivered + carry) < workTotal
    }

    private fun syncProps() {
        val prop = WORK_PROP_SIZE
        val pet = host.petSize()
        val showStart = shouldKeepStartBox()
        // 旗顶左：旗脚在底边中心
        val flagX = endFootX - prop / 2
        val flagY = endFootY - prop
        // 起点箱：坐在起点顶边之上（对照 work_start_y - ph）
        val boxX = startX + pet / 2 - prop / 2
        val boxY = startY - prop
        host.onProps(
            startBoxVisible = showStart,
            flagX = flagX,
            flagY = flagY,
            startX = boxX,
            startY = boxY,
            stack = stack,
        )
    }
}
