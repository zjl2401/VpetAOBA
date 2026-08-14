package com.vpet.mobile

import android.annotation.SuppressLint
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.graphics.PixelFormat
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.PowerManager
import android.view.Gravity
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.ImageView
import android.app.KeyguardManager

/**
 * 熄屏显示：桌宠开启且开关打开时，锁屏/点亮屏幕显示睡觉·刷视频·玩游戏·听音乐姿势。
 * 真·系统 AOD 第三方无法绘制；本层用 FLAG_SHOW_WHEN_LOCKED，点亮锁屏即可看到。
 * 不可触摸，不挡滑动解锁。
 */
class LockScreenPetOverlay(
    private val context: Context,
    private val windowManager: WindowManager,
    private val overlayRunning: () -> Boolean,
) {
    private val app = context.applicationContext
    private val handler = Handler(Looper.getMainLooper())
    private var host: FrameLayout? = null
    private var imageView: ImageView? = null
    private var animator: PetAnimator? = null
    private var lp: WindowManager.LayoutParams? = null
    private var receiver: BroadcastReceiver? = null
    private var attached = false
    private var showing = false
    private var lastPose: LockScreenPetStore.Pose? = null

    fun start() {
        if (receiver != null) return
        val r = object : BroadcastReceiver() {
            override fun onReceive(ctx: Context?, intent: Intent?) {
                when (intent?.action) {
                    Intent.ACTION_SCREEN_OFF -> onScreenOff()
                    Intent.ACTION_SCREEN_ON -> onScreenOn()
                    Intent.ACTION_USER_PRESENT -> onUnlocked()
                }
            }
        }
        receiver = r
        val filter = IntentFilter().apply {
            addAction(Intent.ACTION_SCREEN_OFF)
            addAction(Intent.ACTION_SCREEN_ON)
            addAction(Intent.ACTION_USER_PRESENT)
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            app.registerReceiver(r, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            @Suppress("DEPRECATION")
            app.registerReceiver(r, filter)
        }
        // 启动时若已在锁屏，立刻挂上
        handler.post { refreshVisibility() }
    }

    fun stop() {
        receiver?.let {
            try {
                app.unregisterReceiver(it)
            } catch (_: Exception) {
            }
        }
        receiver = null
        hide(remove = true)
    }

    /** 模式变化时由 Hub 调用，锁屏层若正在显示则立刻换姿势。 */
    fun onPoseChanged() {
        if (!showing) return
        applyPose(LockScreenPetStore.pose(app), force = true)
    }

    private fun onScreenOff() {
        if (!shouldShow()) {
            hide(remove = false)
            return
        }
        // 提前挂上，点亮瞬间即可看见（部分机型熄屏瞬间也会闪一下）
        show()
    }

    private fun onScreenOn() {
        refreshVisibility()
    }

    private fun onUnlocked() {
        hide(remove = false)
    }

    private fun refreshVisibility() {
        if (!shouldShow()) {
            hide(remove = false)
            return
        }
        val kg = app.getSystemService(Context.KEYGUARD_SERVICE) as? KeyguardManager
        val locked = kg?.isKeyguardLocked == true
        val pm = app.getSystemService(Context.POWER_SERVICE) as? PowerManager
        val interactive = pm?.isInteractive != false
        // 锁屏中（含刚熄屏/点亮）：显示；已解锁：隐藏
        if (locked || !interactive) {
            show()
        } else {
            hide(remove = false)
        }
    }

    private fun shouldShow(): Boolean {
        if (!overlayRunning()) return false
        if (!LockScreenPetStore.enabled(app)) return false
        return true
    }

    @SuppressLint("RtlHardcoded")
    private fun show() {
        ensureWindow()
        val h = host ?: return
        h.visibility = android.view.View.VISIBLE
        showing = true
        applyPose(LockScreenPetStore.pose(app), force = false)
        try {
            if (!attached) {
                windowManager.addView(h, lp)
                attached = true
            } else {
                windowManager.updateViewLayout(h, lp)
            }
        } catch (_: Exception) {
            try {
                windowManager.addView(h, lp)
                attached = true
            } catch (_: Exception) {
            }
        }
    }

    private fun hide(remove: Boolean) {
        showing = false
        lastPose = null
        animator?.stop()
        val h = host
        if (h != null) {
            h.visibility = android.view.View.GONE
            if (remove && attached) {
                try {
                    windowManager.removeView(h)
                } catch (_: Exception) {
                }
                attached = false
            }
        }
        if (remove) {
            host = null
            imageView = null
            animator = null
            lp = null
        }
    }

    private fun ensureWindow() {
        if (host != null) return
        val side = (PetPrefs.sizePx(app) * 0.92f).toInt().coerceIn(96, PetPrefs.SIZE_MAX_PX)
        val iv = ImageView(app).apply {
            layoutParams = FrameLayout.LayoutParams(side, side)
            scaleType = ImageView.ScaleType.FIT_XY
            importantForAccessibility = android.view.View.IMPORTANT_FOR_ACCESSIBILITY_NO
        }
        imageView = iv
        host = FrameLayout(app).apply {
            layoutParams = FrameLayout.LayoutParams(side, side)
            addView(iv)
            setBackgroundColor(android.graphics.Color.TRANSPARENT)
        }
        animator = PetAnimator(app, iv, onWalkMove = null)
        @Suppress("DEPRECATION")
        val flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
            WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE or
            WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
            WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS or
            WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED
        val params = WindowManager.LayoutParams(
            side,
            side,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            flags,
            PixelFormat.TRANSLUCENT,
        ).apply {
            gravity = Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL
            x = 0
            y = (side * 0.35f).toInt().coerceAtLeast(24)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                layoutInDisplayCutoutMode =
                    WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                fitInsetsTypes = 0
            }
        }
        lp = params
    }

    private fun applyPose(pose: LockScreenPetStore.Pose, force: Boolean) {
        val anim = animator ?: return
        if (!force && pose == lastPose) return
        lastPose = pose
        val mode = when (pose) {
            LockScreenPetStore.Pose.SLEEP -> PetAnimator.Mode.SLEEP
            LockScreenPetStore.Pose.VIDEO -> PetAnimator.Mode.WATCH_VIDEO
            LockScreenPetStore.Pose.GAME -> PetAnimator.Mode.PLAY_GAME
            LockScreenPetStore.Pose.MUSIC -> PetAnimator.Mode.MUSIC_STAND
        }
        anim.setMode(mode, driveMove = false)
        // 同 mode 时 setMode 会早退，强制刷一帧
        anim.forceSceneMode(mode)
    }
}
