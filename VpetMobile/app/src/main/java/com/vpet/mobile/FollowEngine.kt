package com.vpet.mobile

import android.graphics.Point
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import kotlin.math.hypot

/**
 * 跟随模式：对照桌面 `_follow_tick` / FOLLOW_* 常量。
 * 目标点由宿主更新（全屏触控或拖动）。
 */
class FollowEngine(private val host: Host) {
    interface Host {
        fun screenSize(): Point
        fun petSize(): Int
        fun petTopLeft(): Point
        fun setPetTopLeft(x: Int, y: Int)
        fun onFollowWalk(walking: Boolean)
        fun onFollowDir(dir: SpriteAssets.Dir)
        fun onDizzy()
        fun toast(msg: String)
    }

    companion object {
        /** 位移加快；立绘切帧仍由 PetAnimator.WALK_FRAME_MS 控制，不随此加速。 */
        const val FOLLOW_MOVE_INTERVAL_MS = 45L
        const val FOLLOW_STOP_DIST = 65
        const val FOLLOW_FAR_DIST = 280
        const val FOLLOW_DIZZY_STAND_MS = 3000L
        const val FOLLOW_DIZZY_SPIN_STEPS = 4
        const val FOLLOW_DIZZY_TEXT = "我晕了……"
        const val MOVE_STEP = 3
    }

    var active = false
        private set
    private var targetX = 0
    private var targetY = 0
    private var hasTarget = false
    private var dizzyUntil = 0L
    private var lastSignX = 0
    private var lastSignY = 0
    private var dirFlipCount = 0
    private val handler = Handler(Looper.getMainLooper())
    private var tick: Runnable? = null

    fun start() {
        stop(internal = true)
        active = true
        hasTarget = false
        dizzyUntil = 0L
        dirFlipCount = 0
        host.onFollowWalk(false)
        schedule()
    }

    fun stop(internal: Boolean = false) {
        active = false
        tick?.let { handler.removeCallbacks(it) }
        tick = null
        hasTarget = false
        if (!internal) host.onFollowWalk(false)
    }

    /** 屏幕绝对坐标（脚目标或触点） */
    fun setTarget(x: Int, y: Int) {
        if (!active) return
        targetX = x
        targetY = y
        hasTarget = true
    }

    private fun schedule() {
        tick?.let { handler.removeCallbacks(it) }
        tick = Runnable { step() }
        handler.postDelayed(tick!!, FOLLOW_MOVE_INTERVAL_MS)
    }

    private fun step() {
        if (!active) return
        val now = SystemClock.elapsedRealtime()
        if (now < dizzyUntil) {
            host.onFollowWalk(false)
            schedule()
            return
        }
        if (!hasTarget) {
            host.onFollowWalk(false)
            schedule()
            return
        }
        val pet = host.petSize()
        val scr = host.screenSize()
        val stepPx = MOVE_STEP
        val tl = host.petTopLeft()
        val cx = tl.x + pet / 2
        val cy = tl.y + pet / 2
        val dx = targetX - cx
        val dy = targetY - cy
        val dist = hypot(dx.toDouble(), dy.toDouble())
        if (dist <= FOLLOW_STOP_DIST) {
            host.onFollowWalk(false)
            schedule()
            return
        }
        val sx = when {
            dx > 8 -> 1
            dx < -8 -> -1
            else -> 0
        }
        val sy = when {
            dy > 8 -> 1
            dy < -8 -> -1
            else -> 0
        }
        if (sx != 0 && lastSignX != 0 && sx != lastSignX) dirFlipCount++
        if (sy != 0 && lastSignY != 0 && sy != lastSignY) dirFlipCount++
        if (sx != 0) lastSignX = sx
        if (sy != 0) lastSignY = sy
        if (dirFlipCount >= FOLLOW_DIZZY_SPIN_STEPS) {
            dirFlipCount = 0
            dizzyUntil = now + FOLLOW_DIZZY_STAND_MS
            host.onDizzy()
            host.toast(FOLLOW_DIZZY_TEXT)
            host.onFollowWalk(false)
            schedule()
            return
        }
        // 正交四向：主轴优先（对齐桌面跟随观感）
        val dir = when {
            kotlin.math.abs(dx) >= kotlin.math.abs(dy) && sx != 0 ->
                if (sx < 0) SpriteAssets.Dir.LEFT else SpriteAssets.Dir.RIGHT
            sy != 0 ->
                if (sy < 0) SpriteAssets.Dir.BACK else SpriteAssets.Dir.FRONT
            else -> SpriteAssets.Dir.FRONT
        }
        host.onFollowDir(dir)
        val mx = dir.dx * stepPx
        val my = dir.dy * stepPx
        val nx = (tl.x + mx).coerceIn(0, (scr.x - pet).coerceAtLeast(0))
        val ny = (tl.y + my).coerceIn(0, (scr.y - pet).coerceAtLeast(0))
        host.setPetTopLeft(nx, ny)
        host.onFollowWalk(true)
        schedule()
    }
}
