package com.vpet.mobile

import android.annotation.SuppressLint
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.graphics.PixelFormat
import android.graphics.Point
import android.os.Build
import android.os.IBinder
import android.os.SystemClock
import android.util.DisplayMetrics
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.WindowManager
import android.widget.ImageView
import android.widget.Toast
import androidx.core.app.NotificationCompat
import com.vpet.mobile.databinding.OverlayPetBinding
import kotlin.math.abs

class PetOverlayService : Service() {

    companion object {
        const val ACTION_START = "com.vpet.mobile.START_OVERLAY"
        const val ACTION_STOP = "com.vpet.mobile.STOP_OVERLAY"
        const val ACTION_RESIZE = "com.vpet.mobile.RESIZE_OVERLAY"
        const val ACTION_OPEN_MENU = "com.vpet.mobile.OPEN_MENU"
        const val ACTION_FEED = "com.vpet.mobile.FEED_PET"
        const val ACTION_FEED_DRAG = "com.vpet.mobile.FEED_DRAG"
        const val ACTION_SYNC_FLOWER = "com.vpet.mobile.SYNC_FLOWER"
        const val EXTRA_FOOD_ID = "food_id"
        private const val CHANNEL_ID = "vpet_overlay"
        private const val NOTIFY_ID = 1001
        private const val CLICK_SLOP = 16
    }

    private var windowManager: WindowManager? = null
    private var binding: OverlayPetBinding? = null
    private var layoutParams: WindowManager.LayoutParams? = null
    private var animator: PetAnimator? = null
    private var menuPanel: PetMenuPanel? = null
    private var menuActions: PetMenuActions? = null
    private var hub: PetModeHub? = null
    private var scheduleTicker: ScheduleTicker? = null
    private var pendingFeedFoodId: String? = null
    private var feedHintToast: Toast? = null

    private var screenW = 1080
    private var screenH = 1920

    override fun onBind(intent: Intent?): IBinder? = null

