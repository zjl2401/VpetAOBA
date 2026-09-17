package com.vpet.mobile

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Matrix
import android.graphics.PixelFormat
import android.graphics.Point
import android.graphics.Rect
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.view.Gravity
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.ImageView
import kotlin.math.abs
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.roundToInt

/**
 * 智能伴侣「莲」：对照桌面 minipet / Allmate。
 * 侧向脚底跟随；抠内容盒后高度约为主宠一半，整只缩进画布以免侧面被裁。
 */
class CompanionFollower(
    private val context: Context,
    private val windowManager: WindowManager? = null,
    private val roomHost: FrameLayout? = null,
    private val petTopLeft: () -> Point,
    private val petSize: () -> Int,
    private val screenSize: () -> Point,
    private val mainDir: () -> SpriteAssets.Dir = { SpriteAssets.Dir.FRONT },
    private val mainMoving: () -> Boolean = { false },
) {
    companion object {
        const val FOLLOW_MS = 45L
        const val FOLLOW_STEP = 3
        const val SIDE_GAP = 6
        const val TURN_HOLD_MS = 380L
        const val TURN_AXIS_RATIO = 1.4f
        const val WALK_FRAME_MS = 210L
        /** 相对主宠画布再略收一档，给侧面留边。 */
        private const val FIT_PAD = 0.92f

        /** 伴侣画布高度 ≈ 主宠高度的一半。 */
        fun companionSize(petPx: Int): Int =
            (petPx / 2).coerceIn(48, 220)
    }

    private var view: ImageView? = null
    private var x = 0f
    private var y = 0f
    private var side = "left"
    private var moveDir = SpriteAssets.Dir.FRONT
    private var moveDirMs = 0L
    private var frameToggle = false
    private var lastFrameAt = 0L
    private var lastPetX = 0
    private var lastPetY = 0
    private val handler = Handler(Looper.getMainLooper())
    private var tick: Runnable? = null
    /** 工作导航：非空时侧向跟随该锚点（旗脚附近），否则跟主宠。 */
    var workAnchor: (() -> Point?)? = null
    var active = false
        private set
    private val overlayMode = windowManager != null && roomHost == null

    private var bmpStand: Bitmap? = null
    private var bmpFront1: Bitmap? = null
    private var bmpFront2: Bitmap? = null
    private var bmpBack1: Bitmap? = null
    private var bmpBack2: Bitmap? = null
    private var bmpLeft1: Bitmap? = null
    private var bmpLeft2: Bitmap? = null
    private var bmpRight1: Bitmap? = null
    private var bmpRight2: Bitmap? = null

    fun start() {
        if (active) return
        active = true
        val size = companionSize(petSize())
        loadSprites(size)
        ensureView(size)
        val p = petTopLeft()
        val pet = petSize()
        lastPetX = p.x
        lastPetY = p.y
        val (tx, ty) = sideTarget(p, pet, size)
        x = tx
        y = ty
        moveDir = SpriteAssets.Dir.FRONT
        frameToggle = false
        applySprite(standing = true)
        place()
        schedule()
    }

    fun stop() {
        active = false
        tick?.let { handler.removeCallbacks(it) }
        tick = null
        view?.let { v ->
            try {
                if (overlayMode) windowManager?.removeView(v)
                else roomHost?.removeView(v)
            } catch (_: Exception) {
            }
        }
        view = null
        recycleBitmaps()
    }

    /** 主宠改大小后刷新伴侣尺寸与立绘（不跟金目人格）。 */
    fun refreshSprite() {
        if (!active) return
        val size = companionSize(petSize())
        loadSprites(size)
        view?.let { v ->
            if (overlayMode) {
                val lp = v.layoutParams as? WindowManager.LayoutParams ?: return
                lp.width = size
                lp.height = size
                try {
                    windowManager?.updateViewLayout(v, lp)
                } catch (_: Exception) {
                }
            } else {
                val lp = v.layoutParams as? FrameLayout.LayoutParams ?: return
                lp.width = size
                lp.height = size
                v.layoutParams = lp
            }
        }
        applySprite(standing = !isWalkingVisual())
        place()
    }

    private fun recycleBitmaps() {
        listOf(
            bmpStand, bmpFront1, bmpFront2, bmpBack1, bmpBack2,
            bmpLeft1, bmpLeft2, bmpRight1, bmpRight2,
        ).forEach { it?.recycle() }
        bmpStand = null
        bmpFront1 = null
        bmpFront2 = null
        bmpBack1 = null
        bmpBack2 = null
        bmpLeft1 = null
        bmpLeft2 = null
        bmpRight1 = null
        bmpRight2 = null
    }

    private fun loadSprites(size: Int) {
        recycleBitmaps()
        bmpStand = loadMini("minipet/petstand.png", size)
        bmpFront1 = loadMini("minipet/petfront1.png", size)
        bmpFront2 = loadMini("minipet/petfront2.png", size)
        bmpBack1 = loadMini("minipet/petback1.png", size)
        bmpBack2 = loadMini("minipet/petback2.png", size)
        bmpLeft1 = loadMini("minipet/petleft1.png", size)
        bmpLeft2 = loadMini("minipet/petleft2.png", size)
        bmpRight1 = bmpLeft1?.let { flipH(it) }
        bmpRight2 = bmpLeft2?.let { flipH(it) }
    }

    private fun loadMini(path: String, canvasSize: Int): Bitmap? {
        val raw = decodeAsset(path) ?: return null
        return packHeightMatched(raw, canvasSize).also { packed ->
            if (packed !== raw) raw.recycle()
        }
    }

    private fun decodeAsset(path: String): Bitmap? = try {
        context.assets.open(path).use { BitmapFactory.decodeStream(it) }
    } catch (_: Exception) {
        null
    }

    /**
     * 抠不透明内容盒后，整图装入画布（高度目标约画布高，过宽则再缩小），
     * 水平居中、底对齐，保证侧面帧不被裁切。
     */
    private fun packHeightMatched(src: Bitmap, canvasSize: Int): Bitmap {
        val box = opaqueBounds(src) ?: Rect(0, 0, src.width, src.height)
        val cropped = if (box.left == 0 && box.top == 0 &&
            box.width() == src.width && box.height() == src.height
        ) {
            src
        } else {
            Bitmap.createBitmap(src, box.left, box.top, box.width(), box.height())
        }
        val cw = cropped.width.coerceAtLeast(1)
        val ch = cropped.height.coerceAtLeast(1)
        val maxSide = (canvasSize * FIT_PAD).coerceAtLeast(1f)
        // 先按高度对准画布，若侧面过宽再整体缩小以完整显示
        var scale = maxSide / ch
        if (cw * scale > maxSide) {
            scale = maxSide / cw
        }
        val newW = max(1, (cw * scale).roundToInt())
        val newH = max(1, (ch * scale).roundToInt())
        val scaled = if (newW == cropped.width && newH == cropped.height) {
            cropped
        } else {
            Bitmap.createScaledBitmap(cropped, newW, newH, false).also {
                if (it != cropped && cropped != src) cropped.recycle()
            }
        }
        val out = Bitmap.createBitmap(canvasSize, canvasSize, Bitmap.Config.ARGB_8888)
        val left = (canvasSize - newW) / 2f
        val top = (canvasSize - newH).toFloat() // 底对齐
        Canvas(out).drawBitmap(scaled, left, top, null)
        if (scaled != out && scaled != src) scaled.recycle()
        return out
    }

    private fun opaqueBounds(bmp: Bitmap): Rect? {
        val w = bmp.width
        val h = bmp.height
        var minX = w
        var minY = h
        var maxX = -1
        var maxY = -1
        val row = IntArray(w)
        for (y in 0 until h) {
            bmp.getPixels(row, 0, w, 0, y, w, 1)
            for (x in 0 until w) {
                if ((row[x] ushr 24) > 16) {
                    if (x < minX) minX = x
                    if (x > maxX) maxX = x
                    if (y < minY) minY = y
                    if (y > maxY) maxY = y
                }
            }
        }
        if (maxX < minX) return null
        return Rect(minX, minY, maxX + 1, maxY + 1)
    }

    private fun flipH(src: Bitmap): Bitmap {
        val m = Matrix().apply { preScale(-1f, 1f) }
        return Bitmap.createBitmap(src, 0, 0, src.width, src.height, m, true)
    }

    private fun ensureView(size: Int) {
        if (view != null) return
        val iv = ImageView(context).apply {
            scaleType = ImageView.ScaleType.FIT_XY
            setImageBitmap(bmpStand)
        }
        view = iv
        if (overlayMode) {
            val lp = WindowManager.LayoutParams(
                size, size,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT,
            ).apply { gravity = Gravity.TOP or Gravity.START }
            windowManager?.addView(iv, lp)
        } else {
            roomHost?.addView(iv, FrameLayout.LayoutParams(size, size))
        }
    }

    private fun sideTarget(petTl: Point, petPx: Int, mini: Int): Pair<Float, Float> {
        val gap = SIDE_GAP
        val leftX = (petTl.x - mini - gap).toFloat()
        val rightX = (petTl.x + petPx + gap).toFloat()
        // 伴侣更矮：底边对齐主宠脚底
        val targetY = (petTl.y + petPx - mini).toFloat()
        val sw = screenSize().x
        val leftOk = leftX >= 0 && leftX + mini <= sw
        val rightOk = rightX >= 0 && rightX + mini <= sw
        val targetX = if (side == "left") {
            if (leftOk || !rightOk) leftX else rightX.also { side = "right" }
        } else {
            if (rightOk || !leftOk) rightX else leftX.also { side = "left" }
        }
        return clamp(targetX, targetY, mini)
    }

    private fun clamp(cx: Float, cy: Float, size: Int): Pair<Float, Float> {
        val scr = screenSize()
        val mx = cx.coerceIn(0f, (scr.x - size).coerceAtLeast(0).toFloat())
        val my = cy.coerceIn(0f, (scr.y - size).coerceAtLeast(0).toFloat())
        return mx to my
    }

    private fun schedule() {
        tick?.let { handler.removeCallbacks(it) }
        tick = Runnable { step() }
        handler.postDelayed(tick!!, FOLLOW_MS)
    }

    private fun step() {
        if (!active) return
        val petTl = petTopLeft()
        val petPx = petSize()
        val mini = companionSize(petPx)
        val petMoved = abs(petTl.x - lastPetX) > 0 || abs(petTl.y - lastPetY) > 0
        lastPetX = petTl.x
        lastPetY = petTl.y
        val mainIsMoving = petMoved || mainMoving()

        val anchor = workAnchor?.invoke()
        val (tx, ty) = if (anchor != null) {
            sideTarget(Point(anchor.x - petPx / 2, anchor.y - petPx), petPx, mini)
        } else {
            sideTarget(petTl, petPx, mini)
        }
        val dx = tx - x
        val dy = ty - y
        val dist = hypot(dx.toDouble(), dy.toDouble()).toFloat()
        val step = FOLLOW_STEP.toFloat()

        var moving = false
        if (dist > 1.5f) {
            moving = true
            if (dist > step) {
                x += dx / dist * step
                y += dy / dist * step
            } else {
                x = tx
                y = ty
            }
            val proposed = moveDirFromDelta(dx, dy, moveDir)
            moveDir = applyMoveDir(proposed)
        } else if (mainIsMoving) {
            moveDir = applyMoveDir(mainDir())
        }

        val now = SystemClock.elapsedRealtime()
        if (moving || mainIsMoving) {
            if (now - lastFrameAt >= WALK_FRAME_MS) {
                frameToggle = !frameToggle
                lastFrameAt = now
            }
            applySprite(standing = false)
        } else {
            applySprite(standing = true)
        }
        place()
        schedule()
    }

    private fun moveDirFromDelta(dx: Float, dy: Float, current: SpriteAssets.Dir): SpriteAssets.Dir {
        val ax = abs(dx)
        val ay = abs(dy)
        if (ax < 0.35f && ay < 0.35f) return current
        val horiz = current == SpriteAssets.Dir.LEFT || current == SpriteAssets.Dir.RIGHT
        val ratio = TURN_AXIS_RATIO
        return if (horiz) {
            when {
                ay > ax * ratio -> if (dy > 0) SpriteAssets.Dir.FRONT else SpriteAssets.Dir.BACK
                ax < 0.35f -> current
                else -> if (dx < 0) SpriteAssets.Dir.LEFT else SpriteAssets.Dir.RIGHT
            }
        } else {
            when {
                ax > ay * ratio -> if (dx < 0) SpriteAssets.Dir.LEFT else SpriteAssets.Dir.RIGHT
                ay < 0.35f -> current
                else -> if (dy > 0) SpriteAssets.Dir.FRONT else SpriteAssets.Dir.BACK
            }
        }
    }

    private fun applyMoveDir(proposed: SpriteAssets.Dir): SpriteAssets.Dir {
        if (proposed == moveDir) return moveDir
        val now = SystemClock.elapsedRealtime()
        if (moveDirMs != 0L && now - moveDirMs < TURN_HOLD_MS) return moveDir
        moveDir = proposed
        moveDirMs = now
        return moveDir
    }

    private fun isWalkingVisual(): Boolean = false

    private fun applySprite(standing: Boolean) {
        val bmp = if (standing) {
            bmpStand
        } else {
            when (moveDir) {
                SpriteAssets.Dir.FRONT -> if (frameToggle) bmpFront2 else bmpFront1
                SpriteAssets.Dir.BACK -> if (frameToggle) bmpBack2 else bmpBack1
                SpriteAssets.Dir.LEFT -> if (frameToggle) bmpLeft2 else bmpLeft1
                SpriteAssets.Dir.RIGHT -> if (frameToggle) bmpRight2 else bmpRight1
            }
        } ?: bmpStand
        view?.setImageBitmap(bmp)
    }

    private fun place() {
        val v = view ?: return
        val size = companionSize(petSize())
        if (overlayMode) {
            val lp = v.layoutParams as? WindowManager.LayoutParams ?: return
            lp.x = x.toInt()
            lp.y = y.toInt()
            lp.width = size
            lp.height = size
            try {
                windowManager?.updateViewLayout(v, lp)
            } catch (_: Exception) {
            }
        } else {
            val lp = v.layoutParams as? FrameLayout.LayoutParams ?: return
            lp.leftMargin = x.toInt()
            lp.topMargin = y.toInt()
            lp.width = size
            lp.height = size
            lp.gravity = Gravity.TOP or Gravity.START
            v.layoutParams = lp
            v.requestLayout()
        }
    }
}
