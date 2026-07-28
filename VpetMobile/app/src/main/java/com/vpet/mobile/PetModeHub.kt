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

    private var locomotion = Locomotion.NONE
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
    private var toolClock: ToolClockUi? = null
    private var musicPlayer: MusicPlayer? = null
    private var companion: CompanionFollower? = null
    private var speech: SpeechBubbleUi? = null
    private var fx: PetFxUi? = null
    private var voice: VoicePlayer? = null
    private var musicMode = false
    private val mainHandler = android.os.Handler(android.os.Looper.getMainLooper())
    private var lastUserActivityMs = android.os.SystemClock.elapsedRealtime()
    private var lastDragYuqiMs = 0L
    private var lastMetaGlobalMs = 0L
    private val metaEventMs = mutableMapOf<String, Long>()
    private var metaIdleJob: Runnable? = null
    private var workTimerJob: Runnable? = null
    private var workShowEndButton = true
    private var idleActionBusy = false

    companion object {
        const val FREE_RANDOM_ACTION_CHANCE = 0.06f
        const val MOOD_RANDOM_CHANCE = 0.09f
        const val MOOD_LOW_THRESHOLD = 40
        const val VOICE_FREE_RANDOM_CHANCE = 0.045f
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
    val locomotionEnabled get() =
        locomotion != Locomotion.NONE && !isWorking && !isFollowing && !isQuiet

    fun attach() {
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
        fx = PetFxUi(
            context = context,
            windowManager = windowManager,
            roomHost = roomHost,
            petTopLeft = petTopLeft,
            petSize = petSize,
            raisePet = raisePetOverlay,
        )
        syncHeadFlower()
        if (AppDataStore.companionEnabled(context)) {
            companion?.start()
        }
        startMetaIdlePoll()
        startHungerPoll()
        ModeTimeStore.setBucket(context, "free")
        // H-STARTUP-SLEEP1：开场用 sleep1 立绘做入场溶解
        mainHandler.post {
            animator.setMode(PetAnimator.Mode.SLEEP_PEEK)
            animator.playDissolve(reverse = false) {
                animator.setMode(PetAnimator.Mode.STAND)
                mainHandler.postDelayed({
                    val greet = PetProfileStore.consumeLaunchGreeting(context) ?: return@postDelayed
                    speak(greet, null, forceVoice = false)
                }, 200L)
            }
        }
    }

    fun syncHeadFlower() {
        fx?.setWearFlower(PetProfileStore.wearingFlower(context))
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
            musicMode -> "music"
            isWorking || isPomodoro -> "work"
            isFollowing -> "follow"
            isQuiet -> "quiet"
            locomotion == Locomotion.STROLL -> "stroll"
            locomotion == Locomotion.FREE -> "free"
            else -> "free"
        }
        ModeTimeStore.setBucket(context, key)
    }

    fun destroy() {
        stopMetaIdlePoll()
        stopHungerPoll()
        clearWorkTimer()
        clearSleepInteract()
        ModeTimeStore.flush(context)
        ModeTimeStore.setBucket(context, null)
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
        workProps?.destroy()
        workProps = null
        toolClock?.destroy()
        toolClock = null
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
            speech?.showVoiceSubtitle(InteractLines.DRAG_DIZZY.random(), 2400L)
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
                if (played) {
                    if (text.isNotBlank()) speech?.showVoiceSubtitle(text, holdMs.coerceAtLeast(3000L))
                } else if (text.isNotBlank()) {
                    if (hiTypewriter) speech?.showHiTypewriter(text, holdMs.coerceAtLeast(4200L))
                    else speech?.showTypewriter(text, holdMs, typewriterMs)
                }
                return
            }
            "call" -> {
                val played = voice?.playCall(
                    onRingStart = { speech?.hide() },
                    onLineStart = {
                        if (text.isNotBlank()) {
                            speech?.showVoiceSubtitle(text, holdMs.coerceAtLeast(4500L))
                        }
                    },
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
                    if (played) {
                        if (text.isNotBlank()) speech?.showVoiceSubtitle(text, holdMs)
                        return
                    }
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
        endMusic(silent = true)
        endPomodoro(silent = true)
        stopWorkSilent()
        endFollow(silent = true)
        stopQuietSilent()
        clearSleepInteract()
        locomotion = Locomotion.NONE
        fx?.clearBurst()
        fx?.setMusicWave(false)
        fx?.setSleepZzz(false)
        // 不在此处 sync：调用方会设新模式；destroy 已 flush
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

    fun stopLocomotion() {
        locomotion = Locomotion.NONE
        walkStepsLeft = 0
    }

    /** 移动时钟回调：返回 true 表示本帧应位移。 */
    fun onWalkAnimStep(): Boolean {
        if (!locomotionEnabled) return false
        val now = android.os.SystemClock.elapsedRealtime()
        if (now < freeIdleUntil) return false

        if (musicMode) {
            if (animator.currentMode() != PetAnimator.Mode.MUSIC_WALK) {
                beginWalkBurst(music = true)
            }
            if (walkStepsLeft <= 0) {
                val wait = Random.nextLong(700, 2000)
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
            return true
        }

        when (locomotion) {
            Locomotion.FREE, Locomotion.STROLL -> {
                if (walkStepsLeft <= 0) {
                    if (idleActionBusy) return false
                    var wait = if (locomotion == Locomotion.FREE) {
                        Random.nextLong(450, 1400)
                    } else {
                        Random.nextLong(280, 900)
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
                    return false
                }
                if (animator.currentMode() != PetAnimator.Mode.WALK) {
                    animator.setMode(PetAnimator.Mode.WALK)
                }
                walkStepsLeft--
                fx?.syncPlace()
                speech?.reposition()
                return true
            }
            else -> return false
        }
    }

    private fun beginWalkBurst(music: Boolean) {
        walkStepsLeft = if (music) Random.nextInt(40, 101) else Random.nextInt(70, 181)
        animator.setWalkDir(SpriteAssets.Dir.random())
        animator.setMode(if (music) PetAnimator.Mode.MUSIC_WALK else PetAnimator.Mode.WALK)
    }

    fun startFollow() {
        abortAllModes()
        val eng = FollowEngine(object : FollowEngine.Host {
            override fun screenSize() = this@PetModeHub.screenSize()
            override fun petSize() = this@PetModeHub.petSize()
            override fun petTopLeft() = this@PetModeHub.petTopLeft()
            override fun setPetTopLeft(x: Int, y: Int) = this@PetModeHub.setPetTopLeft(x, y)
            override fun onFollowWalk(walking: Boolean) {
                if (walking) {
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
                // 晕眩三件套：特效 + 文案 + dizzy 语音（有资源时强制）
                speak(InteractLines.FOLLOW_DIZZY_TEXT, "dizzy", 3000L, forceVoice = true)
            }
            override fun toast(msg: String) = showToast(msg)
        })
        followEngine = eng
        eng.start()
        installFollowCatcher()
        showToast("跟随中 · 点屏幕空白处引路，急转会晕")
        syncModeBucket()
    }

    fun endFollow(silent: Boolean = false) {
        followEngine?.stop()
        followEngine = null
        removeFollowCatcher()
        if (!silent) {
            animator.setMode(PetAnimator.Mode.STAND)
            showToast("结束跟随")
        }
        syncModeBucket()
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

    /** 互动→睡眠：对照 SLEEP_INTERACT_MS=30s 后自动醒。 */
    fun startSleepInteract() {
        abortAllModes()
        clearSleepInteract()
        animator.setMode(PetAnimator.Mode.SLEEP)
        fx?.setSleepZzz(true)
        banter("sleep", "sleep")
        showToast("小憩 30 秒…")
        sleepInteractJob = Runnable {
            sleepInteractJob = null
            fx?.setSleepZzz(false)
            animator.setMode(PetAnimator.Mode.STAND)
            showToast("睡醒了")
            syncModeBucket()
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

    private fun launchQuiet() {
        val q = QuietSession(object : QuietSession.Host {
            override fun onQuietVisual(peek: Boolean) {
                animator.setMode(
                    if (peek) PetAnimator.Mode.SLEEP_PEEK else PetAnimator.Mode.SLEEP,
                )
                fx?.setSleepZzz(!peek)
            }
            override fun onQuietTick(elapsedSec: Long) {
                if (!isPomodoro) {
                    quietHud?.quietProgress?.text = "睡眠 ${QuietSession.formatDuration(elapsedSec)}"
                }
            }
            override fun onQuietEnded(elapsedSec: Long) {
                removeQuietHud()
                if (!isPomodoro) animator.setMode(PetAnimator.Mode.STAND)
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
        if (fromMenu) q.endFromMenu() else q.stop()
        quiet = null
        removeQuietHud()
        fx?.setSleepZzz(false)
        syncModeBucket()
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
                    workProps?.clear()
                    clearWorkTimer()
                    if (delivered > 0) AppDataStore.unlock(context, "work_done")
                    if (!isPomodoro) animator.setMode(PetAnimator.Mode.STAND)
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
            },
            continuous = continuous,
            total = total,
        )
        workEngine = eng
        eng.start()
        if (!fromPomo) {
            speak(InteractLines.WORK_MODE.random(), "work", 3200L)
        }
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
        syncModeBucket()
    }

    private fun stopWorkSilent() {
        clearWorkTimer()
        workEngine?.stop(internal = true)
        workEngine = null
        workProps?.clear()
    }

    private fun stopQuietSilent() {
        quiet?.stop(internal = true)
        quiet = null
        removeQuietHud()
        fx?.setSleepZzz(false)
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
                pomoHud?.pomoProgress?.text =
                    "番茄·工作 第${round}轮 ${PomodoroSession.formatRemain(workMs)}"
            }
            override fun onPomoRestStart(round: Int, restMs: Long) {
                stopWorkSilent()
                workProps?.clear()
                launchQuiet()
                pomoHud?.pomoProgress?.text =
                    "番茄·休息 第${round}轮 ${PomodoroSession.formatRemain(restMs)}"
            }
            override fun onPomoTick(phase: String, round: Int, remainMs: Long) {
                val label = if (phase == "rest") "休息" else "工作"
                pomoHud?.pomoProgress?.text =
                    "番茄·$label 第${round}轮 ${PomodoroSession.formatRemain(remainMs)}"
            }
            override fun onPomoRoundDone(completed: Int, nextRound: Int) {
                stopQuietSilent()
                AppDataStore.unlock(context, "pomo_done")
            }
            override fun onPomoEnded(completed: Int) {
                stopWorkSilent()
                stopQuietSilent()
                removePomoHud()
                animator.setMode(PetAnimator.Mode.STAND)
            }
            override fun toast(msg: String) = showToast(msg)
        })
        pomo = session
        session.start(workMin, restMin)
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
        animator.setMode(PetAnimator.Mode.STAND)
    }

    fun showStopwatch() = toolClock?.showStopwatch()
    fun showTimer(minutes: Int) = toolClock?.showTimer(minutes)

    fun startMusic() {
        if (musicMode) {
            endMusic(silent = false)
            return
        }
        val uriStr = PetProfileStore.musicUri(context)
        if (uriStr.isNullOrBlank()) {
            showToast("请先在「工具与档案」导入本地歌曲（网易云云端无法直连）")
            openTools()
            return
        }
        abortAllModes()
        musicMode = true
        voice?.musicBlocked = true
        voice?.stop()
        locomotion = Locomotion.STROLL
        freeIdleUntil = 0L
        beginWalkBurst(music = true)
        val title = PetProfileStore.musicTitle(context).ifBlank { "音乐" }
        musicPlayer?.playUri(
            android.net.Uri.parse(uriStr),
            onError = {
                showToast(it)
                endMusic(silent = true)
            },
        )
        AppDataStore.unlock(context, "music_play")
        fx?.setMusicWave(true)
        showToast("音乐漫步 · $title")
        syncModeBucket()
    }

    fun endMusic(silent: Boolean) {
        if (!musicMode && musicPlayer?.playing != true) return
        musicMode = false
        voice?.musicBlocked = false
        musicPlayer?.stop()
        fx?.setMusicWave(false)
        if (locomotion == Locomotion.STROLL) locomotion = Locomotion.NONE
        if (!silent) {
            animator.setMode(PetAnimator.Mode.STAND)
            showToast("结束音乐")
        }
        syncModeBucket()
    }

    fun toggleCompanion() {
        val c = companion ?: return
        if (c.active) {
            c.stop()
            AppDataStore.setCompanionEnabled(context, false)
            showToast("智能伴侣栏已关闭")
        } else {
            c.start()
            AppDataStore.setCompanionEnabled(context, true)
            fx?.showHappy()
            voice?.playCompanionStart()
            AppDataStore.unlock(context, "companion_on")
            showToast("智能伴侣栏已开启 · 莲来陪你啦！")
        }
    }

    fun refreshCompanionSize() {
        companion?.refreshSprite()
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
        fun tryFinish() {
            if (voiceDone && animDone) mainHandler.post(finishOnce)
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

    /** 面板喂食后：仅播苍叶 eat 动画（数值已在 Panel 扣过）。伴侣不吃。 */
    fun playFeedAnim(foodId: String?) {
        if (musicMode) return
        abortLocomotionSoft()
        val food = foodId?.let { FoodCatalog.byId(it) }
        animator.playPose(listOf(SpriteAssets.EAT1, SpriteAssets.EAT2), 2000L)
        fx?.showFood()
        if (food != null) {
            banter("eat", "eat")
        } else {
            banter("eat", "eat")
        }
    }

    fun openCollect() {
        ModeTimeStore.setBucket(context, "game")
        startActivity(CollectActivity::class.java)
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
        showToast("显示目的地：${if (next) "开" else "关"}")
    }

    fun toggleWorkShowStack() {
        val next = !AppDataStore.workShowStack(context)
        AppDataStore.setWorkShowStack(context, next)
        showToast("显示运送货物：${if (next) "开" else "关"}")
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
        abortLocomotionSoft()
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
            animator.playPose(listOf(SpriteAssets.HI1, SpriteAssets.HI2), hold.coerceAtMost(2800L))
        }, 2300L)
    }

    fun showOwnerInfo() {
        val name = PetPrefs.ownerName(context)
        if (name.isEmpty()) {
            showToast("尚未认主 · 请回主界面填写所属人")
            return
        }
        val days = PetPrefs.companionDays(context)
        ModeTimeStore.flush(context)
        val total = ModeTimeStore.formatDuration(ModeTimeStore.totalSeconds(context))
        showToast("所属人：$name · 相伴第 $days 天 · 时长 $total")
        speak(
            "相伴第 $days 天，合计 $total。\n${ModeTimeStore.detailText(context)}",
            null,
            holdMs = 4200L,
        )
    }

    fun playExpression(id: String) {
        if (musicMode) {
            showToast("音乐模式中暂不触发表情")
            return
        }
        abortLocomotionSoft()
        when (id) {
            "expr_happy" -> {
                animator.setMode(PetAnimator.Mode.HAPPY)
                fx?.showHappy()
                // D04：开心无 banter
            }
            "expr_sad" -> {
                animator.playPose(listOf(SpriteAssets.SAD1, SpriteAssets.SAD2), 2600L)
                fx?.showRain()
                banter("sad")
            }
            "expr_shy" -> {
                animator.playPose(listOf(SpriteAssets.SHY1, SpriteAssets.SHY2), 2200L)
                fx?.showShy()
                // D04：脸红无 banter
            }
            "expr_wink" -> {
                animator.playPose(listOf(SpriteAssets.WINK), 3000L)
                fx?.showWink()
                // D04：wink 无 banter
            }
            "expr_like" -> {
                animator.playPose(listOf(SpriteAssets.LIKE), 2200L)
                fx?.showLike()
                // D04：点赞无 banter
            }
            "expr_angry" -> {
                animator.playPose(listOf(SpriteAssets.WALK_BACK1, SpriteAssets.WALK_BACK2), 1800L)
                fx?.showAngry()
                banter("angry")
            }
            "expr_idea" -> {
                animator.playPose(
                    listOf(SpriteAssets.MOVE1, SpriteAssets.MOVE2, SpriteAssets.MOVE3), 2400L,
                )
                fx?.showBulb()
                // D04：有主意无 banter
            }
            "expr_question" -> {
                animator.playPose(listOf(SpriteAssets.MOVE2, SpriteAssets.MOVE1))
                banter("question")
            }
            "expr_bixin" -> {
                animator.playPose(listOf(SpriteAssets.LIKE), 2000L)
                fx?.showBixin()
                banter("bixin")
            }
            else -> showToast("（后期）表情")
        }
    }

    fun playAction(id: String) {
        if (musicMode && id !in setOf("act_stand", "act_walk")) {
            showToast("音乐模式中暂不触发动作")
            return
        }
        abortLocomotionSoft()
        when (id) {
            "act_hi" -> {
                animator.setMode(PetAnimator.Mode.HI)
                speak(
                    InteractLines.HI_TEXT, "hi", 4200L,
                    forceVoice = true, hiTypewriter = true,
                )
            }
            "act_sleep" -> startSleepInteract()
            "act_walk" -> {
                startStroll()
                banter("walk", "walk")
            }
            "act_stand" -> {
                abortAllModes()
                animator.setMode(PetAnimator.Mode.STAND)
                banter("stand")
            }
            "act_squat" -> {
                animator.playPose(listOf(SpriteAssets.SQUAT))
                // D04：下蹲无 banter
            }
            "act_kick" -> {
                animator.playPose(listOf(SpriteAssets.KICK), 3000L)
                fx?.showKick()
                banter("kick", "kick")
            }
            "act_yes" -> {
                animator.playPose(listOf(SpriteAssets.YES))
                banter("yes")
            }
            "act_no" -> {
                animator.playPose(listOf(SpriteAssets.NO))
                banter("no")
            }
            "act_call" -> {
                animator.playPose(listOf(SpriteAssets.CALL1, SpriteAssets.CALL2), 2800L)
                speak(InteractLines.CALL_TEXT, "call", 4500L, forceVoice = true)
            }
            "act_eat" -> {
                animator.playPose(listOf(SpriteAssets.EAT1, SpriteAssets.EAT2), 2000L)
                fx?.showFood()
                banter("eat", "eat")
            }
            "act_judge" -> playYesNoJudge()
            else -> showToast("（后期）动作")
        }
    }

    private fun playYesNoJudge() {
        speak(InteractLines.YESNO_ANSWER_TEXT, holdMs = 0)
        mainHandler.postDelayed({
            val yes = kotlin.random.Random.nextBoolean()
            if (yes) {
                animator.playPose(listOf(SpriteAssets.YES), 2800L)
                speak("判断结果：${InteractLines.line("yes")}", holdMs = 2800L)
            } else {
                animator.playPose(listOf(SpriteAssets.NO), 2800L)
                speak("判断结果：${InteractLines.line("no")}", holdMs = 2800L)
            }
        }, 5000L)
    }

    private fun abortLocomotionSoft() {
        if (isWorking || isFollowing || isQuiet || isPomodoro || isMusic) abortAllModes()
        else stopLocomotion()
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
        b.pomoEnd.setOnClickListener { endPomodoro(silent = false) }
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
                speech?.showVoiceSubtitle("……", 2200L)
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
        idleActionBusy = true
        walkStepsLeft = 0
        val hold = when (act) {
            "squat" -> {
                animator.playPose(listOf(SpriteAssets.SQUAT))
                // D04 无 banter
                1800L
            }
            "idea" -> {
                animator.playPose(listOf(SpriteAssets.MOVE1, SpriteAssets.MOVE2, SpriteAssets.MOVE3), 2400L)
                fx?.showBulb()
                2400L
            }
            "question" -> {
                animator.playPose(listOf(SpriteAssets.MOVE2, SpriteAssets.MOVE1))
                banter("question")
                1800L
            }
            "sad" -> {
                animator.playPose(listOf(SpriteAssets.SAD1, SpriteAssets.SAD2), 2600L)
                fx?.showRain()
                banter("sad")
                2600L
            }
            "angry" -> {
                animator.playPose(listOf(SpriteAssets.WALK_BACK1, SpriteAssets.WALK_BACK2), 1800L)
                fx?.showAngry()
                banter("angry")
                1800L
            }
            "like" -> {
                animator.playPose(listOf(SpriteAssets.LIKE), 2200L)
                fx?.showLike()
                // D04 点赞无 banter
                2200L
            }
            "happy" -> {
                animator.playPose(listOf(SpriteAssets.HAPPY), 2800L)
                fx?.showHappy()
                2800L
            }
            "hi" -> {
                animator.playPose(listOf(SpriteAssets.HI1, SpriteAssets.HI2), 3000L)
                speak(
                    InteractLines.HI_TEXT, "hi", 4200L,
                    forceVoice = true, hiTypewriter = true,
                )
                3000L
            }
            else -> {
                idleActionBusy = false
                return false
            }
        }
        mainHandler.postDelayed({
            idleActionBusy = false
            if (locomotion == Locomotion.FREE && locomotionEnabled) {
                freeIdleUntil = 0L
                beginWalkBurst(music = false)
            } else {
                animator.setMode(PetAnimator.Mode.STAND)
            }
        }, hold)
        return true
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
}