    private var exiting = false

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_STOP -> {
                requestExit()
                return START_NOT_STICKY
            }
            ACTION_RESIZE -> {
                animator?.applyDisplaySize()
                try {
                    windowManager?.updateViewLayout(binding?.root, layoutParams)
                } catch (_: Exception) {
                }
                hub?.refreshCompanionSize()
                hub?.playSizeDissolve()
            }
            ACTION_OPEN_MENU -> {
                if (binding == null) {
                    startForeground(NOTIFY_ID, buildNotification())
                    showOverlay()
                }
                menuPanel?.show()
            }
            ACTION_FEED -> {
                if (binding == null) {
                    startForeground(NOTIFY_ID, buildNotification())
                    showOverlay()
                }
                val foodId = intent.getStringExtra(EXTRA_FOOD_ID)
                hub?.playFeedAnim(foodId)
            }
            ACTION_FEED_DRAG -> {
                if (binding == null) {
                    startForeground(NOTIFY_ID, buildNotification())
                    showOverlay()
                }
                pendingFeedFoodId = intent.getStringExtra(EXTRA_FOOD_ID)
                feedHintToast?.cancel()
                feedHintToast = Toast.makeText(this, "拖到桌宠上松手喂食（点别处取消）", Toast.LENGTH_LONG)
                feedHintToast?.show()
            }
            ACTION_SYNC_FLOWER -> {
                hub?.syncHeadFlower()
            }
            else -> {
                startForeground(NOTIFY_ID, buildNotification())
                if (binding == null) showOverlay()
            }
        }
        return START_STICKY
    }

    override fun onDestroy() {
        scheduleTicker?.stop()
        scheduleTicker = null
        hub?.destroy()
        hub = null
        menuPanel?.hide()
        animator?.stop()
        removeOverlay()
        super.onDestroy()
    }

    private fun buildNotification(): Notification {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val mgr = getSystemService(NotificationManager::class.java)
            mgr.createNotificationChannel(
                NotificationChannel(
                    CHANNEL_ID,
                    getString(R.string.overlay_channel),
                    NotificationManager.IMPORTANCE_LOW,
                ),
            )
        }
        // 点通知 → 打开菜单，不拉回启动页
        val openMenu = PendingIntent.getService(
            this, 1,
            Intent(this, PetOverlayService::class.java).setAction(ACTION_OPEN_MENU),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val stop = PendingIntent.getService(
            this, 2,
            Intent(this, PetOverlayService::class.java).setAction(ACTION_STOP),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(getString(R.string.app_name))
            .setContentText(getString(R.string.overlay_notify))
            .setSmallIcon(R.drawable.ic_pet_notify)
            .setContentIntent(openMenu)
            .addAction(0, getString(R.string.overlay_notify_action_menu), openMenu)
            .addAction(0, getString(R.string.overlay_notify_action_stop), stop)
            .setOngoing(true)
            .setSilent(true)
            .build()
    }

    @SuppressLint("ClickableViewAccessibility", "InflateParams")
    private fun showOverlay() {
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        binding = OverlayPetBinding.inflate(LayoutInflater.from(this))

        val metrics = DisplayMetrics()
        @Suppress("DEPRECATION")
        windowManager?.defaultDisplay?.getMetrics(metrics)
        screenW = metrics.widthPixels
        screenH = metrics.heightPixels

        layoutParams = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT,
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = 80
            y = 280
        }

        animator = PetAnimator(this, binding!!.overlayPet) {
            if (hub?.onWalkAnimStep() == true) stepLocomotion()
        }
        animator!!.applyDisplaySize()
        animator!!.setMode(PetAnimator.Mode.STAND)

        hub = PetModeHub(
            context = this,
            animator = animator!!,
            windowManager = windowManager,
            screenSize = { Point(screenW, screenH) },
            petSize = { PetPrefs.sizePx(this) },
            petTopLeft = {
                val lp = layoutParams ?: return@PetModeHub Point(0, 0)
                Point(lp.x, lp.y)
            },
            setPetTopLeft = { x, y ->
                val lp = layoutParams ?: return@PetModeHub
                lp.x = x
                lp.y = y
                try {
                    windowManager?.updateViewLayout(binding?.root, lp)
                } catch (_: Exception) {
                }
            },
            raisePetOverlay = {
                val root = binding?.root ?: return@PetModeHub
                val lp = layoutParams ?: return@PetModeHub
                try {
                    windowManager?.removeView(root)
                    windowManager?.addView(root, lp)
                } catch (_: Exception) {
                }
            },
        )
        hub!!.attach()

        scheduleTicker?.stop()
        scheduleTicker = ScheduleTicker(this) { text ->
            Toast.makeText(this, "日程：$text", Toast.LENGTH_LONG).show()
        }.also { it.start() }

        menuActions = PetMenuActions(
            context = this,
            animator = animator!!,
            hub = hub!!,
            onResize = {
                try {
                    windowManager?.updateViewLayout(binding?.root, layoutParams)
                } catch (_: Exception) {
                }
            },
            onExitOverlay = { requestExit() },
        )
        menuPanel = PetMenuPanel(
            context = this,
            actions = menuActions!!,
            asOverlay = true,
            windowManager = windowManager,
            petTopLeft = {
                Point(layoutParams?.x ?: 80, layoutParams?.y ?: 280)
            },
            petSize = { PetPrefs.sizePx(this) },
            screenSize = { Point(screenW, screenH) },
        )

        setupDragAndTap(binding!!.overlayPet)
        windowManager?.addView(binding!!.root, layoutParams)
    }

    private fun requestExit() {
        if (exiting) return
        exiting = true
        menuPanel?.hide()
        val root = binding?.root
        val pet = binding?.overlayPet
        val hubRef = hub
        if (hubRef != null) {
            hubRef.playExitThen { stopSelf() }
        } else {
            try {
                pet?.animate()?.alpha(0.15f)?.setDuration(500L)?.start()
                root?.animate()?.alpha(0.35f)?.setDuration(500L)?.start()
            } catch (_: Exception) {
            }
            android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({ stopSelf() }, 400L)
        }
    }

    private fun stepLocomotion() {
        val lp = layoutParams ?: return
        val petW = binding?.overlayPet?.width?.coerceAtLeast(1) ?: PetPrefs.sizePx(this)
        val petH = binding?.overlayPet?.height?.coerceAtLeast(1) ?: PetPrefs.sizePx(this)
        val (dx, dy) = animator?.walkDelta() ?: (0 to 0)
        var nx = lp.x + dx
        var ny = lp.y + dy
        val maxX = (screenW - petW).coerceAtLeast(0)
        val maxY = (screenH - petH).coerceAtLeast(0)
        var bounced = false
        if (nx < 0 || nx > maxX || ny < 0 || ny > maxY) {
            val next = animator?.pickInboundDir { d ->
                val tx = lp.x + d.dx * (animator?.walkStepPx() ?: 2)
                val ty = lp.y + d.dy * (animator?.walkStepPx() ?: 2)
                tx in 0..maxX && ty in 0..maxY
            }
            if (next != null) {
                animator?.setWalkDir(next)
                val (ndx, ndy) = animator?.walkDelta() ?: (0 to 0)
                nx = (lp.x + ndx).coerceIn(0, maxX)
                ny = (lp.y + ndy).coerceIn(0, maxY)
            } else {
                nx = lp.x.coerceIn(0, maxX)
                ny = lp.y.coerceIn(0, maxY)
                bounced = true
            }
            if (bounced) hub?.let { /* 步数耗尽由 hub 处理 */ }
        }
        lp.x = nx.coerceIn(0, maxX)
        lp.y = ny.coerceIn(0, maxY)
        try {
            windowManager?.updateViewLayout(binding?.root, lp)
        } catch (_: Exception) {
        }
    }

    private fun setupDragAndTap(pet: ImageView) {
        var downX = 0f
        var downY = 0f
        var startX = 0
        var startY = 0
        var moved = false
        var wasLoco = false
        var downAt = 0L
        var yuqiFired = false

        pet.setOnTouchListener { _, event ->
            val lp = layoutParams ?: return@setOnTouchListener false
            val h = hub
            val busy = h?.isWorking == true || h?.isFollowing == true
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    downX = event.rawX
                    downY = event.rawY
                    startX = lp.x
                    startY = lp.y
                    moved = false
                    yuqiFired = false
                    downAt = SystemClock.elapsedRealtime()
                    wasLoco = h?.locomotionEnabled == true
                    if (wasLoco) h?.stopLocomotion()
                    h?.resetDragYuqiSession()
                    h?.noteUserActivity()
                    menuPanel?.hide()
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    if (busy) return@setOnTouchListener true
                    if (h?.isQuiet == true) return@setOnTouchListener true
                    val dx = (event.rawX - downX).toInt()
                    val dy = (event.rawY - downY).toInt()
                    if (abs(dx) > CLICK_SLOP || abs(dy) > CLICK_SLOP) {
                        if (!moved) {
                            moved = true
                            animator?.setMode(PetAnimator.Mode.WALK)
                        }
                    }
                    lp.x = startX + dx
                    lp.y = startY + dy
                    windowManager?.updateViewLayout(binding?.root, lp)
                    h?.noteUserActivity()
                    val held = SystemClock.elapsedRealtime() - downAt
                    if (moved && held >= PetAnimator.DRAG_YUQI_MS) {
                        if (h?.onDragHeld(held) == true) {
                            yuqiFired = true
                        }
                    }
                    true
                }
                MotionEvent.ACTION_UP -> {
                    if (!moved) {
                        val foodId = pendingFeedFoodId
                        if (foodId != null) {
                            pendingFeedFoodId = null
                            completeFeedDrag(foodId)
                        } else if (h?.isQuiet == true) {
                            h.peekQuiet()
                        } else {
                            // 部位感叹：相对立绘坐标
                            val part = PetClickZones.partAt(
                                event.x, event.y, pet.width, pet.height,
                            )
                            if (part != null) h?.tryInterjection(part)
                            h?.noteUserActivity()
                            menuPanel?.toggle()
                        }
                    } else if (!busy && h?.isQuiet != true) {
                        // 拖拽落地 settle
                        h?.playLandSettle { ny ->
                            lp.y = ny.coerceIn(0, (screenH - (pet.height.coerceAtLeast(1))).coerceAtLeast(0))
                            try {
                                windowManager?.updateViewLayout(binding?.root, lp)
                            } catch (_: Exception) {
                            }
                        }
                    }
                    true
                }
                else -> false
            }
        }
    }

    private fun completeFeedDrag(foodId: String) {
        val food = FoodCatalog.byId(foodId) ?: return
        if (!FoodInventoryStore.consumeOne(this, foodId)) {
            Toast.makeText(this, "没有${food.label}了", Toast.LENGTH_SHORT).show()
            return
        }
        AppDataStore.addStaminaMood(this, food.stamina, food.mood)
        hub?.playFeedAnim(foodId)
        Toast.makeText(
            this,
            "喂苍叶：${food.label}（体+${food.stamina} 心+${food.mood}）",
            Toast.LENGTH_SHORT,
        ).show()
    }

    private fun removeOverlay() {
        menuPanel?.hide()
        hub?.destroy()
        hub = null
        binding?.root?.let { v ->
            try {
                windowManager?.removeView(v)
            } catch (_: Exception) {
            }
        }
        binding = null
        animator = null
        menuPanel = null
        menuActions = null
    }
}
