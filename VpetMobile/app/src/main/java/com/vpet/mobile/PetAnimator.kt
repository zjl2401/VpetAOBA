package com.vpet.mobile

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.util.TypedValue
import android.view.ViewGroup
import android.widget.ImageView

/**
 * 立绘动作机：常量对齐桌面 pet.py。
 * 走动：切帧 WALK_FRAME_MS=210 与移动 MOVE_INTERVAL_MS=55 分离；四向立绘。
 * 睡眠：安静固定 sleep2；peek 用 sleep1。
 */
class PetAnimator(
    private val context: Context,
    private val imageView: ImageView,
    private val onWalkMove: (() -> Unit)? = null,
) {
    enum class Mode {
        STAND, HI, SLEEP, SLEEP_PEEK, WALK, HAPPY,
        WORK_STAND, WORK_WALK,
        MUSIC_STAND, MUSIC_WALK,
        POSE,
    }

    companion object {
        const val WALK_FRAME_MS = 210L
        const val MOVE_INTERVAL_MS = 55L
        const val MUSIC_WALK_FRAME_MS = 280L
        const val MUSIC_MOVE_INTERVAL_MS = 105L
        const val ACTION_FRAME_MS = 180L
        const val MOVE_STEP = 2
        const val DRAG_YUQI_MS = 3000L
        const val POSE_HOLD_MS = 1600L
        const val REST_BOBBLE_PX = 3
        const val REST_BOBBLE_MS = 160L
    }

    private val handler = Handler(Looper.getMainLooper())
    private var frameRunnable: Runnable? = null
    private var moveRunnable: Runnable? = null
    private var bobbleRunnable: Runnable? = null
    private var mode = Mode.STAND
    private var frameToggle = false
    private var poseFrames: List<String> = emptyList()
    private var poseIndex = 0
    private var resumeAfterPose: Mode = Mode.STAND
    private var baseTranslationY = 0f
    var walkDir: SpriteAssets.Dir = SpriteAssets.Dir.RIGHT
        private set

    /** 兼容旧代码：+1 右 / -1 左 */
    @Deprecated("use walkDir")
    val legacyWalkSign: Int get() = if (walkDir == SpriteAssets.Dir.LEFT) -1 else 1

    fun currentMode(): Mode = mode

    fun petImage(): ImageView = imageView

    fun playDissolve(reverse: Boolean, totalMs: Long? = null, onDone: (() -> Unit)? = null) {
        PixelDissolve.play(imageView, reverse = reverse, totalMs = totalMs, onDone = onDone)
    }

    fun walkStepPx(): Int = MOVE_STEP

    fun walkDelta(): Pair<Int, Int> {
        val s = walkStepPx()
        return walkDir.dx * s to walkDir.dy * s
    }

    fun setWalkDir(dir: SpriteAssets.Dir) {
        if (walkDir == dir) return
        walkDir = dir
        if (mode == Mode.WALK || mode == Mode.WORK_WALK || mode == Mode.MUSIC_WALK) {
            applyFrame()
        }
    }

    fun reverseWalkDir() {
        walkDir = when (walkDir) {
            SpriteAssets.Dir.LEFT -> SpriteAssets.Dir.RIGHT
            SpriteAssets.Dir.RIGHT -> SpriteAssets.Dir.LEFT
            SpriteAssets.Dir.FRONT -> SpriteAssets.Dir.BACK
            SpriteAssets.Dir.BACK -> SpriteAssets.Dir.FRONT
        }
        applyFrame()
    }

    fun pickInboundDir(canGo: (SpriteAssets.Dir) -> Boolean): SpriteAssets.Dir? {
        val ok = SpriteAssets.Dir.entries.filter(canGo)
        if (ok.isEmpty()) return null
        val others = ok.filter { it != walkDir }
        return (others.ifEmpty { ok }).random()
    }

    fun applyDisplaySize() {
        val px = PetPrefs.sizePx(context)
        val lp = imageView.layoutParams ?: ViewGroup.LayoutParams(px, px)
        lp.width = px
        lp.height = px
        imageView.layoutParams = lp
        applyFrame()
    }

    fun setMode(m: Mode, driveMove: Boolean = true) {
        if (m != Mode.POSE) poseFrames = emptyList()
        val prev = mode
        mode = m
        frameToggle = false
        stopAnimLoops()
        if (prev == Mode.SLEEP || prev == Mode.SLEEP_PEEK) {
            stopBobble()
            imageView.translationY = baseTranslationY
        }
        applyFrame()
        when (m) {
            Mode.HI -> startFrameToggle(ACTION_FRAME_MS)
            Mode.SLEEP -> {
                baseTranslationY = imageView.translationY
                startBobble()
            }
            Mode.SLEEP_PEEK -> Unit
            Mode.WALK -> {
                startFrameToggle(WALK_FRAME_MS)
                if (driveMove) startMoveLoop(MOVE_INTERVAL_MS)
            }
            Mode.WORK_WALK -> {
                startFrameToggle(WALK_FRAME_MS)
            }
            Mode.MUSIC_WALK -> {
                startFrameToggle(MUSIC_WALK_FRAME_MS)
                if (driveMove) startMoveLoop(MUSIC_MOVE_INTERVAL_MS)
            }
            Mode.HAPPY -> {
                handler.postDelayed({
                    if (mode == Mode.HAPPY) setMode(Mode.STAND)
                }, 1200L)
            }
            Mode.STAND, Mode.WORK_STAND, Mode.MUSIC_STAND, Mode.POSE -> Unit
        }
    }

    fun playPose(frames: List<String>, holdMs: Long = POSE_HOLD_MS, resume: Mode = Mode.STAND) {
        if (frames.isEmpty()) return
        resumeAfterPose = resume
        poseFrames = frames
        poseIndex = 0
        mode = Mode.POSE
        stopAnimLoops()
        applyFrame()
        if (frames.size > 1) {
            frameRunnable = object : Runnable {
                override fun run() {
                    if (mode != Mode.POSE || poseFrames.isEmpty()) return
                    poseIndex = (poseIndex + 1) % poseFrames.size
                    applyFrame()
                    handler.postDelayed(this, ACTION_FRAME_MS)
                }
            }
            handler.postDelayed(frameRunnable!!, ACTION_FRAME_MS)
        }
        handler.postDelayed({
            if (mode == Mode.POSE) setMode(resumeAfterPose)
        }, holdMs)
    }

    fun stop() {
        stopAnimLoops()
        stopBobble()
    }

    fun applyFrame() {
        val side = PetPrefs.sizePx(context)
        when (mode) {
            Mode.STAND -> setBitmap(SpriteAssets.STAND, side)
            Mode.HI -> setBitmap(if (frameToggle) SpriteAssets.HI2 else SpriteAssets.HI1, side)
            Mode.SLEEP -> setBitmap(SpriteAssets.SLEEP2, side)
            Mode.SLEEP_PEEK -> setBitmap(SpriteAssets.SLEEP1, side)
            Mode.HAPPY -> setBitmap(SpriteAssets.HAPPY, side)
            Mode.WORK_STAND -> setBitmap(SpriteAssets.WORK_STAND, side)
            Mode.MUSIC_STAND -> setBitmap(SpriteAssets.MUSIC_STAND, side)
            Mode.WALK -> {
                val f = SpriteAssets.walkFrame(SpriteAssets.Outfit.NORMAL, walkDir, frameToggle)
                setBitmap(f.path, side, f.flip)
            }
            Mode.WORK_WALK -> {
                val f = SpriteAssets.walkFrame(SpriteAssets.Outfit.WORK, walkDir, frameToggle)
                setBitmap(f.path, side, f.flip)
            }
            Mode.MUSIC_WALK -> {
                val f = SpriteAssets.walkFrame(SpriteAssets.Outfit.MUSIC, walkDir, frameToggle)
                setBitmap(f.path, side, f.flip)
            }
            Mode.POSE -> setBitmap(poseFrames.getOrElse(poseIndex) { SpriteAssets.STAND }, side)
        }
    }

    private fun setBitmap(path: String, side: Int, flip: Boolean = false) {
        val bmp = SpriteAssets.load(context, path, maxSide = side, flip = flip) ?: return
        imageView.setImageBitmap(bmp)
    }

    private fun startFrameToggle(intervalMs: Long) {
        frameRunnable = object : Runnable {
            override fun run() {
                frameToggle = !frameToggle
                applyFrame()
                handler.postDelayed(this, intervalMs)
            }
        }
        handler.postDelayed(frameRunnable!!, intervalMs)
    }

    private fun startMoveLoop(intervalMs: Long) {
        moveRunnable = object : Runnable {
            override fun run() {
                if (mode == Mode.WALK || mode == Mode.MUSIC_WALK) {
                    onWalkMove?.invoke()
                }
                handler.postDelayed(this, intervalMs)
            }
        }
        handler.postDelayed(moveRunnable!!, intervalMs)
    }

    private fun startBobble() {
        stopBobble()
        bobbleRunnable = object : Runnable {
            var up = true
            override fun run() {
                if (mode != Mode.SLEEP) return
                imageView.translationY = baseTranslationY + if (up) -REST_BOBBLE_PX else 0
                up = !up
                val delay = if (up) (2500L..4500L).random() else REST_BOBBLE_MS
                handler.postDelayed(this, delay)
            }
        }
        handler.postDelayed(bobbleRunnable!!, (2500L..4500L).random())
    }

    private fun stopBobble() {
        bobbleRunnable?.let { handler.removeCallbacks(it) }
        bobbleRunnable = null
    }

    private fun stopAnimLoops() {
        frameRunnable?.let { handler.removeCallbacks(it) }
        moveRunnable?.let { handler.removeCallbacks(it) }
        frameRunnable = null
        moveRunnable = null
    }
}

fun Int.dp(context: Context): Int =
    TypedValue.applyDimension(
        TypedValue.COMPLEX_UNIT_DIP,
        this.toFloat(),
        context.resources.displayMetrics,
    ).toInt()
