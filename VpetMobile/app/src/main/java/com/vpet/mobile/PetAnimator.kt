package com.vpet.mobile

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
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
    /** 对照桌面 HAPPY_JUMP：上移整窗/宿主；null 时退回 translationY（需父布局不裁切）。 */
    private val onJumpLift: ((liftPx: Int) -> Unit)? = null,
) {
    enum class Mode {
        STAND, HI, SLEEP, SLEEP_PEEK, WALK, HAPPY,
        WORK_STAND, WORK_WALK,
        MUSIC_STAND, MUSIC_WALK,
        PLAY_GAME, WATCH_VIDEO,
        DRAG_MOVE,
        POSE,
    }

    companion object {
        const val WALK_FRAME_MS = 210L
        /** 自由走动位移：切帧仍用 WALK_FRAME_MS，移速单独放缓。 */
        const val MOVE_INTERVAL_MS = 72L
        const val MUSIC_WALK_FRAME_MS = 280L
        const val MUSIC_MOVE_INTERVAL_MS = 100L
        const val ACTION_FRAME_MS = 180L
        const val ANGRY_FRAME_MS = 280L
        const val HAPPY_FRAME_MS = 220L
        const val HAPPY_CYCLES = 3
        /** 对照 pet.py HAPPY_JUMP_PX */
        const val HAPPY_JUMP_PX = 14
        const val MOVE_STEP = 1
        /** 拖拽 move1/2/3：对照 pet.py MOVE23_* / MOVE1_*。 */
        const val MOVE23_DURATION_MS = 2500L
        const val MOVE1_DURATION_MS = 5000L
        const val MOVE23_FRAME_MS = 90L
        const val MOVE_DRAG_CYCLES = 2
        const val MOVE_CYCLE_MS = MOVE23_DURATION_MS + MOVE1_DURATION_MS
        const val DRAG_YUQI_MS = 3000L
        const val POSE_HOLD_MS = 1600L
        const val REST_BOBBLE_PX = 3
        const val REST_BOBBLE_MS = 160L
        const val VIDEO_SLIDE_MS = 80L
        const val VIDEO_STRIP_RATIO = 0.34f
        /** 对照 INTERACT_DURATIONS / IDEA_STAND_MS */
        const val IDEA_STAND_MS = 520L
        /** 互动动作/表情略加长，便于看清（菜单触发）。 */
        const val DUR_SQUAT = 3500L
        const val DUR_EAT = 5000L
        const val DUR_ANGRY = 5800L
        const val DUR_QUESTION = 4200L
        const val DUR_IDEA = 5200L
        const val DUR_HAPPY = 6000L
        const val DUR_KICK = 2200L
        const val DUR_SHY = 4500L
        const val DUR_WINK = 3800L
        const val DUR_LIKE = 3800L
        const val DUR_BIXIN = 5200L
        const val DUR_YES = 3600L
        const val DUR_NO = 3600L
        const val DUR_HI = 5500L
        const val DUR_CALL = 5800L
        const val SAD_SQUAT_MS = 1300L
        const val SAD_SAD1_MS = 1300L
        const val SAD_SAD2_MS = 3900L
        const val DUR_SAD = SAD_SQUAT_MS + SAD_SAD1_MS + SAD_SAD2_MS
    }

    private val handler = Handler(Looper.getMainLooper())
    private var frameRunnable: Runnable? = null
    private var moveRunnable: Runnable? = null
    private var bobbleRunnable: Runnable? = null
    private var poseEndRunnable: Runnable? = null
    private var mode = Mode.STAND
    private var frameToggle = false
    private var poseFrames: List<String> = emptyList()
    private var poseIndex = 0
    private var poseLoop = false
    private var resumeAfterPose: Mode = Mode.STAND
    private var baseTranslationY = 0f
    var walkDir: SpriteAssets.Dir = SpriteAssets.Dir.RIGHT
        private set
    private val turnGuard = WalkTurnGuard()
    /** stand 参考宽高：全部立绘共用同一 scale（对照桌面 `_reference_scale`），禁止按帧各自 fit。 */
    private var refStandW = 0
    private var refStandH = 0
    private var dragMoveStartMs = 0L
    private var videoVariantIndex = 0
    private var videoOnLeft = true
    private var videoSlidePhase = 0
    private var videoScrollPx = 0f
    private var outfitDecors: List<OutfitStore.Decor> = emptyList()

    /** 兼容旧代码：+1 右 / -1 左 */
    @Deprecated("use walkDir")
    val legacyWalkSign: Int get() = if (walkDir == SpriteAssets.Dir.LEFT) -1 else 1

    fun currentMode(): Mode = mode

    fun petImage(): ImageView = imageView

    /** 装扮烘焙进立绘；保存后立刻 applyFrame 同步到桌宠。 */
    fun syncOutfit(list: List<OutfitStore.Decor>) {
        outfitDecors = list
        applyFrame()
    }

    private fun paintOutfit(canvas: Canvas, side: Int) {
        if (outfitDecors.isEmpty()) return
        OutfitStore.drawOnPet(canvas, context, 0f, 0f, side.toFloat(), outfitDecors)
    }

    fun playDissolve(reverse: Boolean, totalMs: Long? = null, onDone: (() -> Unit)? = null) {
        PixelDissolve.play(imageView, reverse = reverse, totalMs = totalMs, onDone = onDone)
    }

    fun walkStepPx(): Int = MOVE_STEP

    fun walkDelta(): Pair<Int, Int> {
        val s = walkStepPx()
        return walkDir.dx * s to walkDir.dy * s
    }

    fun setWalkDir(dir: SpriteAssets.Dir) {
        val resolved = turnGuard.resolve(dir, walkDir)
        if (walkDir == resolved) return
        walkDir = resolved
        if (mode == Mode.WALK || mode == Mode.WORK_WALK || mode == Mode.MUSIC_WALK) {
            applyFrame()
        }
    }

    fun reverseWalkDir() {
        val flipped = when (walkDir) {
            SpriteAssets.Dir.LEFT -> SpriteAssets.Dir.RIGHT
            SpriteAssets.Dir.RIGHT -> SpriteAssets.Dir.LEFT
            SpriteAssets.Dir.FRONT -> SpriteAssets.Dir.BACK
            SpriteAssets.Dir.BACK -> SpriteAssets.Dir.FRONT
        }
        setWalkDir(flipped)
    }

    fun resetWalkTurnGuard() {
        turnGuard.reset()
    }

    fun pickInboundDir(canGo: (SpriteAssets.Dir) -> Boolean): SpriteAssets.Dir? {
        val ok = SpriteAssets.Dir.entries.filter(canGo)
        if (ok.isEmpty()) return null
        val others = ok.filter { it != walkDir }
        return (others.ifEmpty { ok }).random()
    }

    /** 覆盖显示边长（家园等）；null 则用桌宠档位。 */
    private var displaySideOverride: Int? = null

    /** 无参：始终读最新桌宠档位（设置滑条/菜单改大小）。家园等需固定边长时用 [applyDisplaySize] 传 px。 */
    fun applyDisplaySize() {
        applyDisplaySize(PetPrefs.sizePx(context))
    }

    fun applyDisplaySize(px: Int) {
        val side = px.coerceAtLeast(24)
        displaySideOverride = side
        // 改尺寸后重算 stand 参考，避免旧采样尺寸污染缩放
        refStandW = 0
        refStandH = 0
        val lp = imageView.layoutParams ?: ViewGroup.LayoutParams(side, side)
        lp.width = side
        lp.height = side
        imageView.layoutParams = lp
        applyFrame()
    }

    /** 清掉家园等临时覆盖，恢复跟随 PetPrefs。 */
    fun clearDisplaySizeOverride() {
        displaySideOverride = null
    }

    private fun displaySide(): Int =
        displaySideOverride ?: PetPrefs.sizePx(context)

    fun setMode(m: Mode, driveMove: Boolean = true) {
        if (m == mode && m != Mode.POSE) {
            // 同模式重复进入：避免重载立绘/重启 bobble 造成闪烁
            if (m == Mode.SLEEP || m == Mode.SLEEP_PEEK || m == Mode.PLAY_GAME ||
                m == Mode.WATCH_VIDEO || m == Mode.MUSIC_STAND
            ) {
                return
            }
        }
        if (m != Mode.POSE) poseFrames = emptyList()
        val prev = mode
        mode = m
        frameToggle = false
        stopAnimLoops()
        cancelPoseEnd()
        if (prev == Mode.SLEEP || prev == Mode.SLEEP_PEEK || prev == Mode.HAPPY ||
            prev == Mode.PLAY_GAME || prev == Mode.WATCH_VIDEO || prev == Mode.MUSIC_STAND
        ) {
            stopBobble()
            applyHappyLift(0)
        }
        if (m != Mode.HAPPY) applyFrame()
        when (m) {
            Mode.HI -> startFrameToggle(ACTION_FRAME_MS)
            Mode.SLEEP, Mode.PLAY_GAME, Mode.MUSIC_STAND -> {
                baseTranslationY = imageView.translationY
                startBobble()
            }
            Mode.WATCH_VIDEO -> {
                baseTranslationY = imageView.translationY
                videoVariantIndex = 0
                videoSlidePhase = 0
                videoScrollPx = 0f
                videoOnLeft = true
                startBobble()
                startFrameToggle(VIDEO_SLIDE_MS)
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
                // 对照 _happy_step：HAPPY_CYCLES 次跳，再由 hold 收尾
                startHappyCycles()
            }
            Mode.STAND, Mode.WORK_STAND, Mode.POSE, Mode.DRAG_MOVE -> Unit
        }
    }

    /** 场景姿势被表情/走动盖掉后：强制重绘（即使已是目标 mode）。 */
    fun forceSceneMode(m: Mode) {
        if (mode != m) {
            setMode(m, driveMove = false)
            return
        }
        when (m) {
            Mode.WATCH_VIDEO -> {
                if (frameRunnable == null) startFrameToggle(VIDEO_SLIDE_MS)
                if (bobbleRunnable == null) {
                    baseTranslationY = imageView.translationY
                    startBobble()
                }
                applyFrame()
            }
            Mode.PLAY_GAME, Mode.MUSIC_STAND, Mode.SLEEP -> {
                if (bobbleRunnable == null) {
                    baseTranslationY = imageView.translationY
                    startBobble()
                }
                applyFrame()
            }
            else -> applyFrame()
        }
    }

    /**
     * 安静模式偷看：只换 sleep1/sleep2，不走完整 setMode 拆装，减少闪现。
     */
    fun setQuietPeek(peek: Boolean) {
        val target = if (peek) Mode.SLEEP_PEEK else Mode.SLEEP
        if (mode == target) return
        val fromSleep = mode == Mode.SLEEP || mode == Mode.SLEEP_PEEK
        mode = target
        if (peek) {
            stopBobble()
            imageView.translationY = baseTranslationY
            applyFrame()
        } else {
            applyFrame()
            if (fromSleep) {
                if (bobbleRunnable == null) startBobble()
            } else {
                baseTranslationY = imageView.translationY
                startBobble()
            }
        }
    }

    /**
     * 采集靠近食物：对照桌面 `_set_image(happy/stand)`，只切静帧，不开跳跃 happy。
     */
    fun setCollectNear(near: Boolean) {
        stopAnimLoops()
        cancelPoseEnd()
        stopBobble()
        imageView.translationY = baseTranslationY
        mode = Mode.STAND
        setBitmap(
            if (near) SpriteAssets.HAPPY else SpriteAssets.STAND,
            displaySide(),
        )
    }

    /** 拖拽中播 move1↔move2/3（对照 `_start_drag_move`）。 */
    fun startDragMove() {
        dragMoveStartMs = android.os.SystemClock.elapsedRealtime()
        mode = Mode.DRAG_MOVE
        stopAnimLoops()
        cancelPoseEnd()
        applyFrame()
        frameRunnable = object : Runnable {
            override fun run() {
                if (mode != Mode.DRAG_MOVE) return
                applyFrame()
                handler.postDelayed(this, MOVE23_FRAME_MS)
            }
        }
        handler.postDelayed(frameRunnable!!, MOVE23_FRAME_MS)
    }

    fun stopDragMove() {
        if (mode != Mode.DRAG_MOVE) return
        stopAnimLoops()
        setMode(Mode.STAND, driveMove = false)
    }

    /**
     * @param loop true：在 holdMs 内循环切帧（吃/打电话/打招呼）；false：播完停在最后一帧（默认，避免表情乱循环）。
     */
    fun playPose(
        frames: List<String>,
        holdMs: Long = POSE_HOLD_MS,
        resume: Mode = Mode.STAND,
        loop: Boolean = false,
        frameMs: Long = ACTION_FRAME_MS,
    ) {
        if (frames.isEmpty()) return
        if (mode == Mode.SLEEP || mode == Mode.PLAY_GAME || mode == Mode.WATCH_VIDEO ||
            mode == Mode.MUSIC_STAND
        ) {
            stopBobble()
            imageView.translationY = baseTranslationY
        }
        resumeAfterPose = resume
        poseFrames = frames
        poseIndex = 0
        poseLoop = loop
        mode = Mode.POSE
        stopAnimLoops()
        cancelPoseEnd()
        applyFrame()
        if (frames.size > 1) {
            frameRunnable = object : Runnable {
                override fun run() {
                    if (mode != Mode.POSE || poseFrames.isEmpty()) return
                    if (poseLoop) {
                        poseIndex = (poseIndex + 1) % poseFrames.size
                        applyFrame()
                        handler.postDelayed(this, frameMs)
                    } else {
                        if (poseIndex >= poseFrames.lastIndex) return
                        poseIndex++
                        applyFrame()
                        if (poseIndex < poseFrames.lastIndex) {
                            handler.postDelayed(this, frameMs)
                        }
                    }
                }
            }
            handler.postDelayed(frameRunnable!!, frameMs)
        }
        poseEndRunnable = Runnable {
            if (mode == Mode.POSE) setMode(resumeAfterPose)
        }
        handler.postDelayed(poseEndRunnable!!, holdMs.coerceAtLeast(frameMs))
    }

    /** 分阶段立绘：每段 (path, 停留 ms)，对照伤心 squat→sad1→sad2 / 有主意 stand→eat2。 */
    fun playTimedPose(steps: List<Pair<String, Long>>, resume: Mode = Mode.STAND) {
        if (steps.isEmpty()) return
        resumeAfterPose = resume
        mode = Mode.POSE
        stopAnimLoops()
        cancelPoseEnd()
        var i = 0
        fun showStep() {
            if (mode != Mode.POSE) return
            if (i >= steps.size) {
                setMode(resumeAfterPose)
                return
            }
            val (path, dur) = steps[i]
            poseFrames = listOf(path)
            poseIndex = 0
            applyFrame()
            i++
            frameRunnable = Runnable { showStep() }
            handler.postDelayed(frameRunnable!!, dur.coerceAtLeast(1L))
        }
        showStep()
    }

    private fun applyHappyLift(liftPx: Int) {
        val lift = liftPx.coerceAtLeast(0)
        if (onJumpLift != null) {
            imageView.translationY = baseTranslationY
            onJumpLift.invoke(lift)
        } else {
            imageView.translationY = baseTranslationY - lift
        }
    }

    private fun startHappyCycles() {
        stopAnimLoops()
        cancelPoseEnd()
        var step = 0
        val total = HAPPY_CYCLES * 2
        baseTranslationY = imageView.translationY
        frameRunnable = object : Runnable {
            override fun run() {
                if (mode != Mode.HAPPY) return
                if (step >= total) {
                    // 动画段结束，保持站立等待 hold（由外部 DUR_HAPPY 的 setMode 收尾）
                    applyHappyLift(0)
                    setBitmap(SpriteAssets.STAND, displaySide())
                    return
                }
                if (step % 2 == 0) {
                    setBitmap(SpriteAssets.HAPPY, displaySide())
                    applyHappyLift(HAPPY_JUMP_PX)
                } else {
                    setBitmap(SpriteAssets.STAND, displaySide())
                    applyHappyLift(0)
                }
                step++
                handler.postDelayed(this, HAPPY_FRAME_MS)
            }
        }
        handler.post(frameRunnable!!)
        poseEndRunnable = Runnable {
            if (mode == Mode.HAPPY) {
                applyHappyLift(0)
                setMode(Mode.STAND)
            }
        }
        handler.postDelayed(poseEndRunnable!!, DUR_HAPPY)
    }

    fun stop() {
        stopAnimLoops()
        cancelPoseEnd()
        stopBobble()
    }

    private fun cancelPoseEnd() {
        poseEndRunnable?.let { handler.removeCallbacks(it) }
        poseEndRunnable = null
    }

    fun applyFrame() {
        val side = displaySide()
        when (mode) {
            Mode.STAND -> setBitmap(SpriteAssets.STAND, side)
            Mode.HI -> setBitmap(if (frameToggle) SpriteAssets.HI2 else SpriteAssets.HI1, side)
            Mode.SLEEP -> setBitmap(SpriteAssets.SLEEP2, side)
            Mode.SLEEP_PEEK -> setBitmap(SpriteAssets.SLEEP1, side)
            Mode.HAPPY -> setBitmap(SpriteAssets.HAPPY, side)
            Mode.WORK_STAND -> setBitmap(SpriteAssets.WORK_STAND, side)
            Mode.MUSIC_STAND -> setBitmap(SpriteAssets.MUSIC_STAND, side)
            Mode.PLAY_GAME -> setSceneComposite(
                leftPath = SpriteAssets.PLAY_GAME2,
                rightPath = SpriteAssets.PLAY_GAME1,
                side = side,
                leftRatio = 0.36f,
            )
            Mode.WATCH_VIDEO -> {
                videoSlidePhase++
                videoScrollPx += (side / 70f).coerceAtLeast(2f)
                if (videoSlidePhase % 240 == 0) videoOnLeft = !videoOnLeft
                setVideoCreditsComposite(side, videoScrollPx, videoOnLeft)
            }
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
            Mode.DRAG_MOVE -> {
                val elapsed = android.os.SystemClock.elapsedRealtime() - dragMoveStartMs
                val totalMs = MOVE_CYCLE_MS * MOVE_DRAG_CYCLES
                val path = if (elapsed >= totalMs) {
                    SpriteAssets.MOVE1
                } else {
                    val phase = elapsed % MOVE_CYCLE_MS
                    if (phase < MOVE23_DURATION_MS) {
                        if ((phase / MOVE23_FRAME_MS) % 2L == 0L) SpriteAssets.MOVE2
                        else SpriteAssets.MOVE3
                    } else {
                        SpriteAssets.MOVE1
                    }
                }
                setBitmap(path, side)
            }
            Mode.POSE -> setBitmap(poseFrames.getOrElse(poseIndex) { SpriteAssets.STAND }, side)
        }
    }

    private fun ensureStandRef(side: Int) {
        if (refStandW > 0 && refStandH > 0) return
        val stand = SpriteAssets.load(context, SpriteAssets.STAND, maxSide = side * 2) ?: return
        refStandW = stand.width.coerceAtLeast(1)
        refStandH = stand.height.coerceAtLeast(1)
        try {
            stand.recycle()
        } catch (_: Exception) {
        }
    }

    private fun setBitmap(path: String, side: Int, flip: Boolean = false) {
        val raw = SpriteAssets.load(context, path, maxSide = side * 2, flip = flip) ?: return
        if (path == SpriteAssets.STAND) {
            refStandW = raw.width.coerceAtLeast(1)
            refStandH = raw.height.coerceAtLeast(1)
        } else {
            ensureStandRef(side)
        }
        val rw = refStandW.coerceAtLeast(1)
        val rh = refStandH.coerceAtLeast(1)
        // 对照桌面 `_to_fixed_canvas(reference_scale=_reference_scale)`：
        // 各帧共用 stand 的缩放系数；溢出只裁切，不再二次压扁。
        val scale = minOf(side.toFloat() / rw, side.toFloat() / rh)
        val rawW = raw.width.coerceAtLeast(1).toFloat()
        val rawH = raw.height.coerceAtLeast(1).toFloat()
        val dw = (rawW * scale).toInt().coerceAtLeast(1)
        val dh = (rawH * scale).toInt().coerceAtLeast(1)
        val scaled = if (dw == raw.width && dh == raw.height) {
            raw
        } else {
            Bitmap.createScaledBitmap(raw, dw, dh, false).also {
                if (it != raw) raw.recycle()
            }
        }
        val out = Bitmap.createBitmap(side, side, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(out)
        val left = (side - dw) / 2f
        val top = (side - dh).toFloat()
        canvas.drawBitmap(scaled, left, top, null)
        paintOutfit(canvas, side)
        if (scaled !== out) {
            try {
                scaled.recycle()
            } catch (_: Exception) {
            }
        }
        // 固定边长，避免 wrap_content 随非方形图变大
        val lp = imageView.layoutParams
        if (lp != null && (lp.width != side || lp.height != side)) {
            lp.width = side
            lp.height = side
            imageView.layoutParams = lp
        }
        imageView.scaleType = ImageView.ScaleType.FIT_XY
        imageView.setImageBitmap(out)
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
        val musicStand = mode == Mode.MUSIC_STAND
        bobbleRunnable = object : Runnable {
            var up = true
            override fun run() {
                if (mode != Mode.SLEEP && mode != Mode.PLAY_GAME &&
                    mode != Mode.WATCH_VIDEO && mode != Mode.MUSIC_STAND
                ) {
                    return
                }
                imageView.translationY = baseTranslationY + if (up) -REST_BOBBLE_PX else 0
                up = !up
                val pause = if (mode == Mode.MUSIC_STAND) (700L..1600L).random()
                else (2500L..4500L).random()
                val delay = if (up) pause else REST_BOBBLE_MS
                handler.postDelayed(this, delay)
            }
        }
        val first = if (musicStand) (700L..1600L).random() else (2500L..4500L).random()
        handler.postDelayed(bobbleRunnable!!, first)
    }

    /** 切视频换色（对照桌面 app_scene_video_index）。 */
    fun rotateVideoPalette(signature: String) {
        val n = SpriteAssets.VIDEO_VARIANTS.size.coerceAtLeast(1)
        var idx = kotlin.math.abs(signature.hashCode()) % n
        if (idx == videoVariantIndex) idx = (idx + 1) % n
        videoVariantIndex = idx
        videoScrollPx = 0f
        videoSlidePhase = 0
        cachedVideoStrip = null
        cachedVideoStripKey = null
        if (mode == Mode.WATCH_VIDEO) {
            applyFrame()
        }
    }

    private var cachedVideoStrip: Bitmap? = null
    private var cachedVideoStripPeriod: Int = 1
    private var cachedVideoStripKey: String? = null
    private var cachedVideoPet: Bitmap? = null
    private var cachedVideoPetKey: String? = null

    /** 站立同比例角色 + 侧向竖滚条（对照桌面 `_compose_video_credits_scene`）。 */
    private fun setVideoCreditsComposite(side: Int, scrollPx: Float, videoOnLeft: Boolean) {
        ensureStandRef(side)
        val vidW = (side * VIDEO_STRIP_RATIO).toInt().coerceAtLeast(8)
        val tileMaxH = (side * 0.58f).toInt().coerceAtLeast(28)
        val tileGap = (side / 20).coerceAtLeast(6)
        val boost = 1.55f
        fun fit(src: Bitmap, mw: Int, mh: Int): Bitmap {
            val s = minOf(mw.toFloat() / src.width, mh.toFloat() / src.height)
            val dw = (src.width * s).toInt().coerceAtLeast(1)
            val dh = (src.height * s).toInt().coerceAtLeast(1)
            return if (dw == src.width && dh == src.height) src
            else Bitmap.createScaledBitmap(src, dw, dh, false)
        }
        val stripKey = "${side}_${videoVariantIndex}_${vidW}"
        if (cachedVideoStripKey != stripKey || cachedVideoStrip == null) {
            try { cachedVideoStrip?.recycle() } catch (_: Exception) {}
            val ordered = ArrayList<String>()
            val paths = SpriteAssets.VIDEO_VARIANTS
            if (paths.isNotEmpty()) {
                val startIdx = videoVariantIndex % paths.size
                for (i in paths.indices) ordered += paths[(startIdx + i) % paths.size]
            }
            val tiles = ArrayList<Bitmap>()
            val tmp = ArrayList<Bitmap>()
            for (pathName in ordered) {
                val raw = SpriteAssets.load(context, pathName, maxSide = side * 2) ?: continue
                tmp += raw
                var t = fit(raw, vidW, tileMaxH)
                if (t !== raw) tmp += t
                var nw = (t.width * boost).toInt().coerceAtLeast(1)
                var nh = (t.height * boost).toInt().coerceAtLeast(1)
                val maxW = (vidW * 1.2f).toInt().coerceAtLeast(vidW)
                if (nw > maxW) {
                    val sc = maxW.toFloat() / nw
                    nw = (nw * sc).toInt().coerceAtLeast(1)
                    nh = (nh * sc).toInt().coerceAtLeast(1)
                }
                if (nw != t.width || nh != t.height) {
                    t = Bitmap.createScaledBitmap(t, nw, nh, false).also { tmp += it }
                }
                tiles += t
            }
            if (tiles.isEmpty()) return
            val period = tiles.sumOf { it.height + tileGap }.coerceAtLeast(1)
            val stripW = maxOf(vidW, tiles.maxOf { it.width })
            val strip = Bitmap.createBitmap(stripW, period * 2, Bitmap.Config.ARGB_8888)
            val sc = Canvas(strip)
            val paintSoft = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
                val cm = android.graphics.ColorMatrix().apply { setSaturation(0.55f) }
                colorFilter = android.graphics.ColorMatrixColorFilter(cm)
                alpha = 210
            }
            var y = 0
            repeat(2) {
                for (t in tiles) {
                    val x = ((stripW - t.width) / 2).coerceAtLeast(0)
                    sc.drawBitmap(t, x.toFloat(), y.toFloat(), paintSoft)
                    y += t.height + tileGap
                }
            }
            for (b in tmp) {
                try { if (!b.isRecycled && b !in tiles) b.recycle() } catch (_: Exception) {}
            }
            cachedVideoStrip = strip
            cachedVideoStripPeriod = period
            cachedVideoStripKey = stripKey
        }
        val strip = cachedVideoStrip ?: return
        val period = cachedVideoStripPeriod.coerceAtLeast(1)
        val scroll = (((scrollPx.toInt() % period) + period) % period)
        val regionH = side.coerceAtMost((strip.height - scroll).coerceAtLeast(1))
        val region = try {
            Bitmap.createBitmap(strip, 0, scroll, strip.width, regionH)
        } catch (_: Exception) {
            return
        }

        val petKey = "${side}_watch"
        if (cachedVideoPetKey != petKey || cachedVideoPet == null) {
            try { cachedVideoPet?.recycle() } catch (_: Exception) {}
            val petRaw = SpriteAssets.load(context, SpriteAssets.WATCH_VIDEO1, maxSide = side * 2) ?: run {
                try { region.recycle() } catch (_: Exception) {}
                return
            }
            val rw = refStandW.coerceAtLeast(1)
            val rh = refStandH.coerceAtLeast(1)
            val refScale = minOf(side.toFloat() / rw, side.toFloat() / rh)
            val pw = petRaw.width.coerceAtLeast(1)
            val ph = petRaw.height.coerceAtLeast(1)
            var s = refScale
            if (pw * s > side || ph * s > side) {
                s = minOf(side.toFloat() / pw, side.toFloat() / ph)
            }
            val dw = (pw * s).toInt().coerceAtLeast(1)
            val dh = (ph * s).toInt().coerceAtLeast(1)
            val scaled = if (dw == petRaw.width && dh == petRaw.height) petRaw
            else Bitmap.createScaledBitmap(petRaw, dw, dh, false)
            val layer = Bitmap.createBitmap(side, side, Bitmap.Config.ARGB_8888)
            val lc = Canvas(layer)
            val px = ((side - scaled.width) / 2).coerceAtLeast(0)
            val py = (side - scaled.height).coerceAtLeast(0)
            lc.drawBitmap(scaled, px.toFloat(), py.toFloat(), null)
            if (scaled !== petRaw) {
                try { scaled.recycle() } catch (_: Exception) {}
            }
            try { if (!petRaw.isRecycled) petRaw.recycle() } catch (_: Exception) {}
            cachedVideoPet = layer
            cachedVideoPetKey = petKey
        }
        val petLayer = cachedVideoPet ?: return
        val out = Bitmap.createBitmap(side, side, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(out)
        val ox = if (videoOnLeft) 0 else (side - region.width).coerceAtLeast(0)
        canvas.drawBitmap(region, ox.toFloat(), 0f, null)
        canvas.drawBitmap(petLayer, 0f, 0f, null)
        paintOutfit(canvas, side)
        try { region.recycle() } catch (_: Exception) {}
        val lp = imageView.layoutParams
        if (lp != null && (lp.width != side || lp.height != side)) {
            lp.width = side
            lp.height = side
            imageView.layoutParams = lp
        }
        imageView.scaleType = ImageView.ScaleType.FIT_XY
        imageView.setImageBitmap(out)
    }
    private fun setSceneComposite(
        leftPath: String,
        rightPath: String,
        side: Int,
        leftRatio: Float,
        slideX: Int = 0,
    ) {
        val leftRaw = SpriteAssets.load(context, leftPath, maxSide = side * 2) ?: return
        val rightRaw = SpriteAssets.load(context, rightPath, maxSide = side * 2) ?: run {
            try { leftRaw.recycle() } catch (_: Exception) {}
            return
        }
        val gap = (side / 36).coerceAtLeast(2)
        val leftSlot = ((side * leftRatio).toInt() - gap / 2).coerceAtLeast(8)
        val rightSlot = (side - leftSlot - gap).coerceAtLeast(8)
        fun fit(src: Bitmap, mw: Int, mh: Int): Bitmap {
            val s = minOf(mw.toFloat() / src.width, mh.toFloat() / src.height)
            val dw = (src.width * s).toInt().coerceAtLeast(1)
            val dh = (src.height * s).toInt().coerceAtLeast(1)
            return if (dw == src.width && dh == src.height) src
            else Bitmap.createScaledBitmap(src, dw, dh, false)
        }
        val L = fit(leftRaw, leftSlot, side)
        val R = fit(rightRaw, rightSlot, side)
        val out = Bitmap.createBitmap(side, side, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(out)
        val lx = ((leftSlot - L.width) / 2 + slideX).coerceAtLeast(0)
        val rx = leftSlot + gap + ((rightSlot - R.width) / 2).coerceAtLeast(0)
        canvas.drawBitmap(L, lx.toFloat(), (side - L.height).toFloat(), null)
        canvas.drawBitmap(R, rx.toFloat(), (side - R.height).toFloat(), null)
        paintOutfit(canvas, side)
        if (L !== leftRaw) try { L.recycle() } catch (_: Exception) {}
        if (R !== rightRaw) try { R.recycle() } catch (_: Exception) {}
        try { leftRaw.recycle() } catch (_: Exception) {}
        try { rightRaw.recycle() } catch (_: Exception) {}
        val lp = imageView.layoutParams
        if (lp != null && (lp.width != side || lp.height != side)) {
            lp.width = side
            lp.height = side
            imageView.layoutParams = lp
        }
        imageView.scaleType = ImageView.ScaleType.FIT_XY
        imageView.setImageBitmap(out)
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
