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
import android.view.View
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.ImageView
import kotlin.math.abs
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.roundToInt

/**
 * 智能伴侣「莲」：对照桌面 minipet / Allmate。
 * 侧向脚底跟随、定步长、四向切帧；窗口随主宠三档缩放（中档约 120，对齐桌面 MINI_PET_SIZE）。
 * 立绘：抠内容盒后按 petstand 高度铺满缩放（正面与站立同高；侧面超宽裁切）。
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
        const val FOLLOW_MS = 55L
        const val FOLLOW_STEP = 2
        const val SIDE_GAP = 6
        const val TURN_HOLD_MS = 380L
        const val TURN_AXIS_RATIO = 1.4f
        const val WALK_FRAME_MS = 210L
        /** 对照桌面 MINI_PET_SIZE / DEFAULT_SIZE：伴侣随主宠同比例缩放。 */
        const val MINI_PET_SIZE = 120
        const val DEFAULT_PET_SIZE = 128

        fun companionSize(petPx: Int): Int {
            val px = petPx.coerceAtLeast(24)
            val scaled = (px.toFloat() * MINI_PET_SIZE / DEFAULT_PET_SIZE).roundToInt()
            // 与主宠同上下限比例，避免一边到顶另一边不动
            val lo = (PetPrefs.SIZE_MIN_PX.toFloat() * MINI_PET_SIZE / DEFAULT_PET_SIZE).roundToInt()
                .coerceAtLeast(72)
            val hi = (PetPrefs.SIZE_MAX_PX.toFloat() * MINI_PET_SIZE / DEFAULT_PET_SIZE).roundToInt()
                .coerceAtMost(PetPrefs.SIZE_MAX_PX)
            return scaled.coerceIn(lo, hi)
        }
    }

    private var view: ImageView? = null
    /** 悬浮窗根：包一层 FrameLayout，供像素溶解叠层（对照主宠 overlay root）。 */
    private var host: FrameLayout? = null
    private var x = 0f
    private var y = 0f
    private var side = "left"
    private var moveDir = SpriteAssets.Dir.FRONT
    private var moveDirMs = 0L
    private val turnGuard = WalkTurnGuard()
    private var frameToggle = false
    private var lastFrameAt = 0L
    private var lastPetX = 0
    private var lastPetY = 0
    private var loadedCanvasSize = -1
    /** 对照桌面 `_reference_scale`：由 petstand 内容盒算出，各向帧共用。 */
    private var refScale = 0f
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

    /** 连点抱起：由外部设置；参数为当前连点次数。 */
    var onMultiClick: ((clicks: Int) -> Unit)? = null
    private val clickTimes = ArrayList<Long>(4)

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
        moveDirMs = 0L
        turnGuard.reset()
        frameToggle = false
        applySprite(standing = true)
        place()
        schedule()
    }

    fun stop() {
        active = false
        tick?.let { handler.removeCallbacks(it) }
        tick = null
        try {
            if (overlayMode) {
                host?.let { windowManager?.removeView(it) }
            } else {
                view?.let { roomHost?.removeView(it) }
            }
        } catch (_: Exception) {
        }
        host = null
        view = null
        recycleBitmaps()
        loadedCanvasSize = -1
    }

    fun setVisible(visible: Boolean) {
        val v = if (overlayMode) host else view
        v?.visibility = if (visible) View.VISIBLE else View.GONE
    }

    fun displayTopLeft(): Point = Point(x.roundToInt(), y.roundToInt())

    fun displaySize(): Int = companionSize(petSize())

    /** 供伴侣背景特效挂到同一窗口内（保证声波在立绘后方）。 */
    fun fxHost(): FrameLayout? = if (overlayMode) host else null

    /** 采集等下层悬浮窗之后，把伴侣再抬到最前。 */
    fun raise() {
        if (overlayMode) {
            val h = host ?: return
            val lp = h.layoutParams as? WindowManager.LayoutParams ?: return
            try {
                windowManager?.removeView(h)
                windowManager?.addView(h, lp)
            } catch (_: Exception) {
            }
        } else {
            view?.bringToFront()
        }
    }

    /** 同窗内把立绘抬到特效之上。 */
    fun bringSpriteToFront() {
        view?.bringToFront()
    }

    /**
     * 与主宠同步的像素块溶解。reverse=false 入场；true 出场。
     * 动画期间暂停跟随，避免切帧干扰抓屏。
     */
    fun playDissolve(reverse: Boolean, totalMs: Long? = null, onDone: (() -> Unit)? = null) {
        val iv = view
        if (iv == null || !active) {
            onDone?.invoke()
            return
        }
        tick?.let { handler.removeCallbacks(it) }
        tick = null
        PixelDissolve.play(iv, reverse = reverse, totalMs = totalMs) {
            if (active && !reverse) schedule()
            onDone?.invoke()
        }
    }

    /**
     * 主宠改大小后同步伴侣窗口与立绘（对照桌面 `_resync_mini_pets_size`）。
     * @param forceReload 为 true 时即使像素档相同也重载贴图（设置滑条连调）。
     */
    fun refreshSprite(forceReload: Boolean = false) {
        if (!active) return
        val size = companionSize(petSize())
        if (forceReload || size != loadedCanvasSize) loadSprites(size)
        val pad = PetFxUi.PAD
        val outer = size + pad * 2
        if (overlayMode) {
            val h = host ?: return
            val lp = h.layoutParams as? WindowManager.LayoutParams ?: return
            lp.width = outer
            lp.height = outer
            try {
                windowManager?.updateViewLayout(h, lp)
            } catch (_: Exception) {
            }
            (view?.layoutParams as? FrameLayout.LayoutParams)?.let { vlp ->
                vlp.width = size
                vlp.height = size
                vlp.leftMargin = pad
                vlp.topMargin = pad
                view?.layoutParams = vlp
            }
        } else {
            view?.let { v ->
                val lp = v.layoutParams as? FrameLayout.LayoutParams ?: return
                lp.width = size
                lp.height = size
                v.layoutParams = lp
            }
        }
        val p = petTopLeft()
        val (tx, ty) = sideTarget(p, petSize(), size)
        x = tx
        y = ty
        applySprite(standing = true)
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
        loadedCanvasSize = size
        refScale = 0f
        // 先算 petstand 参考缩放，再加载各向（对照桌面 mini pet 共用 ref）
        bmpStand = loadMiniCanvas("minipet/petstand.png", size, isRef = true)
        bmpFront1 = loadMiniCanvas("minipet/petfront1.png", size)
        bmpFront2 = loadMiniCanvas("minipet/petfront2.png", size)
        bmpBack1 = loadMiniCanvas("minipet/petback1.png", size)
        bmpBack2 = loadMiniCanvas("minipet/petback2.png", size)
        bmpLeft1 = loadMiniCanvas("minipet/petleft1.png", size)
        bmpLeft2 = loadMiniCanvas("minipet/petleft2.png", size)
        bmpRight1 = bmpLeft1?.let { flipH(it) }
        bmpRight2 = bmpLeft2?.let { flipH(it) }
    }

    /**
     * 抠内容盒后按 petstand 的 reference_scale 缩放，底对齐贴入画布。
     * 对照桌面 `_to_fixed_canvas`：共用 ref、溢出只裁切，不再二次压扁（避免侧面变矮）。
     */
    private fun loadMiniCanvas(path: String, canvasSize: Int, isRef: Boolean = false): Bitmap? {
        val raw = decodeAsset(path) ?: return null
        val box = opaqueBounds(raw) ?: Rect(0, 0, raw.width, raw.height)
        val cropped = if (box.left == 0 && box.top == 0 && box.width() == raw.width && box.height() == raw.height) {
            raw
        } else {
            Bitmap.createBitmap(raw, box.left, box.top, box.width(), box.height()).also {
                if (it != raw) raw.recycle()
            }
        }
        val cw = cropped.width.coerceAtLeast(1)
        val ch = cropped.height.coerceAtLeast(1)
        if (isRef || refScale <= 0f) {
            // 以高度铺满为主，正面与站立同高；更宽的侧面横向裁切
            refScale = canvasSize.toFloat() / ch
        }
        val scale = refScale
        val newW = max(1, (cw * scale).roundToInt())
        val newH = max(1, (ch * scale).roundToInt())
        val scaled = if (newW == cropped.width && newH == cropped.height) {
            cropped
        } else {
            Bitmap.createScaledBitmap(cropped, newW, newH, false).also {
                if (it != cropped) cropped.recycle()
            }
        }
        val out = Bitmap.createBitmap(canvasSize, canvasSize, Bitmap.Config.ARGB_8888)
        // 底对齐；超宽/超高由 Canvas 裁切（对齐桌面 paste）
        Canvas(out).drawBitmap(scaled, (canvasSize - newW) / 2f, (canvasSize - newH).toFloat(), null)
        if (scaled != out) scaled.recycle()
        return out
    }

    private fun decodeAsset(path: String): Bitmap? = try {
        context.assets.open(path).use { BitmapFactory.decodeStream(it) }
    } catch (_: Exception) {
        null
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
        val pad = PetFxUi.PAD
        val outer = size + pad * 2
        val iv = ImageView(context).apply {
            // 已是 size×size 底对齐画布
            scaleType = ImageView.ScaleType.FIT_XY
            setImageBitmap(bmpStand)
        }
        view = iv
        if (overlayMode) {
            val container = FrameLayout(context)
            container.addView(
                iv,
                FrameLayout.LayoutParams(size, size).apply {
                    leftMargin = pad
                    topMargin = pad
                    gravity = Gravity.TOP or Gravity.START
                },
            )
            host = container
            val lp = WindowManager.LayoutParams(
                outer, outer,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT,
            ).apply { gravity = Gravity.TOP or Gravity.START }
            windowManager?.addView(container, lp)
            container.isClickable = true
            container.setOnClickListener { noteCompanionClick() }
        } else {
            roomHost?.addView(iv, FrameLayout.LayoutParams(size, size))
            iv.isClickable = true
            iv.setOnClickListener { noteCompanionClick() }
        }
    }

    private fun noteCompanionClick() {
        val now = android.os.SystemClock.elapsedRealtime()
        clickTimes.removeAll { now - it > 1400L }
        clickTimes.add(now)
        onMultiClick?.invoke(clickTimes.size)
        if (clickTimes.size >= 3) clickTimes.clear()
    }

    private fun sideTarget(petTl: Point, petPx: Int, mini: Int): Pair<Float, Float> {
        val gap = SIDE_GAP
        val leftX = (petTl.x - mini - gap).toFloat()
        val rightX = (petTl.x + petPx + gap).toFloat()
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
        val gated = turnGuard.resolve(proposed, moveDir)
        if (gated == moveDir) return moveDir
        val now = SystemClock.elapsedRealtime()
        if (moveDirMs != 0L && now - moveDirMs < TURN_HOLD_MS) return moveDir
        moveDir = gated
        moveDirMs = now
        return moveDir
    }

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
        val size = companionSize(petSize())
        val pad = PetFxUi.PAD
        val outer = size + pad * 2
        if (overlayMode) {
            val h = host ?: return
            val lp = h.layoutParams as? WindowManager.LayoutParams ?: return
            // 窗口含 PAD：屏幕坐标对齐立绘左上角
            lp.x = x.toInt() - pad
            lp.y = y.toInt() - pad
            lp.width = outer
            lp.height = outer
            try {
                windowManager?.updateViewLayout(h, lp)
            } catch (_: Exception) {
            }
        } else {
            val v = view ?: return
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
