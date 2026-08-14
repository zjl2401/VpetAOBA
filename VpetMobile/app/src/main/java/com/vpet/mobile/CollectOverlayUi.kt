package com.vpet.mobile

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Color
import android.graphics.PixelFormat
import android.graphics.Point
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.view.Gravity
import android.view.MotionEvent
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.TextView
import kotlin.math.hypot
import kotlin.random.Random

/**
 * 采集：对照桌面 game 模式——像素食物下落，靠近时桌宠切 happy 接住图。
 * 采集层负责触控；主宠 NOT_TOUCHABLE，避免抢走拖动。
 */
class CollectOverlayUi(
    private val context: Context,
    private val windowManager: WindowManager? = null,
    private val roomHost: FrameLayout? = null,
    private val screenSize: () -> Point,
    private val petSize: () -> Int,
    private val petTopLeft: () -> Point,
    private val setPetTopLeft: (Int, Int) -> Unit,
    private val raisePets: () -> Unit,
    private val setPetsTouchable: (Boolean) -> Unit,
    private val onNearFood: (Boolean) -> Unit,
    private val onFinished: () -> Unit,
) {
    companion object {
        private const val DURATION_MS = 30_000L
        private const val TICK_MS = 24L
        private const val BOX_DP = 56
        private const val SCORE_PER_CATCH = 10
        private const val PENALTY_MISS = 2
    }

    var active = false
        private set

    private val handler = Handler(Looper.getMainLooper())
    private var root: FrameLayout? = null
    private var hud: TextView? = null
    private var wmLp: WindowManager.LayoutParams? = null
    private var endsAt = 0L
    private var score = 0
    private var catches = 0
    private var misses = 0
    private var finished = false
    private var nearFood = false
    private var spawnJob: Runnable? = null
    private var tickJob: Runnable? = null
    private val drops = mutableListOf<Drop>()
    private lateinit var params: DifficultyParams.Params
    private var dragging = false

    private data class Drop(
        val view: ImageView,
        var x: Float,
        var y: Float,
        val speed: Float,
        val foodId: String,
        val size: Int,
    )

    fun start() {
        if (active) return
        active = true
        finished = false
        score = 0
        catches = 0
        misses = 0
        nearFood = false
        dragging = false
        drops.clear()
        params = DifficultyParams.of(context)
        FoodInventoryStore.ensureSeeded(context)
        endsAt = SystemClock.elapsedRealtime() + DURATION_MS
        ensureLayer()
        setPetsTouchable(false)
        raisePets()
        raiseCollectLayer()
        FirstPlayGuides.maybeShow(context, "gather")
        scheduleSpawn()
        scheduleTick()
    }

    fun stop() {
        if (!active && root == null) return
        active = false
        dragging = false
        spawnJob?.let { handler.removeCallbacks(it) }
        tickJob?.let { handler.removeCallbacks(it) }
        spawnJob = null
        tickJob = null
        drops.clear()
        detachLayer()
        setPetsTouchable(true)
        onNearFood(false)
    }

    @SuppressLint("ClickableViewAccessibility")
    private fun ensureLayer() {
        if (root != null) return
        val host = FrameLayout(context).apply {
            setBackgroundColor(0x22000812)
            isClickable = true
            setOnTouchListener { _, e ->
                when (e.actionMasked) {
                    MotionEvent.ACTION_DOWN -> {
                        dragging = true
                        movePetTo(e.rawX, e.rawY)
                    }
                    MotionEvent.ACTION_MOVE -> {
                        if (dragging) movePetTo(e.rawX, e.rawY)
                    }
                    MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                        dragging = false
                    }
                }
                true
            }
        }
        val hudTv = TextView(context).apply {
            setTextColor(0xFF88CCFF.toInt())
            textSize = 13f
            setPadding(dp(12), dp(8), dp(12), dp(8))
            setBackgroundColor(0xEE111122.toInt())
            gravity = Gravity.START
        }
        val endBtn = TextView(context).apply {
            text = "结束"
            setTextColor(0xFFFFCC88.toInt())
            textSize = 13f
            setPadding(dp(14), dp(8), dp(14), dp(8))
            setBackgroundColor(0xEE221818.toInt())
            setOnClickListener { finishRound() }
        }
        host.addView(
            hudTv,
            FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,
                FrameLayout.LayoutParams.WRAP_CONTENT,
            ).apply {
                gravity = Gravity.TOP or Gravity.START
                leftMargin = dp(12)
                topMargin = dp(48)
            },
        )
        host.addView(
            endBtn,
            FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,
                FrameLayout.LayoutParams.WRAP_CONTENT,
            ).apply {
                gravity = Gravity.TOP or Gravity.END
                rightMargin = dp(12)
                topMargin = dp(48)
            },
        )
        root = host
        hud = hudTv
        updateHud()

        if (windowManager != null && roomHost == null) {
            val lp = WindowManager.LayoutParams(
                WindowManager.LayoutParams.MATCH_PARENT,
                WindowManager.LayoutParams.MATCH_PARENT,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT,
            ).apply {
                gravity = Gravity.TOP or Gravity.START
            }
            wmLp = lp
            windowManager.addView(host, lp)
        } else {
            roomHost?.addView(
                host,
                FrameLayout.LayoutParams(
                    FrameLayout.LayoutParams.MATCH_PARENT,
                    FrameLayout.LayoutParams.MATCH_PARENT,
                ),
            )
        }
    }

    private fun raiseCollectLayer() {
        val host = root ?: return
        val lp = wmLp
        if (windowManager != null && roomHost == null && lp != null) {
            try {
                windowManager.removeView(host)
                windowManager.addView(host, lp)
            } catch (_: Exception) {
            }
        } else {
            host.bringToFront()
        }
    }

    private fun detachLayer() {
        val host = root ?: return
        try {
            if (windowManager != null && roomHost == null) windowManager.removeView(host)
            else roomHost?.removeView(host)
        } catch (_: Exception) {
        }
        root = null
        hud = null
        wmLp = null
    }

    private fun movePetTo(rawX: Float, rawY: Float) {
        val size = petSize()
        val scr = screenSize()
        val x = (rawX - size / 2f).toInt().coerceIn(0, (scr.x - size).coerceAtLeast(0))
        val y = (rawY - size / 2f).toInt().coerceIn(0, (scr.y - size).coerceAtLeast(0))
        setPetTopLeft(x, y)
    }

    private fun scheduleSpawn() {
        spawnJob = Runnable {
            if (!active || finished) return@Runnable
            if (SystemClock.elapsedRealtime() >= endsAt) return@Runnable
            spawnOne()
            val jitter = Random.nextLong(0, 200)
            handler.postDelayed(spawnJob!!, params.gameSpawnMs + jitter)
        }
        handler.postDelayed(spawnJob!!, params.gameSpawnMs)
    }

    private fun scheduleTick() {
        tickJob = object : Runnable {
            override fun run() {
                if (!active || finished) return
                if (SystemClock.elapsedRealtime() >= endsAt) {
                    finishRound()
                    return
                }
                stepDrops()
                updateHud()
                handler.postDelayed(this, TICK_MS)
            }
        }
        handler.post(tickJob!!)
    }

    private fun spawnOne() {
        val host = root ?: return
        val food = FoodCatalog.ALL.random()
        val size = dp(BOX_DP)
        val scr = screenSize()
        val x = Random.nextInt(20, (scr.x - size - 20).coerceAtLeast(40)).toFloat()
        val iv = ImageView(context).apply {
            scaleType = ImageView.ScaleType.FIT_CENTER
            setImageBitmap(FoodPixelArt.bitmapFor(food.id, size))
        }
        host.addView(iv, FrameLayout.LayoutParams(size, size).apply {
            leftMargin = x.toInt()
            topMargin = 80
        })
        val speed = (params.gameSpeed * context.resources.displayMetrics.density).coerceAtLeast(3f)
        drops += Drop(iv, x, 80f, speed, food.id, size)
    }

    private fun stepDrops() {
        val host = root ?: return
        val scr = screenSize()
        val pet = petTopLeft()
        val psz = petSize()
        val petCx = pet.x + psz / 2f
        val petCy = pet.y + psz / 2f
        val catchDist = params.gameCatchDistDp * context.resources.displayMetrics.density
        var near = false
        val remain = mutableListOf<Drop>()
        for (d in drops) {
            d.y += d.speed
            val lp = d.view.layoutParams as FrameLayout.LayoutParams
            lp.leftMargin = d.x.toInt()
            lp.topMargin = d.y.toInt()
            d.view.layoutParams = lp
            val bx = d.x + d.size / 2f
            val by = d.y + d.size / 2f
            val dist = hypot(bx - petCx, by - petCy)
            if (dist < catchDist * 1.35f) near = true
            if (dist < catchDist) {
                host.removeView(d.view)
                FoodInventoryStore.add(context, d.foodId, 1)
                AppDataStore.addStaminaMood(context, 1, 1)
                catches += 1
                score += SCORE_PER_CATCH
                if (catches % 5 == 0) {
                    AppDataStore.addStaminaMood(context, 0, 1)
                }
                continue
            }
            if (d.y > scr.y) {
                host.removeView(d.view)
                misses += 1
                score = (score - PENALTY_MISS).coerceAtLeast(0)
                continue
            }
            remain += d
        }
        drops.clear()
        drops.addAll(remain)
        if (near != nearFood) {
            nearFood = near
            onNearFood(near)
        }
    }

    private fun updateHud() {
        val left = ((endsAt - SystemClock.elapsedRealtime()) / 1000L).coerceAtLeast(0)
        hud?.text =
            "⏱ ${left}s  食物 $catches\n接住 $catches  错过 $misses  分 $score"
    }

    private fun finishRound() {
        if (finished) return
        finished = true
        active = false
        dragging = false
        spawnJob?.let { handler.removeCallbacks(it) }
        tickJob?.let { handler.removeCallbacks(it) }
        val coinGain = minOf(15, maxOf(0, score / 25 + catches / 3))
        if (coinGain > 0) WalletStore.grantCoins(context, coinGain)
        AppDataStore.unlock(context, "collect_play")
        val bal = WalletStore.coins(context)
        if (misses >= catches || catches == 0) {
            GameFailVoice.playHurt(context)
        }
        detachLayer()
        setPetsTouchable(true)
        onNearFood(false)
        GameClearUi.show(
            context,
            title = "采集完成！",
            subtitle = "接住 $catches · 得分 $score · 错过 $misses\n金币 +$coinGain · 钱包 $bal\n食物已进背包",
            accentHex = "#44FF88",
            onDismiss = onFinished,
        )
    }

    private fun dp(v: Int): Int =
        (v * context.resources.displayMetrics.density).toInt()
}
