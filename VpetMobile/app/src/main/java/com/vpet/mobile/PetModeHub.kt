package com.vpet.mobile

import android.content.Context
import android.graphics.PixelFormat
import android.graphics.Point
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.Toast
import com.vpet.mobile.databinding.OverlayPomoHudBinding
import com.vpet.mobile.databinding.OverlayQuietHudBinding
import kotlin.random.Random

/**
 * 模式编排：跟随 / 睡眠 / 工作 / 自由·漫步 / 工具 / 番茄钟。
 */
class PetModeHub(
    private val context: Context,
    private val animator: PetAnimator,
    private val windowManager: WindowManager? = null,
    private val roomHost: FrameLayout? = null,
    private val screenSize: () -> Point,
    private val petSize: () -> Int,
    private val petTopLeft: () -> Point,
    private val setPetTopLeft: (Int, Int) -> Unit,
    private val raisePetOverlay: (() -> Unit)? = null,
) {
    enum class Locomotion { NONE, FREE, STROLL }

    /** 默认态=自由；独占模式结束后一律回到自由。 */
    private var locomotion = Locomotion.FREE
    private var freeIdleUntil = 0L
    private var walkStepsLeft = 0
    private var workEngine: WorkEngine? = null
    private var followEngine: FollowEngine? = null
    private var quiet: QuietSession? = null
    private var pomo: PomodoroSession? = null
    private var workProps: WorkPropsUi? = null
    private var quietHud: OverlayQuietHudBinding? = null
    private var pomoHud: OverlayPomoHudBinding? = null
    private var followCatcher: View? = null
    private var collectUi: CollectOverlayUi? = null
    private var toolClock: ToolClockUi? = null
    private var musicPlayer: MusicPlayer? = null
    private var companion: CompanionFollower? = null
    private var speech: SpeechBubbleUi? = null
    private var fx: PetFxUi? = null
    private var companionFx: PetFxUi? = null
    private var voice: VoicePlayer? = null
    private var musicMode = false
    /** 跟随系统放歌进入的音乐漫步（不播本机曲库）。 */
    private var musicAmbientOnly = false
    private var appSceneMonitor: AppSceneMonitor? = null
    private var ambientMusicSignature: String = ""
    private var musicAffinityJob: Runnable? = null
    private var musicAffinityCharId: String = "aoba"
    private var currentMusicTrack: BundledMusic.Track? = null
    /** 视频软件：避让中央 + 时长桶（立绘稍后）。 */
    private var videoMode = false
    private var videoPlaying = false
    /** 游戏软件：时长桶（立绘稍后）。 */
    private var appGameMode = false
    private var lastAppSceneToastMs = 0L
    /** 采集中把主宠窗口设为不可点，避免抢走拖动。 */
    var setPetTouchable: ((Boolean) -> Unit)? = null
    /** abortAllModes 切换中：禁止 end* 回调抢先 returnToFree。 */
    private var suppressResumeFree = false
    private val mainHandler = android.os.Handler(android.os.Looper.getMainLooper())
    private var lastUserActivityMs = android.os.SystemClock.elapsedRealtime()
    private var lastDragYuqiMs = 0L
    private var lastMetaGlobalMs = 0L
    private val metaEventMs = mutableMapOf<String, Long>()
    private var metaIdleJob: Runnable? = null
    private var workTimerJob: Runnable? = null
    private var workBanterJob: Runnable? = null
    private var workBanterLastMs = 0L
    private var workShowEndButton = true
    private var workContinuousSession = false
    private var idleActionBusy = false
    private var freeIdlePulseJob: Runnable? = null
    /** 取消叠层的「恢复走动」；世代号防止旧回调抢跑。 */
    private var resumeWalkJob: Runnable? = null
    private var interactGen = 0

    companion object {
        const val FREE_RANDOM_ACTION_CHANCE = 0.06f
        const val MOOD_RANDOM_CHANCE = 0.09f
        const val MOOD_LOW_THRESHOLD = 40
        const val VOICE_FREE_RANDOM_CHANCE = 0.045f
        const val VOICE_WORK_RANDOM_CHANCE = VOICE_FREE_RANDOM_CHANCE
        const val WORK_MODE_BANTER_COOLDOWN_MS = 30_000L
        const val WORK_MODE_BANTER_INTERVAL_LO_MS = 30_000L
        const val WORK_MODE_BANTER_INTERVAL_HI_MS = 90_000L
        const val DRAG_MOVE_VOICE_AFTER_MS = 3000L
        const val DRAG_MOVE_VOICE_RETRY_MS = 6500L
        const val META_BANTER_GLOBAL_COOLDOWN_MS = 110_000L
        const val META_BANTER_IDLE_MS = 8 * 60_000L
        const val META_BANTER_IDLE_CHECK_MS = 25_000L
    }

    val isWorking get() = workEngine?.active == true
    val isFollowing get() = followEngine?.active == true
    val isQuiet get() = quiet?.active == true
    val isPomodoro get() = pomo?.active == true
    val isMusic get() = musicMode
    val isVideoMode get() = videoMode
    val isAppGameMode get() = appGameMode
    val isCollecting get() = collectUi?.active == true
    /** 熄屏显示姿势变化时回调（由 OverlayService 挂接）。 */
    var onLockScreenPoseChanged: (() -> Unit)? = null
    val isFreeMode get() =
        !isFollowing && !isWorking && !isQuiet && !isPomodoro && !musicMode && !isCollecting &&
            !videoMode && !appGameMode &&
            locomotion == Locomotion.FREE
    val isStrollMode get() =
        !isFollowing && !isWorking && !isQuiet && !isPomodoro && !musicMode && !isCollecting &&
            !videoMode && !appGameMode &&
            locomotion == Locomotion.STROLL

    /** 菜单项是否当前选中（打勾）。 */
    fun isMenuChecked(id: String): Boolean = when (id) {
        "mode_free" -> isFreeMode
        "mode_follow" -> isFollowing
        "mode_stroll" -> isStrollMode
        "mode_quiet" -> isQuiet
        "mode_music" -> musicMode
        "game_collect" -> isCollecting
        "work_free", "act_work" -> isWorking && (workEngine?.isContinuous == true)
        "work_custom" -> isWorking && workEngine?.isContinuous == false
        "panel_companion" -> AppDataStore.companionEnabled(context) && (companion?.active == true)
        "panel_persona" -> AppDataStore.isJinmu(context)
        "work_show_props" -> AppDataStore.workShowProps(context)
        "work_show_stack" -> AppDataStore.workShowStack(context)
        "set_sound" -> AppDataStore.soundOn(context)
        "set_voice" -> AppDataStore.voiceMode(context)
        "set_size_s" -> PetPrefs.sizeLabel(context) == "小"
        "set_size_m" -> PetPrefs.sizeLabel(context) == "中"
        "set_size_l" -> PetPrefs.sizeLabel(context) == "大"
        "set_font_s" -> AppDataStore.fontLabel(context) == "小"
        "set_font_m" -> AppDataStore.fontLabel(context) == "中"
        "set_font_l" -> AppDataStore.fontLabel(context) == "大"
        "set_font_xl" -> AppDataStore.fontLabel(context) == "特大"
        "set_diff_low" -> AppDataStore.difficulty(context) == "低"
        "set_diff_mid" -> AppDataStore.difficulty(context) == "中"
        "set_diff_high" -> AppDataStore.difficulty(context) == "高"
        "tool_pomo_custom" -> isPomodoro
        "tool_sw" -> toolClock?.isToolStopwatchShowing() == true
        else -> false
    }
    val locomotionEnabled get() =
        locomotion != Locomotion.NONE && !isWorking && !isFollowing && !isQuiet

    fun syncAttachedFx() {
        fx?.syncPlace()
        companionFx?.syncPlace()
    }

    fun attach() {
        AppDataStore.ensureAudioBalance(context)
        workProps = WorkPropsUi(
            context = context,
            windowManager = windowManager,
            roomHost = roomHost,
            onEndClick = { endWork(fromMenu = true) },
            onFlagFootDrag = { fx, fy -> workEngine?.moveEndFoot(fx, fy) },
            onFlagDragEnd = { moved -> workEngine?.onFlagDragReleased(moved) },
        )
        toolClock = ToolClockUi(context, windowManager, roomHost)
        musicPlayer = MusicPlayer(context)
        speech = SpeechBubbleUi(
            context = context,
            windowManager = windowManager,
            roomHost = roomHost,
            petTopLeft = petTopLeft,
            petSize = petSize,
            screenSize = screenSize,
        )
        voice = VoicePlayer(context)
        voice?.hasCompanion = {
            AppDataStore.companionEnabled(context) && (companion?.active == true)
        }
        voice?.onSubtitle = { title, durationMs, source ->
            mainHandler.post {
                speech?.showVoiceSubtitle(title, durationMs + 1000L, source)
            }
        }
        voice?.onHideSubtitle = {
            mainHandler.post { speech?.hide() }
        }
        companion = CompanionFollower(
            context = context,
            windowManager = windowManager,
            roomHost = roomHost,
            petTopLeft = petTopLeft,
            petSize = petSize,
            screenSize = screenSize,
            mainDir = { animator.walkDir },
            mainMoving = {
                locomotionEnabled || isFollowing || isWorking ||
                    animator.currentMode() == PetAnimator.Mode.WALK ||
                    animator.currentMode() == PetAnimator.Mode.WORK_WALK ||
                    animator.currentMode() == PetAnimator.Mode.MUSIC_WALK
            },
        )
        companion?.workAnchor = {
            if (isWorking) workEngine?.endFoot() else null
        }
        companion?.onMultiClick = { clicks ->
            if (clicks >= 3) playHoldAllmate()
        }
        // 主宠特效更新后统一重排，避免伴侣被抬到桌宠之上
        // （PetFxUi.raisePet 回调改走 restack）
        fx = PetFxUi(
            context = context,
            windowManager = windowManager,
            roomHost = roomHost,
            petTopLeft = petTopLeft,
            petSize = petSize,
            raisePet = { restackDisplayLayers() },
        )
        syncHeadFlower()
        syncOutfit()
        if (AppDataStore.companionEnabled(context)) {
            companion?.start()
        }
        rebuildCompanionFx()
        startMetaIdlePoll()
        startHungerPoll()
        startAmbientMusicWatch()
        maybePromptUsageAccess()
        scheduleFreeIdlePulse()
        syncModeBucket()
        // H-STARTUP-SLEEP1：开场用 sleep1 立绘做入场溶解；有伴侣则同步入场
        mainHandler.post {
            animator.setMode(PetAnimator.Mode.SLEEP_PEEK)
            var petIn = false
            var companionIn = companion?.active != true
            fun afterEnter() {
                if (!petIn || !companionIn) return
                // 开宠时若系统已在放歌 → 直接音乐漫步
                if (ambientMusicActiveExternal()) {
                    enterMusicAmbient(fromStartup = true, signature = "startup")
                } else {
                    returnToFreeIfIdle(startWalk = true)
                }
                mainHandler.postDelayed({
                    val greet = PetProfileStore.consumeLaunchGreeting(context) ?: return@postDelayed
                    speak(greet, null, forceVoice = false)
                }, 200L)
            }
            if (companion?.active == true) {
                companion?.playDissolve(reverse = false) {
                    companionIn = true
                    afterEnter()
                }
            }
            animator.playDissolve(reverse = false) {
                petIn = true
                afterEnter()
            }
        }
    }

    /**
     * 无独占模式时回到自由走动（默认态）。
     * 对照桌面各模式 `_exit_*_to_free` / `_resume_idle`。
     */
    fun returnToFreeIfIdle(startWalk: Boolean = true) {
        if (suppressResumeFree) return
        if (isWorking || isFollowing || isQuiet || isPomodoro || musicMode || isCollecting) return
        if (videoMode || appGameMode) {
            reassertSceneSprite()
            return
        }
        locomotion = Locomotion.FREE
        freeIdleUntil = 0L
        idleActionBusy = false
        if (startWalk) {
            beginWalkBurst(music = false)
        } else {
            walkStepsLeft = 0
            animator.setMode(PetAnimator.Mode.STAND)
        }
        syncModeBucket()
    }

    /** 拖拽/落地后恢复走动：保持自由（或音乐漫步）。 */
    fun resumeWalkingAfterPause() {
        if (suppressResumeFree) return
        if (isWorking || isFollowing || isQuiet || isPomodoro || isCollecting) return
        if (videoMode || appGameMode) {
            reassertSceneSprite()
            return
        }
        if (musicMode) {
            locomotion = Locomotion.STROLL
            freeIdleUntil = 0L
            beginWalkBurst(music = true)
            syncModeBucket()
            return
        }
        returnToFreeIfIdle(startWalk = true)
    }

    /** 刷视频 / 玩游戏姿势被走动或表情盖掉后，强制切回场景立绘。 */
    private fun reassertSceneSprite() {
        when {
            appGameMode -> {
                stopLocomotion()
                locomotion = Locomotion.NONE
                animator.forceSceneMode(PetAnimator.Mode.PLAY_GAME)
            }
            videoMode -> {
                stopLocomotion()
                locomotion = Locomotion.NONE
                animator.forceSceneMode(PetAnimator.Mode.WATCH_VIDEO)
            }
            musicMode -> {
                val m = animator.currentMode()
                if (m != PetAnimator.Mode.MUSIC_WALK && m != PetAnimator.Mode.MUSIC_STAND) {
                    beginWalkBurst(music = true)
                }
            }
        }
        syncModeBucket()
    }

    fun syncHeadFlower() {
        fx?.setWearFlower(PetProfileStore.wearingFlower(context))
    }

    fun syncOutfit() {
        val list = OutfitStore.load(context)
        // 烘焙进立绘，避免特效层在宠身后被挡住
        animator.syncOutfit(list)
        fx?.syncOutfit(emptyList())
    }

    fun openOutfitEditor() {
        OutfitEditorUi.show(context) { syncOutfit() }
    }

    /** 全屏游戏时隐藏伴侣/气泡/道具等 overlay 子窗。 */
    fun setOverlayChromeVisible(visible: Boolean) {
        companion?.setVisible(visible)
        speech?.setVisible(visible)
        fx?.setVisible(visible)
        companionFx?.setVisible(visible && companion?.active == true)
        if (!visible) {
            workProps?.clear()
        }
    }

    private var hungerJob: Runnable? = null
    private var lastHungerMs = 0L

    private fun startHungerPoll() {
        stopHungerPoll()
        hungerJob = object : Runnable {
            override fun run() {
                maybeHungerReminder()
                mainHandler.postDelayed(this, 45_000L)
            }
        }
        mainHandler.postDelayed(hungerJob!!, 20_000L)
    }

    private fun stopHungerPoll() {
        hungerJob?.let { mainHandler.removeCallbacks(it) }
        hungerJob = null
    }

    private fun maybeHungerReminder() {
        if (musicMode || isQuiet) return
        if (AppDataStore.stamina(context) > 30) return
        val now = android.os.SystemClock.elapsedRealtime()
        if (now - lastHungerMs < 120_000L) return
        lastHungerMs = now
        showToast("肚子饿了，去模式→游戏接食物，再来喂我吧！")
        if (voice?.voiceEnabled() == true && voice?.hasCategory("hungry") == true) {
            voice?.playCategory("hungry", force = true, chain = false)
        }
    }

    private fun syncModeBucket() {
        val key = when {
            isCollecting || appGameMode -> "game"
            videoMode -> "video"
            musicMode -> "music"
            isWorking || isPomodoro -> "work"
            isFollowing -> "follow"
            isQuiet -> "quiet"
            locomotion == Locomotion.STROLL -> "stroll"
            locomotion == Locomotion.FREE -> "free"
            else -> "free"
        }
        ModeTimeStore.setBucket(context, key)
        publishLockScreenPose()
    }

    private fun publishLockScreenPose() {
        val pose = LockScreenPetStore.resolve(
            video = videoMode,
            game = appGameMode,
            music = musicMode,
            quiet = isQuiet,
        )
        LockScreenPetStore.setPose(context, pose)
        onLockScreenPoseChanged?.invoke()
    }

    fun destroy() {
        endUserInteractHold()
        stopMetaIdlePoll()
        stopHungerPoll()
        clearWorkTimer()
        clearSleepInteract()
        ModeTimeStore.flush(context)
        ModeTimeStore.setBucket(context, null)
        stopAmbientMusicWatch()
        stopFreeIdlePulse()
        cancelMusicAffinityTick()
        abortAllModes()
        companion?.stop()
        companion = null
        musicPlayer?.stop()
        musicPlayer = null
        voice?.stop()
        voice = null
        speech?.destroy()
        speech = null
        fx?.destroy()
        fx = null
        companionFx?.destroy()
        companionFx = null
        workProps?.destroy()
        workProps = null
        toolClock?.destroy()
        toolClock = null
        stopCollect(resumeFree = false)
        removeQuietHud()
        removePomoHud()
        removeFollowCatcher()
    }

    fun noteUserActivity() {
        lastUserActivityMs = android.os.SystemClock.elapsedRealtime()
        speech?.reposition()
    }

    /**
     * 长拖 yuqi：对照 `_maybe_drag_move_voice`。
     * @return 是否触发了语音/台词
     */
    fun onDragHeld(elapsedMs: Long): Boolean {
        noteUserActivity()
        if (elapsedMs < DRAG_MOVE_VOICE_AFTER_MS) return false
        if (isWorking || isQuiet) return false
        val now = android.os.SystemClock.elapsedRealtime()
        if (lastDragYuqiMs > 0L && now - lastDragYuqiMs < DRAG_MOVE_VOICE_RETRY_MS) return false
        lastDragYuqiMs = now
        if (musicMode) return false
        if (maybeMetaBanter("drag_long")) return true
        if (voice?.playCategory("yuqi", force = true) == true) {
            // 有中文台词才弹字幕；英文资源名已在 VoiceTitle 里屏蔽
            return true
        }
        speak(InteractLines.DRAG_DIZZY.random(), holdMs = 2400L)
        return true
    }

    fun resetDragYuqiSession() {
        lastDragYuqiMs = 0L
    }

    /** 台词气泡；对齐桌面：关声打字机；开语音可 50/50；强制类强制播。 */
    private fun speak(
        text: String,
        voiceCat: String? = null,
        holdMs: Long = 2800L,
        forceVoice: Boolean = false,
        typewriterMs: Long = SpeechBubbleUi.TYPEWRITER_MS,
        hiTypewriter: Boolean = false,
        pick5050: Boolean = false,
    ) {
        if (musicMode && voiceCat != null) {
            if (text.isNotBlank()) speech?.showTypewriter(text, holdMs.coerceAtLeast(1L), typewriterMs)
            return
        }
        voice?.musicBlocked = musicMode
        val cat = voiceCat
        val force = forceVoice || cat in setOf("hi", "call", "kick", "eat", "sleep", "work", "dizzy", "yuqi", "hungry")
        when (cat) {
            "hi" -> {
                val played = voice?.playHi {} == true
                // 对照桌面：播语音时用文件名解析的标题框，不覆盖成互动文案
                if (!played && text.isNotBlank()) {
                    if (hiTypewriter) speech?.showHiTypewriter(text, holdMs.coerceAtLeast(4200L))
                    else speech?.showTypewriter(text, holdMs, typewriterMs)
                }
                return
            }
            "call" -> {
                val played = voice?.playCall(
                    onRingStart = { speech?.hide() },
                    onLineStart = { /* 台词字幕由 VoicePlayer.emitSubtitle 负责 */ },
                ) == true
                if (!played && text.isNotBlank()) {
                    speech?.showTypewriter(text, holdMs, typewriterMs)
                }
                return
            }
            null, "" -> {
                if (text.isNotBlank()) {
                    if (typewriterMs > 0) speech?.showTypewriter(text, holdMs, typewriterMs)
                    else speech?.show(text, holdMs)
                }
                return
            }
            else -> {
                // D09：开语音且非强制 → 语音框与打字框 50/50
                val tryVoiceFirst = force || (
                    pick5050 &&
                        voice?.voiceEnabled() == true &&
                        voice?.hasCategory(cat) == true &&
                        kotlin.random.Random.nextFloat() < 0.5f
                    )
                if (tryVoiceFirst) {
                    val played = voice?.playCategory(cat, force = force, chain = !force) == true
                    // 播中则保留 VoiceTitle 字幕（如「我开动了」），不再盖成 banter
                    if (played) return
                }
                if (text.isNotBlank()) {
                    speech?.showTypewriter(text, holdMs, typewriterMs)
                } else if (!tryVoiceFirst && voice?.hasCategory(cat) == true) {
                    voice?.playCategory(cat, force = force, chain = !force)
                }
            }
        }
    }

    private fun banter(key: String, voiceCat: String? = null, allowBanter: Boolean = true) {
        if (musicMode) return
        if (!allowBanter) return
        val line = InteractLines.line(key)
        if (line.isBlank() && voiceCat == null) return
        val force = voiceCat in setOf("kick", "eat", "sleep", "work", "dizzy", "hungry")
        // 表情类走 50/50；强制类强制播
        val pick = !force && voiceCat != null
        speak(line, voiceCat, forceVoice = force, pick5050 = pick)
    }

    /** 部位点击感叹音（开语音）。 */
    fun tryInterjection(part: String): Boolean {
        if (musicMode || isQuiet) return false
        return voice?.playInterjection(part) == true
    }

    /** 拖拽落地：对照 MOVE_LAND_MS，整体下移后回站。 */
    fun playLandSettle(setY: (Int) -> Unit) {
        val size = petSize()
        val landPx = size / 3
        val base = petTopLeft()
        setY(base.y + landPx)
        animator.setMode(PetAnimator.Mode.STAND)
        mainHandler.postDelayed({
            val now = petTopLeft()
            // 保持落地后的 y（桌面 settle 不弹回）
            setY(now.y)
        }, 160L)
    }

    fun abortAllModes() {
        suppressResumeFree = true
        try {
            endMusic(silent = true)
            endVideoMode(silent = true)
            endAppGameMode(silent = true)
            endPomodoro(silent = true)
            stopWorkSilent()
            endFollow(silent = true)
            stopQuietSilent()
            clearSleepInteract()
            stopCollect(resumeFree = false)
            locomotion = Locomotion.NONE
            walkStepsLeft = 0
            fx?.clearBurst()
            fx?.setMusicWave(false)
            companionFx?.setMusicWave(false)
            fx?.clearSleepZzz()
        } finally {
            suppressResumeFree = false
        }
        // 不在此处 sync / returnToFree：调用方会设新模式；destroy 已 flush
    }

    fun startFree() {
        abortAllModes()
        locomotion = Locomotion.FREE
        freeIdleUntil = 0L
        beginWalkBurst(music = false)
        syncModeBucket()
    }

    fun startStroll() {
        abortAllModes()
        locomotion = Locomotion.STROLL
        freeIdleUntil = 0L
        beginWalkBurst(music = false)
        syncModeBucket()
    }

    /** 暂停走动（拖拽/表情），不退出当前 locomotion 身份。 */
    fun stopLocomotion() {
        walkStepsLeft = 0
        freeIdleUntil = Long.MAX_VALUE / 4
    }

    /** 移动时钟回调：返回 true 表示本帧应位移。 */
    fun onWalkAnimStep(): Boolean {
        // 菜单互动/随机动作进行中：禁止走动与站立随机
        if (idleActionBusy) return false
        if (videoMode || appGameMode) {
            reassertSceneSprite()
            return false
        }
        if (!locomotionEnabled) return false
        val now = android.os.SystemClock.elapsedRealtime()
        if (now < freeIdleUntil) return false

        if (musicMode) {
            if (animator.currentMode() != PetAnimator.Mode.MUSIC_WALK) {
                beginWalkBurst(music = true)
            }
            if (walkStepsLeft <= 0) {
                // 站立略长，配合音乐轻弹（对照桌面 music stand bobble）
                val wait = Random.nextLong(2800, 5200)
                freeIdleUntil = now + wait
                animator.setMode(PetAnimator.Mode.MUSIC_STAND)
                mainHandler.postDelayed({
                    if (musicMode && locomotionEnabled &&
                        android.os.SystemClock.elapsedRealtime() >= freeIdleUntil
                    ) {
                        beginWalkBurst(music = true)
                    }
                }, wait + 16L)
                return false
            }
            walkStepsLeft--
            fx?.syncPlace()
            companionFx?.syncPlace()
            if (videoPlaying) parkPetAwayFromCenter(force = false)
            return true
        }

        when (locomotion) {
            Locomotion.FREE, Locomotion.STROLL -> {
                if (walkStepsLeft <= 0) {
                    if (idleActionBusy) return false
                    var wait = if (locomotion == Locomotion.FREE) {
                        Random.nextLong(800, 2200)
                    } else {
                        Random.nextLong(500, 1400)
                    }
                    if (locomotion == Locomotion.FREE && tryStandIdleRandom()) {
                        wait = Random.nextLong(700, 2000)
                    }
                    freeIdleUntil = now + wait
                    if (!idleActionBusy) animator.setMode(PetAnimator.Mode.STAND)
                    mainHandler.postDelayed({
                        if (locomotionEnabled && !idleActionBusy &&
                            android.os.SystemClock.elapsedRealtime() >= freeIdleUntil
                        ) {
                            beginWalkBurst(music = false)
                        }
                    }, wait + 16L)
                    if (videoPlaying) parkPetAwayFromCenter(force = false)
                    return false
                }
                if (animator.currentMode() != PetAnimator.Mode.WALK) {
                    animator.setMode(PetAnimator.Mode.WALK)
                }
                walkStepsLeft--
                fx?.syncPlace()
                speech?.reposition()
                if (videoPlaying) parkPetAwayFromCenter(force = false)
                return true
            }
            else -> return false
        }
    }

    private fun beginWalkBurst(music: Boolean) {
        animator.resetWalkTurnGuard()
        walkStepsLeft = if (music) Random.nextInt(40, 101) else Random.nextInt(70, 181)
        animator.setWalkDir(SpriteAssets.Dir.random())
        animator.setMode(if (music) PetAnimator.Mode.MUSIC_WALK else PetAnimator.Mode.WALK)
    }

    fun startFollow() {
        if (isFollowing) {
            endFollow(silent = false)
            return
        }
        abortAllModes()
        animator.resetWalkTurnGuard()
        val eng = FollowEngine(object : FollowEngine.Host {
            override fun screenSize() = this@PetModeHub.screenSize()
            override fun petSize() = this@PetModeHub.petSize()
            override fun petTopLeft() = this@PetModeHub.petTopLeft()
            override fun setPetTopLeft(x: Int, y: Int) = this@PetModeHub.setPetTopLeft(x, y)
            override fun onFollowWalk(walking: Boolean) {
                if (walking) {
                    // driveMove=false：只切走路立绘，位移由 FollowEngine 负责
                    if (animator.currentMode() != PetAnimator.Mode.WALK) {
                        animator.setMode(PetAnimator.Mode.WALK, driveMove = false)
                    }
                } else {
                    animator.setMode(PetAnimator.Mode.STAND)
                }
            }
            override fun onFollowDir(dir: SpriteAssets.Dir) {
                animator.setWalkDir(dir)
            }
            override fun onDizzy() {
                animator.playPose(listOf(SpriteAssets.STAND), FollowEngine.FOLLOW_DIZZY_STAND_MS)
                fx?.showDizzy()
                speak(InteractLines.FOLLOW_DIZZY_TEXT, "dizzy", 3000L, forceVoice = true)
            }
            override fun toast(msg: String) = showToast(msg)
        })
        followEngine = eng
        eng.start()
        installFollowCatcher()
        showToast("跟随中 · 再点「跟随」可结束 · 点空白处引路")
        syncModeBucket()
    }

    /** 菜单「跟随」开关：开→跟随，关→自由。 */
    fun toggleFollow() {
        if (isFollowing) endFollow(silent = false)
        else startFollow()
    }

    fun endFollow(silent: Boolean = false) {
        if (followEngine == null && !silent) {
            showToast("当前未在跟随")
            return
        }
        followEngine?.stop()
        followEngine = null
        removeFollowCatcher()
        if (!silent) {
            showToast("结束跟随 · 回到自由")
            returnToFreeIfIdle(startWalk = true)
        } else {
            syncModeBucket()
        }
    }

    fun startQuiet() {
        if (!isPomodoro) abortAllModes()
        else {
            stopWorkSilent()
            endFollow(silent = true)
            locomotion = Locomotion.NONE
            stopQuietSilent()
        }
        clearSleepInteract()
        launchQuiet()
    }

    /** 互动→睡眠：sleep1→sleep2，对照 SLEEP_INTERACT_MS=30s 后自动醒。 */
    fun startSleepInteract() {
        abortAllModes()
        clearSleepInteract()
        animator.setMode(PetAnimator.Mode.SLEEP_PEEK)
        fx?.setSleepZzz(false)
        banter("sleep", "sleep")
        showToast("小憩 30 秒…")
        mainHandler.postDelayed({
            if (sleepInteractJob == null) return@postDelayed
            animator.setMode(PetAnimator.Mode.SLEEP)
            fx?.setSleepZzz(true)
        }, QuietSession.ENTER_TRANSITION_MS)
        sleepInteractJob = Runnable {
            sleepInteractJob = null
            animator.setMode(PetAnimator.Mode.SLEEP_PEEK)
            fx?.setSleepZzz(false)
            mainHandler.postDelayed({
                showToast("睡醒了")
                returnToFreeIfIdle(startWalk = true)
            }, QuietSession.ENTER_TRANSITION_MS)
        }
        mainHandler.postDelayed(sleepInteractJob!!, 30_000L)
        ModeTimeStore.setBucket(context, "quiet")
    }

    private var sleepInteractJob: Runnable? = null

    private fun clearSleepInteract() {
        sleepInteractJob?.let { mainHandler.removeCallbacks(it) }
        sleepInteractJob = null
        fx?.setSleepZzz(false)
    }

    /** 改大小：像素加载溶解（H-SIZE）。 */
    fun playSizeDissolve(onDone: (() -> Unit)? = null) {
        animator.playDissolve(reverse = false) { onDone?.invoke() }
    }

    /**
     * 桌宠与智能伴侣一并改大小（对照桌面改档后 `_resync_mini_pets_size`）。
     * 设置页滑条 / 菜单小中大 / 房间模式按钮共用。
     */
    fun applyDisplaySizeToPetAndCompanion() {
        // 显式读 prefs，避免 animator 缓存的旧边长卡住主宠
        animator.applyDisplaySize(PetPrefs.sizePx(context))
        companion?.refreshSprite(forceReload = true)
        // 伴侣窗尺寸变了：重建伴侣特效层，避免声波/特效仍按旧尺寸
        if (companion?.active == true) {
            val waveOn = musicMode
            val waveColors = if (waveOn) {
                if (musicAmbientOnly) BundledMusic.waveColorsForSignature(ambientMusicSignature)
                else BundledMusic.waveColorsForTrack(currentMusicTrack)
            } else {
                null
            }
            rebuildCompanionFx()
            if (waveOn && waveColors != null) {
                companionFx?.setMusicWave(true, waveColors)
            }
            companion?.setVisible(true)
            companionFx?.setVisible(true)
        }
        fx?.syncPlace()
        companionFx?.syncPlace()
        speech?.reposition()
        restackDisplayLayers()
    }

    /** 设置「字体大小」变更后刷新悬浮层已开 UI。 */
    fun applyFontScaleToOverlay() {
        toolClock?.refreshFonts()
        speech?.refreshFontScale()
        val b = pomoHud
        if (b != null) {
            val btnSp = AppDataStore.fontClockBtnSp(context)
            b.pomoProgress.setTextSize(
                android.util.TypedValue.COMPLEX_UNIT_SP,
                AppDataStore.fontCaptionSp(context),
            )
            b.pomoPlay.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, btnSp)
            b.pomoPause.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, btnSp)
            b.pomoEnd.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, btnSp)
            b.pomoClockDecor.applyFontScale(context)
        }
    }

    private fun launchQuiet() {
        val q = QuietSession(object : QuietSession.Host {
            override fun onQuietVisual(peek: Boolean) {
                animator.setQuietPeek(peek)
                fx?.setSleepZzz(!peek)
            }
            override fun onQuietTick(elapsedSec: Long) {
                if (!isPomodoro) {
                    quietHud?.quietProgress?.text = "睡眠 ${QuietSession.formatDuration(elapsedSec)}"
                }
            }
            override fun onQuietEnded(elapsedSec: Long) {
                removeQuietHud()
                fx?.clearSleepZzz()
                quiet = null
                if (!isPomodoro) returnToFreeIfIdle(startWalk = true)
            }
            override fun toast(msg: String) {
                if (!isPomodoro) showToast(msg)
            }
        })
        quiet = q
        if (!isPomodoro) {
            ensureQuietHud()
            banter("sleep", "sleep")
        }
        q.start(announce = !isPomodoro)
        syncModeBucket()
    }

    fun endQuiet(fromMenu: Boolean) {
        if (isPomodoro && fromMenu) {
            endPomodoro(silent = false)
            return
        }
        val q = quiet ?: run {
            if (fromMenu) showToast("当前未在睡眠")
            return
        }
        if (!q.active) {
            quiet = null
            if (fromMenu) showToast("当前未在睡眠")
            return
        }
        // endFromMenu 自带醒来过渡；stop 用于内部打断
        if (fromMenu) {
            q.endFromMenu()
        } else {
            q.stop()
            quiet = null
            removeQuietHud()
            fx?.clearSleepZzz()
            if (!isPomodoro) returnToFreeIfIdle(startWalk = true)
            else syncModeBucket()
            return
        }
        quiet = null
        // onQuietEnded 里会 returnToFree；此处只清 HUD，zzZ 由醒来立绘控制
        removeQuietHud()
    }

    fun peekQuiet() {
        quiet?.peek()
    }

    fun startWorkFree() = startWork(continuous = true, total = 5, fromPomo = false, timedMs = 0L)

    fun startWorkBoxes(n: Int) = startWork(continuous = false, total = n, fromPomo = false, timedMs = 0L)

    fun startWorkTimed(durationMs: Long) =
        startWork(continuous = true, total = 5, fromPomo = false, timedMs = durationMs.coerceAtLeast(1000L))

    private fun startWork(continuous: Boolean, total: Int, fromPomo: Boolean, timedMs: Long = 0L) {
        clearWorkTimer()
        if (!fromPomo) abortAllModes()
        else {
            endFollow(silent = true)
            stopQuietSilent()
            locomotion = Locomotion.NONE
            stopWorkSilent()
        }
        workShowEndButton = continuous && timedMs <= 0L && !fromPomo
        workContinuousSession = continuous
        // 进入运送时确保旗/箱可见开关为开（避免上次关掉后“看不见道具”）
        AppDataStore.setWorkShowProps(context, true)
        AppDataStore.setWorkShowStack(context, true)
        val eng = WorkEngine(
            host = object : WorkEngine.Host {
                override fun screenSize() = this@PetModeHub.screenSize()
                override fun petSize() = this@PetModeHub.petSize()
                override fun petTopLeft() = this@PetModeHub.petTopLeft()
                override fun setPetTopLeft(x: Int, y: Int) {
                    this@PetModeHub.setPetTopLeft(x, y)
                    speech?.reposition()
                }
                override fun onWorkVisual(carrying: Boolean, useWorkSprites: Boolean) {
                    when {
                        useWorkSprites -> {
                            if (animator.currentMode() != PetAnimator.Mode.WORK_WALK) {
                                animator.setMode(PetAnimator.Mode.WORK_WALK)
                            }
                        }
                        workEngine?.active == true -> {
                            if (animator.currentMode() != PetAnimator.Mode.WALK) {
                                animator.setMode(PetAnimator.Mode.WALK, driveMove = false)
                            }
                        }
                        else -> animator.setMode(PetAnimator.Mode.STAND)
                    }
                }
                override fun onWorkDir(dir: SpriteAssets.Dir) {
                    animator.setWalkDir(dir)
                }
                override fun onProps(
                    startBoxVisible: Boolean,
                    flagX: Int, flagY: Int, startX: Int, startY: Int, stack: Int,
                ) {
                    workProps?.updateProps(startBoxVisible, flagX, flagY, startX, startY, stack)
                }
                override fun onProgress(delivered: Int, total: Int, continuous: Boolean) {
                    if (!isPomodoro) {
                        workProps?.showHud(delivered, total, continuous, workShowEndButton)
                    }
                }
                override fun onWorkFinished(delivered: Int, continuousEnd: Boolean) {
                    workEngine = null
                    workProps?.clear()
                    clearWorkTimer()
                    clearWorkBanter()
                    if (delivered > 0) AppDataStore.unlock(context, "work_done")
                    if (!isPomodoro) returnToFreeIfIdle(startWalk = true)
                }
                override fun toast(msg: String) {
                    if (!isPomodoro) showToast(msg)
                }
                override fun onFlagMovedFar() {
                    maybeMetaBanter("work_flag", forceChance = 0.32f)
                }
                override fun onBoxDelivered() {
                    AppDataStore.addStaminaMood(context, 2, 1)
                    val n = WalletStore.noteWorkBoxDelivered(context)
                    if (n > 0 && !isPomodoro) {
                        showToast("工作宝箱 +$n（累计每 25 箱）")
                    }
                }
                override fun onWorkVoiceTick() {
                    // 对照 _try_voice_work：步进抽检；优先 work 语音，否则台词气泡
                    if (Random.nextFloat() >= VOICE_WORK_RANDOM_CHANCE) return
                    if (voice?.playing() == true) return
                    triggerWorkBanter(fromStep = true)
                }
            },
            continuous = continuous,
            total = total,
        )
        workEngine = eng
        eng.start()
        if (!fromPomo) {
            speak(InteractLines.WORK_MODE.random(), "work", 3200L)
        }
        if (continuous) scheduleWorkBanter()
        if (timedMs > 0L) {
            workShowEndButton = false
            workProps?.showHud(0, total, continuous = true, showEndButton = false)
            workTimerJob = Runnable {
                if (workEngine?.active == true) {
                    endWork(fromMenu = false)
                    showToast("工作定时到！")
                }
            }
            mainHandler.postDelayed(workTimerJob!!, timedMs)
        }
        syncModeBucket()
    }

    fun endWork(fromMenu: Boolean) {
        clearWorkTimer()
        clearWorkBanter()
        if (isPomodoro && fromMenu) {
            endPomodoro(silent = false)
            return
        }
        val eng = workEngine ?: run {
            if (fromMenu) showToast("当前未在运送")
            return
        }
        if (!eng.active) {
            workEngine = null
            if (fromMenu) showToast("当前未在运送")
            return
        }
        if (fromMenu) eng.endFromMenu() else eng.stop()
        workEngine = null
        if (!isPomodoro) returnToFreeIfIdle(startWalk = true)
        else syncModeBucket()
    }

    private fun stopWorkSilent() {
        clearWorkTimer()
        clearWorkBanter()
        workEngine?.stop(internal = true)
        workEngine = null
        workProps?.clear()
    }

    private fun stopQuietSilent() {
        quiet?.stop(internal = true)
        quiet = null
        removeQuietHud()
        fx?.clearSleepZzz()
    }

    // —— 番茄钟 ——

    fun startPomodoro(workMin: Int, restMin: Int) {
        if (isPomodoro) {
            endPomodoro(silent = false)
            return
        }
        abortAllModes()
        ensurePomoHud()
        val session = PomodoroSession(object : PomodoroSession.Host {
            override fun onPomoWorkStart(round: Int, workMs: Long) {
                startWork(continuous = true, total = 5, fromPomo = true)
                updatePomoClock(
                    title = "番茄·工作 ·第${round}轮",
                    remainMs = workMs,
                    totalMs = workMs,
                    style = DeskClockDecorView.WalkerStyle.WORK,
                    subtitle = "工作 ${PomodoroSession.formatRemain(workMs)}",
                    paused = false,
                )
            }
            override fun onPomoRestStart(round: Int, restMs: Long) {
                stopWorkSilent()
                workProps?.clear()
                launchQuiet()
                updatePomoClock(
                    title = "番茄·休息 ·第${round}轮",
                    remainMs = restMs,
                    totalMs = restMs,
                    style = DeskClockDecorView.WalkerStyle.SLEEP,
                    subtitle = "休息 ${PomodoroSession.formatRemain(restMs)}",
                    paused = false,
                )
            }
            override fun onPomoTick(
                phase: String,
                round: Int,
                remainMs: Long,
                phaseTotalMs: Long,
                paused: Boolean,
            ) {
                val work = phase != "rest"
                val phaseLabel = if (work) "工作" else "休息"
                updatePomoClock(
                    title = if (work) "番茄·工作 ·第${round}轮" else "番茄·休息 ·第${round}轮",
                    remainMs = remainMs,
                    totalMs = phaseTotalMs,
                    style = if (work) DeskClockDecorView.WalkerStyle.WORK else DeskClockDecorView.WalkerStyle.SLEEP,
                    subtitle = if (paused) {
                        "$phaseLabel ${PomodoroSession.formatRemain(remainMs)} · 暂停"
                    } else {
                        "$phaseLabel ${PomodoroSession.formatRemain(remainMs)}"
                    },
                    paused = paused,
                )
            }
            override fun onPomoRoundDone(completed: Int, nextRound: Int) {
                stopQuietSilent()
                AppDataStore.unlock(context, "pomo_done")
            }
            override fun onPomoEnded(completed: Int) {
                stopWorkSilent()
                stopQuietSilent()
                removePomoHud()
                returnToFreeIfIdle(startWalk = true)
            }
            override fun toast(msg: String) = showToast(msg)
        })
        pomo = session
        session.start(workMin, restMin)
    }

    private fun updatePomoClock(
        title: String,
        remainMs: Long,
        totalMs: Long,
        style: DeskClockDecorView.WalkerStyle,
        subtitle: String,
        paused: Boolean,
    ) {
        val b = pomoHud ?: return
        b.pomoProgress.text = subtitle
        b.pomoClockDecor.apply {
            applyFontScale(context)
            titleText = if (paused) "$title · 暂停" else title
            timeText = ToolClockUi.formatClockMs(remainMs)
            // 绕圈用已走时间，与计时器一致，避免倒走
            progressMs = (totalMs - remainMs).coerceAtLeast(0L)
            walkerStyle = style
            accentArgb = if (style == DeskClockDecorView.WalkerStyle.SLEEP) {
                0xFF88AADD.toInt()
            } else {
                0xFFFFCC66.toInt()
            }
        }
    }

    fun endPomodoro(silent: Boolean) {
        val s = pomo ?: return
        if (!s.active) {
            pomo = null
            removePomoHud()
            return
        }
        if (silent) s.stop(internal = true) else s.endFromMenu()
        pomo = null
        stopWorkSilent()
        stopQuietSilent()
        removePomoHud()
        if (!silent) returnToFreeIfIdle(startWalk = true)
    }

    fun showStopwatch() = toolClock?.toggleStopwatch()
    fun showTimer(minutes: Int) = toolClock?.showTimer(minutes)
    fun showTimerMs(durationMs: Long) = toolClock?.showTimerMs(durationMs)

    fun openTimerSetup() {
        TimeSetupDialogs.showTimerSetup(context) { ms -> showTimerMs(ms) }
    }

    fun openPomodoroSetup() {
        if (isPomodoro) {
            endPomodoro(silent = false)
            return
        }
        TimeSetupDialogs.showPomodoroSetup(context) { w, r -> startPomodoro(w, r) }
    }

    fun openWorkCustomSetup() {
        if (isWorking) {
            endWork(fromMenu = true)
            return
        }
        TimeSetupDialogs.showWorkCustomSetup(
            context,
            onBoxes = { n -> startWorkBoxes(n) },
            onTimed = { ms -> startWorkTimed(ms) },
        )
    }

    fun openScheduleSetup() {
        ScheduleBirthdayDialogs.showSchedule(context)
    }

    fun openBirthdaySetup() {
        ScheduleBirthdayDialogs.showBirthday(context)
    }

    fun openVoiceVolumeSetup() {
        TimeSetupDialogs.showVolumeSetup(context, voice = true)
    }

    fun openSfxVolumeSetup() {
        TimeSetupDialogs.showVolumeSetup(context, voice = false)
    }

    /**
     * 模式菜单 → 音乐：优先播导入本地曲，否则内置默认曲 + 音乐立绘漫步 + 声波颜色。
     * （音乐 App 触发见 [enterMusicAmbient]，只切动画、不播本地曲。）
     */
    fun startMusic() {
        if (musicMode) {
            endMusic(silent = false)
            return
        }
        val importedUri = PetProfileStore.musicUri(context)
        val importedTitle = PetProfileStore.musicTitle(context).ifBlank { "导入曲" }
        val bundled = BundledMusic.defaultTrack(context)
        if (importedUri.isNullOrBlank() && bundled == null) {
            showToast("未找到可播歌曲（请导入本地曲或检查内置曲）")
            return
        }
        abortAllModes()
        musicMode = true
        musicAmbientOnly = false
        ambientMusicSignature = ""
        voice?.musicBlocked = true
        voice?.stop()
        locomotion = Locomotion.STROLL
        freeIdleUntil = 0L
        beginWalkBurst(music = true)
        AppDataStore.unlock(context, "music_play")
        val onPlayError: (String) -> Unit = {
            clearMusicWave()
            showToast(it)
            endMusic(silent = true)
        }
        if (!importedUri.isNullOrBlank()) {
            currentMusicTrack = null
            musicAffinityCharId = "aoba"
            musicPlayer?.playUri(
                android.net.Uri.parse(importedUri),
                onError = onPlayError,
            )
            if (musicPlayer?.playing == true) {
                applyMusicWave(BundledMusic.waveColorsForFolder(BundledMusic.DEFAULT_FOLDER))
            }
            toolClock?.showMusicAutoStopwatch()
            startMusicAffinityTick()
            showToast("音乐漫步 · $importedTitle")
            syncModeBucket()
            return
        }
        currentMusicTrack = bundled
        musicAffinityCharId = bundled!!.charId
        musicPlayer?.playAsset(
            bundled.assetPath,
            loop = true,
            onError = onPlayError,
        )
        if (musicPlayer?.playing == true) {
            applyMusicWave(BundledMusic.waveColorsForTrack(bundled))
        }
        toolClock?.showMusicAutoStopwatch()
        startMusicAffinityTick()
        showToast("音乐漫步 · ${bundled.title}")
        syncModeBucket()
    }

    /**
     * 音乐 App 触发：只切音乐立绘/漫步动画与声波颜色，不播桌宠本地曲。
     * 切歌时签名变化 → 换背景声波颜色。
     */
    private fun enterMusicAmbient(fromStartup: Boolean, signature: String = "") {
        if (musicMode) {
            if (musicAmbientOnly) {
                musicPlayer?.stop()
                ambientMusicSignature = signature.ifBlank { ambientMusicSignature }
                applyMusicWave(BundledMusic.waveColorsForSignature(ambientMusicSignature))
                val m = animator.currentMode()
                if (m != PetAnimator.Mode.MUSIC_WALK && m != PetAnimator.Mode.MUSIC_STAND) {
                    locomotion = Locomotion.STROLL
                    freeIdleUntil = 0L
                    beginWalkBurst(music = true)
                }
            }
            return
        }
        if (isWorking || isFollowing || isQuiet || isPomodoro || isCollecting) return
        if (videoMode || appGameMode) {
            endVideoMode(silent = true)
            endAppGameMode(silent = true)
        }
        abortAllModes()
        musicMode = true
        musicAmbientOnly = true
        currentMusicTrack = null
        musicAffinityCharId = "aoba"
        // 绝不播本地 BGM，只跟外部音乐 App
        musicPlayer?.stop()
        voice?.musicBlocked = true
        voice?.stop()
        locomotion = Locomotion.STROLL
        freeIdleUntil = 0L
        beginWalkBurst(music = true)
        ambientMusicSignature = signature
        AppDataStore.unlock(context, "music_play")
        applyMusicWave(BundledMusic.waveColorsForSignature(signature))
        toolClock?.showMusicAutoStopwatch()
        showToast(
            if (fromStartup) "检测到音乐App · 音乐立绘（不播本地曲）"
            else "音乐App · 立绘漫步（切歌换色）",
        )
        syncModeBucket()
    }

    private fun applyMusicWave(colors: IntArray) {
        fx?.setMusicWave(true, colors)
        if (companion?.active == true) {
            companionFx?.setMusicWave(true, colors)
        } else {
            companionFx?.setMusicWave(false)
        }
    }

    private fun clearMusicWave() {
        fx?.setMusicWave(false)
        companionFx?.setMusicWave(false)
    }

    private fun startMusicAffinityTick() {
        cancelMusicAffinityTick()
        if (musicAmbientOnly) return
        musicAffinityJob = object : Runnable {
            override fun run() {
                if (!musicMode || musicAmbientOnly || musicPlayer?.playing != true) return
                MusicAffinityStore.addTick(context, musicAffinityCharId)
                musicAffinityJob?.let { mainHandler.postDelayed(it, MusicAffinityStore.TICK_MS) }
            }
        }
        mainHandler.postDelayed(musicAffinityJob!!, MusicAffinityStore.TICK_MS)
    }

    private fun cancelMusicAffinityTick() {
        musicAffinityJob?.let { mainHandler.removeCallbacks(it) }
        musicAffinityJob = null
    }

    fun endMusic(silent: Boolean) {
        if (!musicMode && musicPlayer?.playing != true) return
        musicMode = false
        musicAmbientOnly = false
        ambientMusicSignature = ""
        currentMusicTrack = null
        voice?.musicBlocked = false
        musicPlayer?.stop()
        clearMusicWave()
        cancelMusicAffinityTick()
        toolClock?.hideMusicAutoStopwatch()
        if (!silent) {
            showToast("结束音乐")
            returnToFreeIfIdle(startWalk = true)
        } else if (!suppressResumeFree) {
            returnToFreeIfIdle(startWalk = true)
        } else {
            syncModeBucket()
        }
    }

    private fun ambientMusicActiveExternal(): Boolean {
        if (musicPlayer?.playing == true) return false
        return AmbientMusicMonitor.isMediaActive(context)
    }

    private fun maybePromptUsageAccess() {
        if (AppSceneClassifier.hasUsageAccess(context)) return
        // 每次开宠都提醒：没有这项权限就检测不到「切到 B 站/网易云」
        mainHandler.postDelayed({
            if (AppSceneClassifier.hasUsageAccess(context)) return@postDelayed
            showToast("请授权「使用情况访问」：打开视频/音乐 App 才会自动切立绘（系统设置 → 特殊应用权限）")
            val prefs = context.getSharedPreferences("vpet_mobile", android.content.Context.MODE_PRIVATE)
            val lastOpen = prefs.getLong("usage_access_settings_opened_at", 0L)
            val now = System.currentTimeMillis()
            // 最多每天自动跳一次设置页，避免烦扰
            if (now - lastOpen > 20L * 60L * 60L * 1000L) {
                prefs.edit().putLong("usage_access_settings_opened_at", now).apply()
                AppSceneClassifier.openUsageAccessSettings(context)
            }
        }, 1600L)
    }

    private fun startAmbientMusicWatch() {
        stopAmbientMusicWatch()
        appSceneMonitor = AppSceneMonitor(context) { scene, signature ->
            mainHandler.post { onAppSceneChanged(scene, signature) }
        }.also { it.start() }
    }

    private fun stopAmbientMusicWatch() {
        appSceneMonitor?.stop()
        appSceneMonitor = null
    }

    private fun onAppSceneChanged(scene: AppScene, signature: String) {
        when (scene) {
            AppScene.VIDEO -> {
                suppressResumeFree = true
                try {
                    endAppGameMode(silent = true)
                } finally {
                    suppressResumeFree = false
                }
                enterVideoMode(signature)
            }
            AppScene.GAME -> {
                suppressResumeFree = true
                try {
                    endVideoMode(silent = true)
                } finally {
                    suppressResumeFree = false
                }
                enterAppGameMode(signature)
            }
            AppScene.MUSIC -> {
                suppressResumeFree = true
                try {
                    endVideoMode(silent = true)
                    endAppGameMode(silent = true)
                } finally {
                    suppressResumeFree = false
                }
                onAmbientMusicChanged(active = true, signature = signature)
            }
            AppScene.NONE -> {
                endVideoMode(silent = true)
                endAppGameMode(silent = true)
                onAmbientMusicChanged(active = false, signature = "")
            }
        }
    }

    private fun sceneBusy(): Boolean =
        isWorking || isFollowing || isQuiet || isPomodoro || isCollecting

    private var videoSignature: String = ""

    private fun enterVideoMode(signature: String) {
        if (sceneBusy()) return
        if (musicMode) {
            suppressResumeFree = true
            try {
                endMusic(silent = true)
            } finally {
                suppressResumeFree = false
            }
        }
        videoPlaying = true
        parkPetAwayFromCenter(force = true)
        val sigChanged = videoMode && signature.isNotEmpty() && signature != videoSignature
        videoSignature = signature
        if (videoMode) {
            if (sigChanged) {
                animator.rotateVideoPalette(signature)
            }
            animator.forceSceneMode(PetAnimator.Mode.WATCH_VIDEO)
            syncModeBucket()
            return
        }
        stopLocomotion()
        locomotion = Locomotion.NONE
        videoMode = true
        animator.setMode(PetAnimator.Mode.WATCH_VIDEO, driveMove = false)
        if (signature.isNotEmpty()) {
            animator.rotateVideoPalette(signature)
        }
        syncModeBucket()
        sceneToast("刷视频 · 看视频姿势")
    }

    /** 模式菜单 → 看视频：手动开关姿势（不依赖使用情况访问）。 */
    fun toggleVideoMode() {
        if (videoMode) {
            endVideoMode(silent = false)
            return
        }
        abortAllModes()
        enterVideoMode(signature = "menu")
    }

    private fun endVideoMode(silent: Boolean) {
        val was = videoMode || videoPlaying
        videoMode = false
        videoPlaying = false
        videoSignature = ""
        if (!was) return
        if (animator.currentMode() == PetAnimator.Mode.WATCH_VIDEO) {
            animator.setMode(PetAnimator.Mode.STAND, driveMove = false)
        }
        if (!silent) {
            sceneToast("结束刷视频姿势")
            returnToFreeIfIdle(startWalk = true)
        } else if (!suppressResumeFree) {
            returnToFreeIfIdle(startWalk = true)
        } else {
            syncModeBucket()
        }
    }

    private fun enterAppGameMode(@Suppress("UNUSED_PARAMETER") signature: String) {
        if (sceneBusy()) return
        if (musicMode) {
            suppressResumeFree = true
            try {
                endMusic(silent = true)
            } finally {
                suppressResumeFree = false
            }
        }
        if (appGameMode) {
            animator.forceSceneMode(PetAnimator.Mode.PLAY_GAME)
            syncModeBucket()
            return
        }
        stopLocomotion()
        locomotion = Locomotion.NONE
        appGameMode = true
        animator.setMode(PetAnimator.Mode.PLAY_GAME, driveMove = false)
        syncModeBucket()
        if (voice?.voiceEnabled() == true && voice?.hasCategory("game") == true) {
            voice?.playCategory("game", force = false, chain = true)
        }
        sceneToast("玩游戏 · 开玩姿势")
    }

    private fun endAppGameMode(silent: Boolean) {
        if (!appGameMode) return
        appGameMode = false
        if (animator.currentMode() == PetAnimator.Mode.PLAY_GAME) {
            animator.setMode(PetAnimator.Mode.STAND, driveMove = false)
        }
        if (!silent) {
            sceneToast("结束游戏姿势")
            returnToFreeIfIdle(startWalk = true)
        } else if (!suppressResumeFree) {
            returnToFreeIfIdle(startWalk = true)
        } else {
            syncModeBucket()
        }
    }

    private fun sceneToast(msg: String) {
        val now = android.os.SystemClock.elapsedRealtime()
        if (now - lastAppSceneToastMs < 2500L) return
        lastAppSceneToastMs = now
        showToast(msg)
    }

    private fun playHoldAllmate() {
        val resume = when {
            appGameMode -> PetAnimator.Mode.PLAY_GAME
            videoMode -> PetAnimator.Mode.WATCH_VIDEO
            musicMode -> PetAnimator.Mode.MUSIC_STAND
            isQuiet -> PetAnimator.Mode.SLEEP
            else -> PetAnimator.Mode.STAND
        }
        stopLocomotion()
        companion?.setVisible(false)
        companionFx?.setVisible(false)
        animator.playPose(
            frames = listOf(SpriteAssets.ALLMATE),
            holdMs = 3000L,
            resume = resume,
            loop = false,
        )
        mainHandler.postDelayed({
            if (companion?.active == true) {
                companion?.setVisible(true)
                companionFx?.setVisible(true)
            }
            restackDisplayLayers()
        }, 3050L)
        restackDisplayLayers()
        showToast("抱抱智能伴侣~")
    }

    /**
     * 看视频时尽量离开屏幕中央：落到左右下角安全区。
     * @param force 为 false 时仅在已处于中央才挪。
     */
    fun parkPetAwayFromCenter(force: Boolean = false) {
        if (!videoPlaying) return
        val scr = screenSize()
        val size = petSize()
        val p = petTopLeft()
        val cx = p.x + size / 2f
        val cy = p.y + size / 2f
        val inCenter =
            cx > scr.x * 0.22f && cx < scr.x * 0.78f &&
                cy > scr.y * 0.16f && cy < scr.y * 0.70f
        if (!inCenter) return
        val margin = (size * 0.12f).toInt().coerceAtLeast(10)
        val bottomPad = (scr.y * 0.05f).toInt().coerceAtLeast(8)
        val targetY = (scr.y - size - margin - bottomPad).coerceAtLeast(0)
        val leftX = margin
        val rightX = (scr.x - size - margin).coerceAtLeast(0)
        val targetX = if (cx < scr.x / 2f) leftX else rightX
        setPetTopLeft(targetX, targetY)
        fx?.syncPlace()
        companion?.refreshSprite()
        companionFx?.syncPlace()
        companion?.bringSpriteToFront()
    }

    /** 走动时：视频播放中把位置钳到边缘带，避免挡画面。 */
    fun clampPetForVideo(x: Int, y: Int, petW: Int, petH: Int): Point {
        val scr = screenSize()
        var nx = x.coerceIn(0, (scr.x - petW).coerceAtLeast(0))
        var ny = y.coerceIn(0, (scr.y - petH).coerceAtLeast(0))
        if (!videoPlaying) return Point(nx, ny)
        val cx = nx + petW / 2f
        val cy = ny + petH / 2f
        val centerL = scr.x * 0.28f
        val centerR = scr.x * 0.72f
        val centerT = scr.y * 0.18f
        val centerB = scr.y * 0.68f
        if (cx in centerL..centerR && cy in centerT..centerB) {
            val margin = (petW * 0.12f).toInt().coerceAtLeast(10)
            val bottomPad = (scr.y * 0.05f).toInt().coerceAtLeast(8)
            ny = (scr.y - petH - margin - bottomPad).coerceAtLeast(0)
            nx = if (cx < scr.x / 2f) margin else (scr.x - petW - margin).coerceAtLeast(0)
        }
        return Point(nx, ny)
    }

    private fun onAmbientMusicChanged(active: Boolean, signature: String) {
        if (active) {
            // 菜单音乐模式（正在播默认曲）优先，不被外部 App 打断
            if (musicMode && !musicAmbientOnly) return
            if (musicPlayer?.playing == true && !musicAmbientOnly) return
            if (isWorking || isFollowing || isQuiet || isPomodoro || isCollecting) return
            val trackChanged = musicMode && musicAmbientOnly &&
                signature.isNotEmpty() && signature != ambientMusicSignature
            if (!musicMode) {
                enterMusicAmbient(fromStartup = false, signature = signature)
            } else if (trackChanged) {
                ambientMusicSignature = signature
                musicPlayer?.stop()
                applyMusicWave(BundledMusic.waveColorsForSignature(signature))
            } else {
                ambientMusicSignature = signature
            }
        } else if (musicMode && musicAmbientOnly) {
            ambientMusicSignature = ""
            endMusic(silent = true)
        }
    }

    fun toggleCompanion() {
        val c = companion ?: return
        if (c.active) {
            c.stop()
            companionFx?.setMusicWave(false)
            companionFx?.destroy()
            companionFx = null
            AppDataStore.setCompanionEnabled(context, false)
            showToast("智能伴侣栏已关闭")
        } else {
            c.start()
            AppDataStore.setCompanionEnabled(context, true)
            rebuildCompanionFx()
            fx?.showHappy()
            voice?.playCompanionStart()
            AppDataStore.unlock(context, "companion_on")
            if (musicMode) {
                val wave = if (musicAmbientOnly) {
                    BundledMusic.waveColorsForSignature(ambientMusicSignature)
                } else {
                    BundledMusic.waveColorsForTrack(currentMusicTrack)
                }
                applyMusicWave(wave)
            }
            showToast("智能伴侣已开启。")
        }
    }

    /** 伴侣特效：悬浮时挂进伴侣同窗底层，保证声波在立绘后。 */
    private fun rebuildCompanionFx() {
        companionFx?.destroy()
        companionFx = null
        val c = companion ?: return
        if (!c.active && c.fxHost() == null && roomHost == null) return
        val nested = c.fxHost()
        companionFx = if (nested != null) {
            PetFxUi(
                context = context,
                windowManager = null,
                roomHost = nested,
                petTopLeft = { Point(PetFxUi.PAD, PetFxUi.PAD) },
                petSize = { c.displaySize() },
                raisePet = { c.bringSpriteToFront() },
            )
        } else {
            PetFxUi(
                context = context,
                windowManager = windowManager,
                roomHost = roomHost,
                petTopLeft = { c.displayTopLeft() },
                petSize = { c.displaySize() },
                raisePet = { restackDisplayLayers() },
            )
        }
    }

    /** 由 Overlay/Room 注入：先抬菜单等工具栏，再抬宠与伴侣。 */
    var raiseToolbars: (() -> Unit)? = null

    /**
     * 图层（底→顶）：工具栏 → 伴侣特效 → 桌宠特效=桌宠文本 → 伴侣立绘 → 桌宠立绘。
     * 游戏界面由 CollectOverlayUi 在 raisePets 之后自行抬到最上。
     */
    fun restackDisplayLayers() {
        raiseToolbars?.invoke()
        toolClock?.raiseLayer()
        companionFx?.raiseLayer()
        fx?.raiseLayer()
        speech?.raiseLayer()
        companion?.raise()
        companion?.bringSpriteToFront()
        raisePetOverlay?.invoke()
    }

    fun refreshCompanionSize() {
        companion?.refreshSprite(forceReload = true)
        companionFx?.syncPlace()
    }

    /** 退出：end 语音 + 像素溶解出场（A02/A03）；超时兜底。 */
    fun playExitThen(onDone: () -> Unit) {
        abortAllModes()
        ModeTimeStore.flush(context)
        ModeTimeStore.setBucket(context, null)
        var finished = false
        val finishOnce = Runnable {
            if (finished) return@Runnable
            finished = true
            onDone()
        }
        var voiceDone = false
        var animDone = false
        var companionDone = companion?.active != true
        fun tryFinish() {
            if (voiceDone && animDone && companionDone) mainHandler.post(finishOnce)
        }
        val played = voice?.playCategory("end", force = true, chain = false) {
            voiceDone = true
            tryFinish()
        } == true
        if (!played) {
            speak("一会儿见～", null, holdMs = 1200L)
            voiceDone = true
        }
        val totalMs = if (played) 2800L else (PixelDissolve.FRAME_MS * PixelDissolve.FRAMES)
        if (companion?.active == true) {
            companion?.playDissolve(reverse = true, totalMs = totalMs) {
                companionDone = true
                tryFinish()
            }
        }
        animator.playDissolve(reverse = true, totalMs = totalMs) {
            animDone = true
            tryFinish()
        }
        mainHandler.postDelayed(finishOnce, if (played) 8000L else 2500L)
    }

    fun openTools() = startActivity(ToolsActivity::class.java)

    fun openHome() = startActivity(HomeActivity::class.java)

    fun openRpg() {
        ModeTimeStore.setBucket(context, "game")
        startActivity(RpgActivity::class.java)
    }

    fun openPanel() = startActivity(PanelActivity::class.java)

    /** 互动→吃东西：对照 `_open_eat_food_menu`，从背包选食投喂。 */
    fun openEatFoodMenu() {
        if (musicMode) {
            showToast("音乐模式中暂不喂食")
            return
        }
        if (isCollecting) {
            showToast("采集中请先结束再喂食")
            return
        }
        FeedFoodPicker.show(context) { foodId -> feedFromBag(foodId) }
    }

    /** 扣背包 + 加体力心情 + 播吃动画。 */
    fun feedFromBag(foodId: String) {
        val food = FoodCatalog.byId(foodId) ?: return
        if (!FoodInventoryStore.consumeOne(context, foodId)) {
            showToast("没有${food.label}了")
            return
        }
        AppDataStore.addStaminaMood(context, food.stamina, food.mood)
        AppDataStore.unlock(context, "first_feed")
        showToast("喂苍叶：${food.label}（体+${food.stamina} 心+${food.mood}）")
        playFeedAnim(foodId)
    }

    /** 面板喂食后：仅播苍叶 eat 动画（数值已在 Panel 扣过）。伴侣不吃。 */
    fun playFeedAnim(foodId: String?) {
        if (musicMode) return
        beginUserInteract()
        animator.playPose(listOf(SpriteAssets.EAT1, SpriteAssets.EAT2), PetAnimator.DUR_EAT, loop = true)
        fx?.showFood(foodId ?: "apple")
        @Suppress("UNUSED_PARAMETER")
        val fed = foodId
        banter("eat", "eat")
        scheduleResumeWalking(PetAnimator.DUR_EAT)
    }

    fun openCollect() {
        if (isCollecting) {
            showToast("采集进行中")
            return
        }
        ModeTimeStore.setBucket(context, "game")
        abortAllModes()
        locomotion = Locomotion.NONE
        walkStepsLeft = 0
        freeIdleUntil = Long.MAX_VALUE / 4
        animator.setMode(PetAnimator.Mode.STAND, driveMove = false)
        collectUi = CollectOverlayUi(
            context = context,
            windowManager = windowManager,
            roomHost = roomHost,
            screenSize = screenSize,
            petSize = petSize,
            petTopLeft = petTopLeft,
            setPetTopLeft = setPetTopLeft,
            raisePets = {
                // 图层：伴侣 < 桌宠 < 游戏界面（本回调后再 raiseCollect）
                companion?.raise()
                raisePetOverlay?.invoke()
            },
            setPetsTouchable = { touchable ->
                setPetTouchable?.invoke(touchable)
            },
            onNearFood = { near ->
                if (!isCollecting) return@CollectOverlayUi
                // 对照桌面：靠近切 happy，离开回 stand（静帧，不跳）
                animator.setCollectNear(near)
            },
            onFinished = {
                collectUi = null
                setPetTouchable?.invoke(true)
                if (!suppressResumeFree) {
                    returnToFreeIfIdle(startWalk = true)
                }
            },
        ).also { it.start() }
        syncModeBucket()
        showToast("手指滑动接住下落食物")
    }

    private fun stopCollect(resumeFree: Boolean) {
        val ui = collectUi ?: return
        ui.stop()
        collectUi = null
        animator.setMode(PetAnimator.Mode.STAND, driveMove = false)
        if (resumeFree && !suppressResumeFree) {
            returnToFreeIfIdle(startWalk = true)
        }
    }

    fun openRhythm() {
        ModeTimeStore.setBucket(context, "game")
        startActivity(RhythmActivity::class.java)
    }

    fun openRhyme() = startActivity(RhymeActivity::class.java)

    fun openExpose() = startActivity(ExposeActivity::class.java)

    fun toggleWorkShowProps() {
        val next = !AppDataStore.workShowProps(context)
        AppDataStore.setWorkShowProps(context, next)
        refreshWorkPropsNow()
        showToast("显示目的地：${if (next) "开" else "关"}")
    }

    fun toggleWorkShowStack() {
        val next = !AppDataStore.workShowStack(context)
        AppDataStore.setWorkShowStack(context, next)
        refreshWorkPropsNow()
        showToast("显示运送货物：${if (next) "开" else "关"}")
    }

    private fun refreshWorkPropsNow() {
        // 触发一次 props 刷新：挪 0 像素仍走 sync
        workEngine?.moveEndFoot(
            workEngine!!.endFoot().x,
            workEngine!!.endFoot().y,
        )
    }

    fun togglePersona() {
        val next = AppDataStore.togglePersona(context)
        animator.applyFrame()
        // 莲不跟金目人格；仅主宠改尺寸时 refreshSprite
        showToast("人格：${if (next == "jinmu") "金目" else "默认"}")
    }

    private fun startActivity(cls: Class<*>) {
        val i = android.content.Intent(context, cls)
        if (context !is android.app.Activity) {
            i.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        context.startActivity(i)
    }

    fun openSystemPage(page: String) {
        val i = android.content.Intent(context, SystemHubActivity::class.java)
            .putExtra(SystemHubActivity.EXTRA_PAGE, page)
        if (context !is android.app.Activity) {
            i.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        context.startActivity(i)
    }

    fun playPresetDialog(entry: PresetDialogs.Entry) {
        if (musicMode) return
        beginUserInteract()
        // V-EMAIL：点对话有概率 email 语音
        if (voice?.voiceEnabled() == true && voice?.hasCategory("email") == true &&
            kotlin.random.Random.nextFloat() < 0.5f
        ) {
            voice?.playCategory("email", force = false, chain = true)
        }
        val reply = entry.answers.random()
        speech?.showDialog("你：${entry.question}", 2200L)
        mainHandler.postDelayed({
            val hold = (2800 + reply.length * 45).coerceAtLeast(4200).toLong()
            speech?.showDialog(reply, hold)
            animator.playPose(
                listOf(SpriteAssets.HI1, SpriteAssets.HI2),
                hold.coerceAtMost(2800L),
                loop = true,
            )
            scheduleResumeWalking(hold)
        }, 2300L)
    }

    fun showOwnerInfo() {
        val name = PetPrefs.ownerName(context)
        if (name.isEmpty()) {
            showToast("尚未认主 · 请回主界面填写所属人")
            return
        }
        ModeTimeStore.flush(context)
        OwnerCompanionUi.show(context)
        val days = PetPrefs.companionDays(context)
        val total = ModeTimeStore.formatDuration(ModeTimeStore.totalSeconds(context))
        speak("相伴第 $days 天，合计 $total。", null, holdMs = 2800L)
    }

    fun playExpression(id: String) {
        if (musicMode) {
            showToast("音乐模式中暂不触发表情")
            return
        }
        if (videoMode || appGameMode) {
            showToast("场景姿势中暂不触发表情")
            return
        }
        beginUserInteract()
        when (id) {
            "expr_happy" -> {
                animator.setMode(PetAnimator.Mode.HAPPY)
                fx?.showHappy()
                // D04：开心无 banter
            }
            "expr_sad" -> {
                // squat → sad1 → sad2（对照 _play_expression_sad）
                animator.playTimedPose(
                    listOf(
                        SpriteAssets.SQUAT to PetAnimator.SAD_SQUAT_MS,
                        SpriteAssets.SAD1 to PetAnimator.SAD_SAD1_MS,
                        SpriteAssets.SAD2 to PetAnimator.SAD_SAD2_MS,
                    ),
                )
                fx?.showRain(PetAnimator.DUR_SAD)
                banter("sad")
            }
            "expr_shy" -> {
                // 默认 shy1；桌面双击才 shy2 —— 手机单次触发放 shy1
                animator.playPose(listOf(SpriteAssets.SHY1), PetAnimator.DUR_SHY, loop = false)
                fx?.showShy(PetAnimator.DUR_SHY)
            }
            "expr_wink" -> {
                animator.playPose(listOf(SpriteAssets.WINK), PetAnimator.DUR_WINK, loop = false)
                fx?.showWink()
            }
            "expr_like" -> {
                animator.playPose(listOf(SpriteAssets.LIKE), PetAnimator.DUR_LIKE, loop = false)
                fx?.showLike()
            }
            "expr_angry" -> {
                // 对照 _angry_anim_step 有限序列，再停在 stand_angry
                val seq = listOf(
                    SpriteAssets.STAND_ANGRY,
                    SpriteAssets.WALK_FRONT1,
                    SpriteAssets.STAND_ANGRY,
                    SpriteAssets.WALK_BACK1,
                    SpriteAssets.WALK_BACK2,
                    SpriteAssets.WALK_BACK1,
                    SpriteAssets.WALK_BACK2,
                    SpriteAssets.WALK_BACK1,
                    SpriteAssets.WALK_BACK2,
                    SpriteAssets.STAND_ANGRY,
                )
                val animMs = seq.size * PetAnimator.ANGRY_FRAME_MS
                animator.playPose(
                    seq,
                    holdMs = animMs + PetAnimator.DUR_ANGRY,
                    loop = false,
                    frameMs = PetAnimator.ANGRY_FRAME_MS,
                )
                fx?.showAngry(animMs + PetAnimator.DUR_ANGRY)
                banter("angry")
            }
            "expr_idea" -> {
                // stand + 灯泡 → eat2（对照 _play_expression_idea）
                fx?.showBulb(PetAnimator.IDEA_STAND_MS + PetAnimator.DUR_IDEA)
                animator.playTimedPose(
                    listOf(
                        SpriteAssets.STAND to PetAnimator.IDEA_STAND_MS,
                        SpriteAssets.EAT2 to PetAnimator.DUR_IDEA,
                    ),
                )
            }
            "expr_question" -> {
                // 站立 + 问号贴纸（对照 stand_question）
                animator.playPose(
                    listOf(SpriteAssets.STAND_QUESTION),
                    PetAnimator.DUR_QUESTION,
                    loop = false,
                )
                banter("question")
            }
            "expr_bixin" -> {
                animator.playPose(listOf(SpriteAssets.STAND), PetAnimator.DUR_BIXIN, loop = false)
                fx?.showBixin(PetAnimator.DUR_BIXIN)
                banter("bixin")
            }
            else -> showToast("（后期）表情")
        }
        val hold = when (id) {
            "expr_happy" -> PetAnimator.DUR_HAPPY
            "expr_sad" -> PetAnimator.DUR_SAD
            "expr_shy" -> PetAnimator.DUR_SHY
            "expr_wink" -> PetAnimator.DUR_WINK
            "expr_like" -> PetAnimator.DUR_LIKE
            "expr_angry" -> PetAnimator.DUR_ANGRY + 10 * PetAnimator.ANGRY_FRAME_MS
            "expr_idea" -> PetAnimator.IDEA_STAND_MS + PetAnimator.DUR_IDEA
            "expr_question" -> PetAnimator.DUR_QUESTION
            "expr_bixin" -> PetAnimator.DUR_BIXIN
            else -> 1200L
        }
        scheduleResumeWalking(hold)
    }

    fun playAction(id: String) {
        if (musicMode && id !in setOf("act_stand", "act_walk")) {
            showToast("音乐模式中暂不触发动作")
            return
        }
        when (id) {
            "act_walk" -> {
                // 走动本身：结束互动占用，回到漫步
                endUserInteractHold()
                startStroll()
                banter("walk", "walk")
            }
            "act_sleep" -> {
                endUserInteractHold()
                startSleepInteract()
            }
            "act_eat" -> openEatFoodMenu()
            "act_stand" -> {
                beginUserInteract()
                abortAllModes()
                returnToFreeIfIdle(startWalk = false)
                banter("stand")
                scheduleResumeWalking(2000L)
            }
            "act_hi" -> {
                beginUserInteract()
                animator.playPose(
                    listOf(SpriteAssets.HI1, SpriteAssets.HI2),
                    holdMs = PetAnimator.DUR_HI,
                    loop = true,
                )
                speak(
                    InteractLines.HI_TEXT, "hi", PetAnimator.DUR_HI,
                    forceVoice = true, hiTypewriter = true,
                )
                scheduleResumeWalking(PetAnimator.DUR_HI)
            }
            "act_squat" -> {
                beginUserInteract()
                animator.playPose(listOf(SpriteAssets.SQUAT), PetAnimator.DUR_SQUAT, loop = false)
                scheduleResumeWalking(PetAnimator.DUR_SQUAT)
            }
            "act_kick" -> {
                beginUserInteract()
                animator.playPose(listOf(SpriteAssets.KICK), PetAnimator.DUR_KICK, loop = false)
                fx?.showKick(PetAnimator.DUR_KICK)
                banter("kick", "kick")
                scheduleResumeWalking(PetAnimator.DUR_KICK)
            }
            "act_yes" -> {
                beginUserInteract()
                animator.playPose(listOf(SpriteAssets.YES), PetAnimator.DUR_YES, loop = false)
                banter("yes")
                scheduleResumeWalking(PetAnimator.DUR_YES)
            }
            "act_no" -> {
                beginUserInteract()
                animator.playPose(listOf(SpriteAssets.NO), PetAnimator.DUR_NO, loop = false)
                banter("no")
                scheduleResumeWalking(PetAnimator.DUR_NO)
            }
            "act_call" -> {
                beginUserInteract()
                animator.playPose(
                    listOf(SpriteAssets.CALL1, SpriteAssets.CALL2),
                    holdMs = PetAnimator.DUR_CALL,
                    loop = true,
                )
                speak(InteractLines.CALL_TEXT, "call", PetAnimator.DUR_CALL, forceVoice = true)
                scheduleResumeWalking(PetAnimator.DUR_CALL)
            }
            "act_judge" -> {
                beginUserInteract()
                playYesNoJudge()
            }
            "act_adult" -> {
                beginUserInteract()
                speak(InteractLines.ADULT_CONTENT_TEXT, holdMs = 8000L)
                scheduleResumeWalking(8000L)
            }
            else -> showToast("（后期）动作")
        }
    }

    private fun playYesNoJudge() {
        speak(InteractLines.YESNO_ANSWER_TEXT, holdMs = 0)
        val gen = interactGen
        mainHandler.postDelayed({
            if (gen != interactGen) return@postDelayed
            val yes = kotlin.random.Random.nextBoolean()
            if (yes) {
                animator.playPose(listOf(SpriteAssets.YES), PetAnimator.DUR_YES, loop = false)
                speak("判断结果：${InteractLines.line("yes")}", holdMs = PetAnimator.DUR_YES)
            } else {
                animator.playPose(listOf(SpriteAssets.NO), PetAnimator.DUR_NO, loop = false)
                speak("判断结果：${InteractLines.line("no")}", holdMs = PetAnimator.DUR_NO)
            }
            scheduleResumeWalking(PetAnimator.DUR_YES)
        }, 5000L)
    }

    /** 菜单/喂食等互动：高于随机与走动；清特效残留；作废旧的恢复走动。 */
    private fun beginUserInteract() {
        lastUserActivityMs = android.os.SystemClock.elapsedRealtime()
        interactGen++
        idleActionBusy = true
        cancelResumeWalking()
        fx?.clearBurst()
        companionFx?.clearBurst()
        abortLocomotionSoft()
    }

    private fun endUserInteractHold() {
        interactGen++
        idleActionBusy = false
        cancelResumeWalking()
        fx?.clearBurst()
        companionFx?.clearBurst()
    }

    private fun cancelResumeWalking() {
        resumeWalkJob?.let { mainHandler.removeCallbacks(it) }
        resumeWalkJob = null
    }

    private fun scheduleResumeWalking(afterMs: Long) {
        cancelResumeWalking()
        val gen = interactGen
        val job = Runnable {
            if (gen != interactGen) return@Runnable
            resumeWalkJob = null
            idleActionBusy = false
            fx?.clearBurst()
            companionFx?.clearBurst()
            resumeWalkingAfterPause()
        }
        resumeWalkJob = job
        mainHandler.postDelayed(job, afterMs.coerceAtLeast(200L))
    }

    private fun abortLocomotionSoft() {
        if (isWorking || isFollowing || isQuiet || isPomodoro || isMusic) {
            abortAllModes()
            // 表情/动作打断独占模式后回到自由身份，走动由动作结束后再启
            locomotion = Locomotion.FREE
            walkStepsLeft = 0
            freeIdleUntil = Long.MAX_VALUE / 4
            syncModeBucket()
        } else {
            stopLocomotion()
        }
    }

    private fun installFollowCatcher() {
        removeFollowCatcher()
        val v = View(context).apply {
            setBackgroundColor(0x01000000)
            setOnTouchListener { _, e ->
                if (e.action == MotionEvent.ACTION_DOWN || e.action == MotionEvent.ACTION_MOVE) {
                    followEngine?.setTarget(e.rawX.toInt(), e.rawY.toInt())
                }
                true
            }
        }
        followCatcher = v
        if (windowManager != null && roomHost == null) {
            val lp = WindowManager.LayoutParams(
                WindowManager.LayoutParams.MATCH_PARENT,
                WindowManager.LayoutParams.MATCH_PARENT,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT,
            )
            windowManager.addView(v, lp)
            raisePetOverlay?.invoke()
        } else {
            roomHost?.let { host ->
                host.addView(
                    v,
                    0,
                    FrameLayout.LayoutParams(
                        FrameLayout.LayoutParams.MATCH_PARENT,
                        FrameLayout.LayoutParams.MATCH_PARENT,
                    ),
                )
            }
        }
    }

    private fun removeFollowCatcher() {
        val v = followCatcher ?: return
        try {
            if (windowManager != null && roomHost == null) windowManager.removeView(v)
            else roomHost?.removeView(v)
        } catch (_: Exception) {
        }
        followCatcher = null
    }

    private fun ensureQuietHud() {
        if (quietHud != null) return
        val b = OverlayQuietHudBinding.inflate(LayoutInflater.from(context))
        b.quietEnd.setOnClickListener { endQuiet(fromMenu = true) }
        quietHud = b
        attachTopHud(b.root, yOverlay = 48, topRoom = 100)
    }

    private fun removeQuietHud() {
        detachHud(quietHud?.root)
        quietHud = null
    }

    private fun ensurePomoHud() {
        if (pomoHud != null) return
        val b = OverlayPomoHudBinding.inflate(LayoutInflater.from(context))
        val btnSp = AppDataStore.fontClockBtnSp(context)
        b.pomoProgress.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, AppDataStore.fontCaptionSp(context))
        b.pomoPlay.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, btnSp)
        b.pomoPause.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, btnSp)
        b.pomoEnd.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, btnSp)
        b.pomoPlay.setOnClickListener { pomo?.resume() }
        b.pomoPause.setOnClickListener { pomo?.pause() }
        b.pomoEnd.setOnClickListener { endPomodoro(silent = false) }
        b.pomoClockDecor.applyFontScale(context)
        pomoHud = b
        attachTopHud(b.root, yOverlay = 48, topRoom = 100)
    }

    private fun removePomoHud() {
        detachHud(pomoHud?.root)
        pomoHud = null
    }

    private fun attachTopHud(root: View, yOverlay: Int, topRoom: Int) {
        if (windowManager != null && roomHost == null) {
            val lp = WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT,
            ).apply {
                gravity = Gravity.TOP or Gravity.CENTER_HORIZONTAL
                y = yOverlay
            }
            windowManager.addView(root, lp)
        } else {
            val lp = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,
                FrameLayout.LayoutParams.WRAP_CONTENT,
            ).apply {
                gravity = Gravity.TOP or Gravity.CENTER_HORIZONTAL
                topMargin = topRoom
            }
            roomHost?.addView(root, lp)
        }
    }

    private fun detachHud(root: View?) {
        if (root == null) return
        try {
            if (windowManager != null && roomHost == null) windowManager.removeView(root)
            else roomHost?.removeView(root)
        } catch (_: Exception) {
        }
    }

    private fun showToast(msg: String) {
        Toast.makeText(context, msg, Toast.LENGTH_SHORT).show()
    }

    private fun clearWorkTimer() {
        workTimerJob?.let { mainHandler.removeCallbacks(it) }
        workTimerJob = null
    }

    private fun clearWorkBanter() {
        workBanterJob?.let { mainHandler.removeCallbacks(it) }
        workBanterJob = null
        workContinuousSession = false
    }

    /** 对照 `_schedule_work_mode_banter`：自由运送周期性鼓励。 */
    private fun scheduleWorkBanter() {
        workBanterJob?.let { mainHandler.removeCallbacks(it) }
        workBanterJob = null
        if (!workContinuousSession) return
        val delay = Random.nextLong(WORK_MODE_BANTER_INTERVAL_LO_MS, WORK_MODE_BANTER_INTERVAL_HI_MS + 1)
            .coerceAtLeast(WORK_MODE_BANTER_COOLDOWN_MS)
        workBanterJob = Runnable {
            workBanterJob = null
            if (isWorking && workContinuousSession) {
                triggerWorkBanter(fromStep = false)
                scheduleWorkBanter()
            }
        }
        mainHandler.postDelayed(workBanterJob!!, delay)
    }

    /** 对照 `_trigger_work_banter` / `_maybe_work_mode_banter`。 */
    private fun triggerWorkBanter(fromStep: Boolean) {
        if (!isWorking) return
        if (!fromStep && !workContinuousSession) return
        val now = android.os.SystemClock.elapsedRealtime()
        if (!fromStep && workBanterLastMs > 0L && now - workBanterLastMs < WORK_MODE_BANTER_COOLDOWN_MS) {
            return
        }
        workBanterLastMs = now
        val line = InteractLines.WORK_MODE.random()
        speak(line, "work", holdMs = 4200L, forceVoice = true)
    }

    /** 对照 `_stand_tick` 随机链（仅自由站立）。 */
    private fun tryStandIdleRandom(): Boolean {
        if (locomotion != Locomotion.FREE || musicMode || idleActionBusy) return false
        if (isWorking || isFollowing || isQuiet || isPomodoro) return false
        val mood = AppDataStore.mood(context)
        if (mood < MOOD_LOW_THRESHOLD && Random.nextFloat() < MOOD_RANDOM_CHANCE) {
            val pool = moodActionPool(mood)
            val act = pool.randomOrNull() ?: return false
            return fireIdleAction(act)
        }
        if (Random.nextFloat() < VOICE_FREE_RANDOM_CHANCE) {
            val cats = mutableListOf("normal", "forget", "dizzy")
            if (AppDataStore.companionEnabled(context)) cats += "ren"
            if (AppDataStore.isJinmu(context)) cats += "jinmu"
            val cat = cats.random()
            // 自由 random 只播语音字幕，不绑 walk 文案
            if (voice?.playCategory(cat, force = false) == true) {
                return true
            }
        }
        if (Random.nextFloat() < FREE_RANDOM_ACTION_CHANCE) {
            // 自由随机动作不含 wink；squat 无 banter
            val pool = listOf("hi", "squat", "like", "question")
            return fireIdleAction(pool.random())
        }
        return false
    }

    private fun moodActionPool(mood: Int): List<String> = when {
        mood >= 85 -> listOf("happy", "like")
        mood >= 65 -> listOf("hi", "idea", "question")
        mood >= 45 -> listOf("squat", "question")
        mood >= 25 -> listOf("sad")
        else -> listOf("sad", "angry")
    }

    private fun fireIdleAction(act: String): Boolean {
        if (idleActionBusy) return false
        // 走统一入口，避免与菜单互动抢优先级 / 双重恢复走动
        when (act) {
            "angry" -> {
                playExpression("expr_angry")
                return true
            }
            "hi" -> {
                playAction("act_hi")
                return true
            }
            "happy" -> {
                playExpression("expr_happy")
                return true
            }
            "like" -> {
                playExpression("expr_like")
                return true
            }
            "sad" -> {
                playExpression("expr_sad")
                return true
            }
            "question" -> {
                playExpression("expr_question")
                return true
            }
            "idea" -> {
                playExpression("expr_idea")
                return true
            }
            "squat" -> {
                playAction("act_squat")
                return true
            }
            else -> return false
        }
    }

    private fun maybeMetaBanter(event: String, forceChance: Float? = null): Boolean {
        val lines = InteractLines.META[event] ?: return false
        val chance = forceChance ?: when (event) {
            "drag_long" -> 0.20f
            "work_flag" -> 0.32f
            "idle_long" -> 0.40f
            else -> 0.30f
        }
        if (Random.nextFloat() >= chance) return false
        val now = android.os.SystemClock.elapsedRealtime()
        if (now - lastMetaGlobalMs < META_BANTER_GLOBAL_COOLDOWN_MS) return false
        val evCd = when (event) {
            "drag_long" -> 240_000L
            "work_flag" -> 160_000L
            "idle_long" -> 700_000L
            else -> 180_000L
        }
        if (now - (metaEventMs[event] ?: 0L) < evCd) return false
        lastMetaGlobalMs = now
        metaEventMs[event] = now
        speak(lines.random(), holdMs = 2800L)
        return true
    }

    private fun startMetaIdlePoll() {
        stopMetaIdlePoll()
        metaIdleJob = object : Runnable {
            override fun run() {
                val now = android.os.SystemClock.elapsedRealtime()
                if (locomotion == Locomotion.FREE && locomotionEnabled &&
                    !idleActionBusy && now - lastUserActivityMs >= META_BANTER_IDLE_MS
                ) {
                    maybeMetaBanter("idle_long")
                }
                mainHandler.postDelayed(this, META_BANTER_IDLE_CHECK_MS)
            }
        }
        mainHandler.postDelayed(metaIdleJob!!, META_BANTER_IDLE_CHECK_MS)
    }

    private fun stopMetaIdlePoll() {
        metaIdleJob?.let { mainHandler.removeCallbacks(it) }
        metaIdleJob = null
    }

    /** 自由站立：按设置间隔触发语音/动作表情。 */
    private fun scheduleFreeIdlePulse() {
        stopFreeIdlePulse()
        val sec = AppDataStore.freeIdleBanterSec(context).toLong().coerceIn(10L, 30L)
        freeIdlePulseJob = Runnable {
            freeIdlePulseJob = null
            maybeFreeIdlePulse()
            scheduleFreeIdlePulse()
        }
        mainHandler.postDelayed(freeIdlePulseJob!!, sec * 1000L)
    }

    private fun stopFreeIdlePulse() {
        freeIdlePulseJob?.let { mainHandler.removeCallbacks(it) }
        freeIdlePulseJob = null
    }

    private fun maybeFreeIdlePulse() {
        if (locomotion != Locomotion.FREE || musicMode || idleActionBusy) return
        if (isWorking || isFollowing || isQuiet || isPomodoro || isCollecting) return
        if (videoMode || appGameMode) return
        // 走动中不打断；停下（站立/表情结束）才触发
        val m = animator.currentMode()
        if (m == PetAnimator.Mode.WALK || m == PetAnimator.Mode.MUSIC_WALK ||
            m == PetAnimator.Mode.WORK_WALK || m == PetAnimator.Mode.DRAG_MOVE
        ) {
            return
        }
        if (walkStepsLeft > 0) return
        // 间隔到：优先语音，再动作/表情
        val cats = mutableListOf("normal", "forget", "dizzy")
        if (AppDataStore.companionEnabled(context)) cats += "ren"
        if (AppDataStore.isJinmu(context)) cats += "jinmu"
        voice?.playCategory(cats.random(), force = true)
        if (!idleActionBusy) {
            val mood = AppDataStore.mood(context)
            val pool = if (mood < MOOD_LOW_THRESHOLD) {
                moodActionPool(mood)
            } else {
                listOf("hi", "squat", "like", "question", "happy", "idea")
            }
            fireIdleAction(pool.random())
        }
    }
}
