package com.vpet.mobile

import android.os.SystemClock

/**
 * 走动转向节流：对照桌面 `_resolve_walk_direction`。
 * 变向连打超过 [STREAK_MAX_MS] 则锁定当前方向 [LOCK_MS]。
 */
class WalkTurnGuard {
    companion object {
        const val STREAK_MAX_MS = 3000L
        const val GAP_RESET_MS = 450L
        const val LOCK_MS = 1800L
    }

    private var streakStartMs = 0L
    private var lastChangeMs = 0L
    private var lockUntilMs = 0L
    private var lockedDir: SpriteAssets.Dir? = null

    fun reset() {
        streakStartMs = 0L
        lastChangeMs = 0L
        lockUntilMs = 0L
        lockedDir = null
    }

    fun resolve(proposed: SpriteAssets.Dir, current: SpriteAssets.Dir): SpriteAssets.Dir {
        val now = SystemClock.elapsedRealtime()
        val locked = lockedDir
        if (now < lockUntilMs && locked != null) return locked

        if (proposed == current) {
            if (streakStartMs != 0L && lastChangeMs != 0L && now - lastChangeMs >= GAP_RESET_MS) {
                streakStartMs = 0L
            }
            return proposed
        }

        if (streakStartMs == 0L || lastChangeMs == 0L || now - lastChangeMs > GAP_RESET_MS) {
            streakStartMs = now
            lastChangeMs = now
            return proposed
        }

        lastChangeMs = now
        if (now - streakStartMs >= STREAK_MAX_MS) {
            lockUntilMs = now + LOCK_MS
            lockedDir = current
            streakStartMs = 0L
            return current
        }
        return proposed
    }
}
