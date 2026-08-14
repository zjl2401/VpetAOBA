package com.vpet.mobile

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.PixelFormat
import android.graphics.Point
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import android.widget.FrameLayout
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.sin
import kotlin.random.Random

/**
 * 桌宠背景特效：对照 pet.py Canvas 像素 FX（花/雨/灯泡/星/心/声波/ZZZ 等）。
 * 叠在立绘后方（比心在前）；点击穿透。
 */
class PetFxUi(
    private val context: Context,
    private val windowManager: WindowManager? = null,
    private val roomHost: FrameLayout? = null,
    private val petTopLeft: () -> Point,
    private val petSize: () -> Int,
    private val raisePet: (() -> Unit)? = null,
) {
    companion object {
        const val PAD = 28
        /** 灯泡额外上留白，避免被立绘头顶挡住 */
        const val BULB_TOP_EXTRA = 48
        const val MUSIC_WAVE_MS = 60L
        const val SLEEP_ZZZ_MS = 700L
        const val RAIN_MS = 80L
        const val WINK_MS = 100L
        const val BIXIN_MS = 48L
        const val KICK_MS = 80L
        const val BULB_MS = 160L
        const val HAPPY_HOLD_MS = 6000L
        const val LIKE_HOLD_MS = 3800L
        const val SHY_HOLD_MS = 4500L
        const val IDEA_HOLD_MS = 5720L
        const val SAD_HOLD_MS = 6500L
        const val WINK_HOLD_MS = 3800L
        const val BIXIN_HOLD_MS = 5200L
        const val KICK_HOLD_MS = 2200L
        const val DIZZY_HOLD_MS = 3000L
        const val FOOD_HOLD_MS = 2200L
        val MUSIC_COLORS = intArrayOf(Color.parseColor("#9EC8E8"), Color.parseColor("#D0E8F5"))
        /** 对照桌面 MUSIC_FOLDER_BASE_COLORS */
        private val MUSIC_WAVE_PALETTE = intArrayOf(
            Color.parseColor("#9EC8E8"),
            Color.parseColor("#8AA4C8"),
            Color.parseColor("#E8D6A0"),
            Color.parseColor("#E0A0AC"),
            Color.parseColor("#D0909C"),
            Color.parseColor("#E8B8D0"),
            Color.parseColor("#A8D4B4"),
            Color.parseColor("#B0BCC4"),
        )

        fun randomMusicWaveColors(): IntArray {
            val base = MUSIC_WAVE_PALETTE.random()
            val light = Color.argb(
                255,
                (Color.red(base) + 255) / 2,
                (Color.green(base) + 255) / 2,
                (Color.blue(base) + 255) / 2,
            )
            return intArrayOf(base, light)
        }
    }

    enum class Burst {
        NONE, HAPPY, RAIN, BULB, LIKE, WINK, SHY, BIXIN, KICK, ANGRY, DIZZY, FOOD
    }

    private val overlayMode = windowManager != null && roomHost == null
    private val handler = Handler(Looper.getMainLooper())
    private var layer: FxCanvas? = null
    private var wmLp: WindowManager.LayoutParams? = null
    private var roomLp: FrameLayout.LayoutParams? = null

    private var burst = Burst.NONE
    private var burstUntil = 0L
    private var musicOn = false
    private var musicWaveColors: IntArray = MUSIC_COLORS.copyOf()
    private var sleepZzzOn = false
    private var wearFlowerOn = false
    private var outfitDecors: List<OutfitStore.Decor> = emptyList()
    private var phase = 0
    private var tick: Runnable? = null

    private fun hasPersistentFx(): Boolean =
        musicOn || sleepZzzOn || wearFlowerOn || outfitDecors.isNotEmpty()

    // burst layout caches
    private val flowerPts = mutableListOf<Pair<Float, Float>>()
    private val flowerCols = mutableListOf<Int>()
    private val starPts = mutableListOf<Pair<Float, Float>>()
    private val heartPts = mutableListOf<Pair<Float, Float>>()
    private val rainDrops = mutableListOf<FloatArray>() // x,y,vy
    private val bixinParts = mutableListOf<FloatArray>() // x,y,vx,vy,life,size

    fun destroy() {
        stopTick()
        detach()
    }

    fun setVisible(visible: Boolean) {
        layer?.visibility = if (visible) View.VISIBLE else View.GONE
    }

    fun clearBurst() {
        burst = Burst.NONE
        burstUntil = 0L
        clearBurstParticles()
        invalidate()
        if (!hasPersistentFx()) {
            stopTick()
            detach()
        }
    }

    /** 清散点/雨/比心等，避免换特效或结束后残留。 */
    private fun clearBurstParticles() {
        flowerPts.clear()
        flowerCols.clear()
        starPts.clear()
        heartPts.clear()
        rainDrops.clear()
        bixinParts.clear()
    }

    fun clearAll() {
        musicOn = false
        sleepZzzOn = false
        wearFlowerOn = false
        outfitDecors = emptyList()
        clearBurst()
        stopTick()
        detach()
    }

    fun showHappy() = startBurst(Burst.HAPPY, HAPPY_HOLD_MS) {
        flowerPts.clear(); flowerCols.clear()
        val size = canvasSize()
        val cols = intArrayOf(
            Color.parseColor("#FF88CC"), Color.parseColor("#FFCC44"),
            Color.parseColor("#88DD88"), Color.parseColor("#FF6688"),
            Color.parseColor("#CC88FF"), Color.parseColor("#88CCFF"),
        )
        repeat(10) {
            flowerPts += scatterOnRing(size)
            flowerCols += cols.random()
        }
    }

    fun showRain(holdMs: Long = SAD_HOLD_MS) = startBurst(Burst.RAIN, holdMs) {
        rainDrops.clear()
        val size = canvasSize()
        repeat(14) {
            rainDrops += floatArrayOf(
                Random.nextFloat() * size,
                Random.nextFloat() * size * 0.35f,
                6f + Random.nextFloat() * 8f,
            )
        }
    }

    fun showBulb(holdMs: Long = IDEA_HOLD_MS) = startBurst(Burst.BULB, holdMs)

    fun showAngry(holdMs: Long = 4600L) = startBurst(Burst.ANGRY, holdMs)

    fun showLike() = startBurst(Burst.LIKE, LIKE_HOLD_MS) {
        starPts.clear()
        val size = canvasSize()
        repeat(18) { starPts += scatterOnRing(size) }
        repeat(6) { starPts += scatterOnRing(size) }
    }

    fun showWink() = startBurst(Burst.WINK, WINK_HOLD_MS)

    fun showShy(holdMs: Long = SHY_HOLD_MS) = startBurst(Burst.SHY, holdMs) {
        heartPts.clear()
        val size = canvasSize()
        repeat(8) { heartPts += scatterOnRing(size) }
    }

    fun showBixin(holdMs: Long = BIXIN_HOLD_MS) = startBurst(Burst.BIXIN, holdMs, inFront = true) {
        bixinParts.clear()
        val size = canvasSize()
        val cx = size / 2f
        val cy = size * 0.55f
        repeat(16) {
            val ang = Random.nextFloat() * Math.PI.toFloat() * 2f
            val sp = 1.5f + Random.nextFloat() * 3.5f
            bixinParts += floatArrayOf(
                cx, cy,
                cos(ang) * sp, sin(ang) * sp - 1.2f,
                1f, 2f + Random.nextFloat() * 2f,
            )
        }
    }

    fun showKick(holdMs: Long = KICK_HOLD_MS) = startBurst(Burst.KICK, holdMs)

    fun showDizzy() = startBurst(Burst.DIZZY, DIZZY_HOLD_MS)

    private var foodBurstId: String = "apple"

    fun showFood(foodId: String = "apple") {
        foodBurstId = foodId.ifBlank { "apple" }
        startBurst(Burst.FOOD, FOOD_HOLD_MS)
    }

    fun setMusicWave(on: Boolean, colors: IntArray? = null) {
        musicOn = on
        if (on) {
            musicWaveColors = when {
                colors != null && colors.size >= 2 -> colors.copyOf(2)
                else -> randomMusicWaveColors()
            }
            ensureLayer(inFront = false)
            startTick()
            place()
            // 刚开启时新建层容易盖住立绘：立刻压后，再延迟一次（避开并发 raise）
            restackBehindPet()
            handler.post { restackBehindPet() }
            handler.postDelayed({ restackBehindPet() }, 80L)
        } else if (!hasPersistentFx() && burst == Burst.NONE) {
            stopTick(); detach()
        }
        invalidate()
    }

    /** 强制把特效压到立绘下层（同窗 addView(0) / 异窗则先贴特效再抬宠）。 */
    fun restackBehindPet() {
        val v = layer ?: return
        if (overlayMode) {
            val lp = wmLp ?: return
            try {
                windowManager?.removeView(v)
                windowManager?.addView(v, lp)
            } catch (_: Exception) {
            }
            raisePet?.invoke()
        } else {
            val host = roomHost ?: return
            val lp = roomLp ?: return
            try {
                host.removeView(v)
                host.addView(v, 0, lp)
            } catch (_: Exception) {
            }
            raisePet?.invoke()
        }
    }

    fun setSleepZzz(on: Boolean) {
        if (sleepZzzOn == on) {
            if (on) invalidate()
            return
        }
        sleepZzzOn = on
        if (on) {
            val created = layer == null
            ensureLayer(inFront = false)
            startTick()
            place()
            // 仅新建特效层时抬宠；偷看结束再 raise 会卸挂悬浮窗导致闪白
            if (created) raisePet?.invoke()
        } else if (!hasPersistentFx() && burst == Burst.NONE) {
            // 偷看只是暂时关 ZZZ：保留层，避免马上 detach 再创建时闪
            invalidate()
        } else {
            invalidate()
        }
    }

    /** 彻底关掉睡眠 ZZZ 并拆层（退出睡眠模式时用）。 */
    fun clearSleepZzz() {
        sleepZzzOn = false
        invalidate()
        if (!hasPersistentFx() && burst == Burst.NONE) {
            stopTick()
            detach()
        }
    }

    /** 头顶戴花（对照 pet.py `_sync_head_flower`）。 */
    fun setWearFlower(on: Boolean) {
        wearFlowerOn = on
        if (on) {
            ensureLayer(inFront = true)
            startTick()
            place()
            raisePet?.invoke()
        } else if (!hasPersistentFx() && burst == Burst.NONE) {
            stopTick(); detach()
        }
        invalidate()
    }

    /** 装扮叠层：任意动作/模式都画在宠上。 */
    fun syncOutfit(list: List<OutfitStore.Decor>) {
        outfitDecors = list
        if (list.isNotEmpty()) {
            ensureLayer(inFront = true)
            startTick()
            place()
            raisePet?.invoke()
        } else if (!hasPersistentFx() && burst == Burst.NONE) {
            stopTick(); detach()
        }
        invalidate()
    }

    fun syncPlace() {
        if (layer != null) place()
    }

    /** 把特效层抬到当前悬浮栈顶（用于统一重排图层）。 */
    fun raiseLayer() {
        val v = layer ?: return
        if (overlayMode) {
            val lp = wmLp ?: return
            try {
                windowManager?.removeView(v)
                windowManager?.addView(v, lp)
            } catch (_: Exception) {
            }
        } else {
            v.bringToFront()
        }
    }

    private fun startBurst(kind: Burst, holdMs: Long, inFront: Boolean = false, setup: (() -> Unit)? = null) {
        // 先清旧 burst，避免雨/花/星叠在下一特效上
        clearBurstParticles()
        burst = kind
        burstUntil = SystemClock.elapsedRealtime() + holdMs
        phase = 0
        setup?.invoke()
        ensureLayer(inFront = inFront)
        startTick()
        place()
        if (!inFront) raisePet?.invoke()
        invalidate()
    }

    private fun topPad(): Int = if (burst == Burst.BULB) PAD + BULB_TOP_EXTRA else PAD

    private fun layerW(): Int = petSize() + PAD * 2

    private fun layerH(): Int = petSize() + topPad() + PAD

    /** 散射/雨点等仍按宽度取参考尺寸 */
    private fun canvasSize(): Int = layerW()

    private fun scatterOnRing(size: Int): Pair<Float, Float> {
        val ang = Random.nextFloat() * (Math.PI * 2).toFloat()
        val rad = size * (0.34f + Random.nextFloat() * 0.14f)
        val mid = size * 0.5f
        return mid + cos(ang) * rad to mid + sin(ang) * rad
    }

    private fun ensureLayer(inFront: Boolean) {
        if (layer != null) {
            // 比心需要前置：必要时重建
            if (inFront && overlayMode) {
                // overlay 比心：抬到 pet 之上 —— 重新 add 到最顶
                try {
                    windowManager?.removeView(layer)
                    windowManager?.addView(layer, wmLp)
                } catch (_: Exception) {
                }
            }
            return
        }
        val v = FxCanvas(context)
        layer = v
        val w = layerW()
        val h = layerH()
        if (overlayMode) {
            wmLp = WindowManager.LayoutParams(
                w, h,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT,
            ).apply { gravity = Gravity.TOP or Gravity.START }
            windowManager?.addView(v, wmLp)
        } else {
            roomLp = FrameLayout.LayoutParams(w, h)
            val host = roomHost ?: return
            if (inFront) host.addView(v, roomLp)
            else host.addView(v, 0, roomLp)
        }
    }

    private fun detach() {
        val v = layer ?: return
        try {
            if (overlayMode) windowManager?.removeView(v)
            else roomHost?.removeView(v)
        } catch (_: Exception) {
        }
        layer = null
        wmLp = null
        roomLp = null
    }

    private fun place() {
        val v = layer ?: return
        val w = layerW()
        val h = layerH()
        val pet = petTopLeft()
        val x = pet.x - PAD
        val y = pet.y - topPad()
        if (overlayMode) {
            val lp = wmLp ?: return
            lp.width = w
            lp.height = h
            lp.x = x
            lp.y = y
            try {
                windowManager?.updateViewLayout(v, lp)
            } catch (_: Exception) {
            }
        } else {
            val lp = (v.layoutParams as? FrameLayout.LayoutParams) ?: return
            lp.width = w
            lp.height = h
            lp.leftMargin = x
            lp.topMargin = y
            lp.gravity = Gravity.TOP or Gravity.START
            v.layoutParams = lp
        }
    }

    private fun startTick() {
        if (tick != null) return
        tick = object : Runnable {
            override fun run() {
                val now = SystemClock.elapsedRealtime()
                if (burst != Burst.NONE && now >= burstUntil) {
                    burst = Burst.NONE
                    clearBurstParticles()
                }
                phase++
                // animate rain / bixin
                when (burst) {
                    Burst.RAIN -> {
                        val size = canvasSize().toFloat()
                        for (d in rainDrops) {
                            d[1] += d[2]
                            if (d[1] > size * 0.55f) {
                                d[0] = Random.nextFloat() * size
                                d[1] = Random.nextFloat() * size * 0.2f
                            }
                        }
                    }
                    Burst.BIXIN -> {
                        val it = bixinParts.iterator()
                        while (it.hasNext()) {
                            val p = it.next()
                            p[0] += p[2]
                            p[1] += p[3]
                            p[4] -= 0.02f
                            p[5] += 0.08f
                            if (p[4] <= 0f) it.remove()
                        }
                        if (bixinParts.size < 8 && now < burstUntil) {
                            val size = canvasSize()
                            val cx = size / 2f
                            val cy = size * 0.55f
                            val ang = Random.nextFloat() * Math.PI.toFloat() * 2f
                            val sp = 1.5f + Random.nextFloat() * 3f
                            bixinParts += floatArrayOf(
                                cx, cy, cos(ang) * sp, sin(ang) * sp - 1.2f, 1f, 2f,
                            )
                        }
                    }
                    else -> Unit
                }
                place()
                invalidate()
                val alive = hasPersistentFx() || burst != Burst.NONE
                if (!alive) {
                    stopTick()
                    detach()
                    return
                }
                val delay = when {
                    burst == Burst.BIXIN -> BIXIN_MS
                    burst == Burst.RAIN -> RAIN_MS
                    burst == Burst.WINK || burst == Burst.KICK || burst == Burst.ANGRY ->
                        if (burst == Burst.WINK) WINK_MS else KICK_MS
                    burst == Burst.BULB -> BULB_MS
                    sleepZzzOn && !musicOn -> SLEEP_ZZZ_MS
                    else -> MUSIC_WAVE_MS
                }
                handler.postDelayed(this, delay)
            }
        }
        handler.post(tick!!)
    }

    private fun stopTick() {
        tick?.let { handler.removeCallbacks(it) }
        tick = null
    }

    private fun invalidate() {
        layer?.invalidate()
    }

    private inner class FxCanvas(ctx: Context) : View(ctx) {
        private val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.FILL }

        override fun onDraw(canvas: Canvas) {
            val size = width.coerceAtLeast(1)
            if (musicOn) drawMusicWave(canvas, size)
            if (sleepZzzOn) drawSleepZzz(canvas, size)
            if (wearFlowerOn) drawHeadFlower(canvas, size)
            if (outfitDecors.isNotEmpty()) {
                val pet = petSize().toFloat()
                OutfitStore.drawOnPet(canvas, context, PAD.toFloat(), PAD.toFloat(), pet, outfitDecors)
            }
            when (burst) {
                Burst.HAPPY -> drawHappy(canvas)
                Burst.RAIN -> drawRain(canvas)
                Burst.BULB -> drawBulb(canvas, size)
                Burst.LIKE -> drawLike(canvas)
                Burst.WINK -> drawWink(canvas, size)
                Burst.SHY -> drawShy(canvas)
                Burst.BIXIN -> drawBixin(canvas)
                Burst.KICK -> drawKick(canvas, size)
                Burst.ANGRY -> drawAngry(canvas, size)
                Burst.DIZZY -> drawDizzy(canvas, size)
                Burst.FOOD -> drawFood(canvas, size)
                Burst.NONE -> Unit
            }
        }

        private fun px(size: Int, div: Int) = max(2, size / div)

        private fun rect(c: Canvas, x: Float, y: Float, w: Float, h: Float, color: Int) {
            paint.color = color
            c.drawRect(x, y, x + w, y + h, paint)
        }

        private fun drawFlower(c: Canvas, x: Float, y: Float, color: Int, p: Int) {
            val pf = p.toFloat()
            rect(c, x, y, pf, pf, color)
            rect(c, x - pf, y + pf, pf, pf, color)
            rect(c, x + pf, y + pf, pf, pf, color)
            rect(c, x, y + pf * 2, pf, pf, color)
            rect(c, x + pf / 2, y + pf, pf, pf, Color.parseColor("#FFEE88"))
        }

        private fun drawHeadFlower(c: Canvas, size: Int) {
            val pet = petSize().toFloat()
            val cx = PAD + pet / 2f
            val cy = PAD + pet * 0.12f
            val p = max(2, (pet / 10f).toInt())
            drawFlower(c, cx - p / 2f, cy - p * 2f, Color.parseColor("#FF7799"), p)
            paint.color = Color.parseColor("#44AA55")
            c.drawRect(cx - 1f, cy + p, cx + 1f, cy + p * 3f, paint)
        }

        private fun drawStar(c: Canvas, x: Float, y: Float, p: Int, color: Int) {
            val pf = p.toFloat()
            rect(c, x + pf, y, pf, pf, color)
            rect(c, x, y + pf, pf * 3, pf, color)
            rect(c, x + pf, y + pf * 2, pf, pf, color)
        }

        private fun drawHeart(c: Canvas, x: Float, y: Float, p: Int, color: Int) {
            val pf = p.toFloat()
            rect(c, x, y, pf, pf, color)
            rect(c, x + pf * 2, y, pf, pf, color)
            rect(c, x, y + pf, pf * 3, pf, color)
            rect(c, x + pf, y + pf * 2, pf, pf, color)
        }

        private fun drawZ(c: Canvas, x: Float, y: Float, s: Int, color: Int) {
            val sf = s.toFloat()
            rect(c, x, y, sf * 2, sf, color)
            rect(c, x + sf, y + sf, sf, sf, color)
            rect(c, x, y + sf * 2, sf * 2, sf, color)
        }

        private fun drawPixelRing(c: Canvas, cx: Float, cy: Float, r: Int, p: Int, color: Int) {
            paint.color = color
            paint.style = Paint.Style.STROKE
            paint.strokeWidth = p.toFloat()
            c.drawCircle(cx, cy, r.toFloat(), paint)
            paint.style = Paint.Style.FILL
        }

        private fun drawHappy(c: Canvas) {
            val p = px(width, 36)
            for (i in flowerPts.indices) {
                val (x, y) = flowerPts[i]
                drawFlower(c, x, y, flowerCols.getOrElse(i) { Color.MAGENTA }, p)
            }
        }

        private fun drawRain(c: Canvas) {
            paint.color = Color.parseColor("#6699FF")
            for (d in rainDrops) {
                c.drawRect(d[0], d[1], d[0] + 3f, d[1] + 10f, paint)
            }
            // small cloud top
            val p = px(width, 28)
            rect(c, width * 0.28f, p.toFloat(), p * 5f, p * 2f, Color.parseColor("#667788"))
        }

        private fun drawBulb(c: Canvas, size: Int) {
            val glow = 0.7f + 0.3f * (0.5f + 0.5f * sin(phase * 0.25f)).toFloat()
            val p = max(3, petSize() / 28)
            val x = size / 2f - p * 2
            // 立绘顶在 canvas 的 topPad；灯泡整颗放在头顶上方空隙里
            val petTop = topPad().toFloat()
            val bulbH = p * 5f
            val y = (petTop - 12f - bulbH).coerceAtLeast(2f)
            val bulb = Color.argb((255 * glow).toInt().coerceIn(120, 255), 255, 238, 136)
            rect(c, x + p, y, p * 2f, p.toFloat(), bulb)
            rect(c, x, y + p, p * 4f, p * 2f, bulb)
            rect(c, x + p, y + p * 3, p * 2f, p.toFloat(), Color.parseColor("#CCCCCC"))
            rect(c, x + p * 1.5f, y + p * 4, p.toFloat(), p.toFloat(), Color.parseColor("#888888"))
        }

        private fun drawLike(c: Canvas) {
            val p = px(width, 40)
            for ((x, y) in starPts) drawStar(c, x, y, p, Color.parseColor("#FFFF88"))
        }

        private fun drawWink(c: Canvas, size: Int) {
            val cx = size / 2f
            val cy = size / 2f
            val p = px(size, 22)
            for (ring in 0 until 3) {
                val glow = 0.35f + 0.65f * (0.5f + 0.5f * sin(phase * 0.18f + ring)).toFloat()
                val r = (size * (0.38f + ring * 0.07f) * (0.85f + 0.2f * glow)).toInt()
                val col = intArrayOf(
                    Color.parseColor("#FFFF88"),
                    Color.parseColor("#FFCC66"),
                    Color.parseColor("#FFAA88"),
                )[ring]
                drawPixelRing(c, cx, cy, r, p, col)
            }
            val hp = px(size, 28)
            for (i in 0 until 3) {
                val spread = ((phase * 2 + i * 18) % (size / 2)).toFloat()
                val col = intArrayOf(
                    Color.parseColor("#FF6688"),
                    Color.parseColor("#FF88AA"),
                    Color.parseColor("#FF4466"),
                )[i]
                drawHeart(c, cx - hp * 2 - spread, size / 3f - spread / 3f, hp, col)
                drawHeart(c, cx + spread, size / 3f - spread / 3f, hp, col)
            }
        }

        private fun drawShy(c: Canvas) {
            val p = px(width, 36)
            for ((x, y) in heartPts) drawHeart(c, x, y, p, Color.parseColor("#FF6688"))
        }

        private fun drawBixin(c: Canvas) {
            for (p in bixinParts) {
                val alpha = (p[4] * 255).toInt().coerceIn(0, 255)
                val col = Color.argb(alpha, 255, 102, 136)
                drawHeart(c, p[0], p[1], p[5].toInt().coerceAtLeast(2), col)
            }
        }

        private fun drawKick(c: Canvas, size: Int) {
            val p = px(size, 24)
            val mid = size * 0.5f
            val inner = size * 0.36f
            val outer = size * 0.48f
            for (i in 0 until 10) {
                val ang = (phase * 0.42f + i * (Math.PI * 2 / 10)).toFloat()
                val dist = inner + (outer - inner) * (0.35f + 0.65f * ((phase + i * 3) % 5) / 4f)
                val cx = mid + cos(ang) * dist
                val cy = mid + sin(ang) * dist
                val col = if (i % 2 == 0) Color.parseColor("#FFEE44") else Color.parseColor("#FF8844")
                rect(c, cx, cy, p * 2f, p * 2f, col)
            }
            paint.color = Color.parseColor("#FFFF88")
            paint.strokeWidth = 3f
            paint.style = Paint.Style.STROKE
            c.drawLine(size * 0.18f, size * 0.72f, size * 0.82f, size * 0.72f - p, paint)
            paint.style = Paint.Style.FILL
        }

        private fun drawAngry(c: Canvas, size: Int) {
            drawKick(c, size) // reuse ring with angry colors override below
            val p = px(size, 24)
            val cx = size * 0.78f
            val cy = size * 0.22f
            rect(c, cx - p * 2, cy - p / 2f, p * 4f, p.toFloat(), Color.parseColor("#FF3333"))
            rect(c, cx - p / 2f, cy - p * 2, p.toFloat(), p * 4f, Color.parseColor("#FF3333"))
        }

        private fun drawDizzy(c: Canvas, size: Int) {
            val cx = size * 0.72f
            val cy = size * 0.22f
            val p = px(size, 28)
            for (i in 0 until 4) {
                val ang = phase * 0.4f + i * (Math.PI / 2).toFloat()
                val r = p * 3f
                drawStar(
                    c,
                    cx + cos(ang) * r,
                    cy + sin(ang) * r,
                    p,
                    Color.parseColor("#FFFF88"),
                )
            }
        }

        private fun drawFood(c: Canvas, size: Int) {
            val side = max(28, size / 3)
            val bmp = FoodPixelArt.bitmapFor(foodBurstId, side)
            val x = size * 0.62f
            val y = size * 0.38f
            c.drawBitmap(bmp, x, y, null)
        }

        private fun drawMusicWave(c: Canvas, size: Int) {
            val cx = size / 2f
            val cy = size / 2f
            val half = size / 2
            val p = max(4, size / 18)
            val maxR = max(8, half - p - 1)
            val base = musicWaveColors.getOrElse(0) { MUSIC_COLORS[0] }
            val light = musicWaveColors.getOrElse(1) { MUSIC_COLORS[1] }
            for (ring in 0 until 4) {
                val wave = 0.5f + 0.5f * sin(phase * 0.22f + ring * 0.85f).toFloat()
                val frac = 0.48f + ring * 0.16f
                val pulse = 0.50f + 0.50f * wave
                val r = (maxR * frac * pulse).toInt().coerceIn(4, maxR)
                drawPixelRing(c, cx, cy, r, p, if (ring % 2 == 0) base else light)
            }
            val bars = 7
            val barW = max(p, size / (bars * 3))
            val gap = barW
            val total = bars * barW + (bars - 1) * gap
            val x0 = (size - total) / 2
            for (i in 0 until bars) {
                val x = x0 + i * (barW + gap)
                val wave = (sin(phase * 0.35f + i * 0.8f) * 0.5f + 0.5f).toFloat()
                val h = (wave * (size / 10) + p).toInt()
                rect(
                    c, x.toFloat(), (size - h - 2).toFloat(),
                    barW.toFloat(), h.toFloat(),
                    if (i % 2 == 0) base else light,
                )
            }
        }

        private fun drawSleepZzz(c: Canvas, size: Int) {
            val p = max(3, (size - PAD * 2) / 28)
            val offset = (phase % 3) * max(3, p / 2)
            val colors = intArrayOf(
                Color.parseColor("#AABBFF"),
                Color.parseColor("#8899EE"),
                Color.parseColor("#6677DD"),
            )
            drawZ(c, (size - p * 9).toFloat(), (p * 2 + offset).toFloat(), p, colors[0])
            drawZ(c, (size - p * 13).toFloat(), (p * 5 + offset).toFloat(), max(2, p - 1), colors[1])
            drawZ(c, (size - p * 17).toFloat(), (p * 8 + offset).toFloat(), max(2, p - 1), colors[2])
        }
    }
}
