from pathlib import Path

p = Path("app/src/main/java/com/vpet/mobile/PetModeHub.kt")
t = p.read_text(encoding="utf-8")

# 1) fields
old = """    private var idleActionBusy = false
    private var freeIdlePulseJob: Runnable? = null
"""
new = """    private var idleActionBusy = false
    private var freeIdlePulseJob: Runnable? = null
    /** 取消叠层的「恢复走动」；世代号防止旧回调抢跑。 */
    private var resumeWalkJob: Runnable? = null
    private var interactGen = 0
"""
if old not in t:
    raise SystemExit("fields missing")
t = t.replace(old, new, 1)
print("fields ok")

# 2) onWalkAnimStep guard
old = """    fun onWalkAnimStep(): Boolean {
        if (videoMode || appGameMode) {
            reassertSceneSprite()
            return false
        }
        if (!locomotionEnabled) return false
"""
new = """    fun onWalkAnimStep(): Boolean {
        // 菜单互动/随机动作进行中：禁止走动与站立随机
        if (idleActionBusy) return false
        if (videoMode || appGameMode) {
            reassertSceneSprite()
            return false
        }
        if (!locomotionEnabled) return false
"""
if old not in t:
    raise SystemExit("onWalkAnimStep missing")
t = t.replace(old, new, 1)
print("walk guard ok")

# 3) playExpression begin
old = """    fun playExpression(id: String) {
        if (musicMode) {
            showToast("音乐模式中暂不触发表情")
            return
        }
        if (videoMode || appGameMode) {
            showToast("场景姿势中暂不触发表情")
            return
        }
        abortLocomotionSoft()
        when (id) {
"""
new = """    fun playExpression(id: String) {
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
"""
if old not in t:
    raise SystemExit("playExpression missing")
t = t.replace(old, new, 1)
print("playExpression ok")

# 4) replace playAction whole function carefully
old = """    fun playAction(id: String) {
        if (musicMode && id !in setOf("act_stand", "act_walk")) {
            showToast("音乐模式中暂不触发动作")
            return
        }
        abortLocomotionSoft()
        when (id) {
            "act_hi" -> {
                animator.playPose(
                    listOf(SpriteAssets.HI1, SpriteAssets.HI2),
                    holdMs = 4200L,
                    loop = true,
                )
                speak(
                    InteractLines.HI_TEXT, "hi", 4200L,
                    forceVoice = true, hiTypewriter = true,
                )
                scheduleResumeWalking(4200L)
            }
            "act_sleep" -> startSleepInteract()
            "act_walk" -> {
                startStroll()
                banter("walk", "walk")
            }
            "act_stand" -> {
                abortAllModes()
                returnToFreeIfIdle(startWalk = false)
                banter("stand")
                scheduleResumeWalking(1600L)
            }
            "act_squat" -> {
                animator.playPose(listOf(SpriteAssets.SQUAT), PetAnimator.DUR_SQUAT, loop = false)
                scheduleResumeWalking(PetAnimator.DUR_SQUAT)
            }
            "act_kick" -> {
                animator.playPose(listOf(SpriteAssets.KICK), PetAnimator.DUR_KICK, loop = false)
                fx?.showKick(PetAnimator.DUR_KICK)
                banter("kick", "kick")
                scheduleResumeWalking(PetAnimator.DUR_KICK)
            }
            "act_yes" -> {
                animator.playPose(listOf(SpriteAssets.YES), PetAnimator.DUR_YES, loop = false)
                banter("yes")
                scheduleResumeWalking(PetAnimator.DUR_YES)
            }
            "act_no" -> {
                animator.playPose(listOf(SpriteAssets.NO), PetAnimator.DUR_NO, loop = false)
                banter("no")
                scheduleResumeWalking(PetAnimator.DUR_NO)
            }
            "act_call" -> {
                animator.playPose(
                    listOf(SpriteAssets.CALL1, SpriteAssets.CALL2),
                    holdMs = 4500L,
                    loop = true,
                )
                speak(InteractLines.CALL_TEXT, "call", 4500L, forceVoice = true)
                scheduleResumeWalking(4500L)
            }
            "act_eat" -> openEatFoodMenu()
            "act_judge" -> playYesNoJudge()
            "act_adult" -> {
                // 对照桌面 _play_adult_reserved：扁平文本框 + 固定文案
                speak(InteractLines.ADULT_CONTENT_TEXT, holdMs = 6500L)
                scheduleResumeWalking(6500L)
            }
            else -> showToast("（后期）动作")
        }
    }
"""
new = """    fun playAction(id: String) {
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
"""
if old not in t:
    raise SystemExit("playAction missing")
t = t.replace(old, new, 1)
print("playAction ok")

# 5) playFeedAnim / playPresetDialog / playYesNoJudge / scheduleResumeWalking
old = """    fun playFeedAnim(foodId: String?) {
        if (musicMode) return
        abortLocomotionSoft()
        animator.playPose(listOf(SpriteAssets.EAT1, SpriteAssets.EAT2), PetAnimator.DUR_EAT, loop = true)
        fx?.showFood(foodId ?: "apple")
        // foodId 预留：后续可按食物换特效贴图
        @Suppress("UNUSED_PARAMETER")
        val fed = foodId
        banter("eat", "eat")
        scheduleResumeWalking(PetAnimator.DUR_EAT)
    }
"""
new = """    fun playFeedAnim(foodId: String?) {
        if (musicMode) return
        beginUserInteract()
        animator.playPose(listOf(SpriteAssets.EAT1, SpriteAssets.EAT2), PetAnimator.DUR_EAT, loop = true)
        fx?.showFood(foodId ?: "apple")
        @Suppress("UNUSED_PARAMETER")
        val fed = foodId
        banter("eat", "eat")
        scheduleResumeWalking(PetAnimator.DUR_EAT)
    }
"""
if old not in t:
    raise SystemExit("playFeedAnim missing")
t = t.replace(old, new, 1)
print("playFeedAnim ok")

old = """    fun playPresetDialog(entry: PresetDialogs.Entry) {
        if (musicMode) return
        abortLocomotionSoft()
"""
new = """    fun playPresetDialog(entry: PresetDialogs.Entry) {
        if (musicMode) return
        beginUserInteract()
"""
if old not in t:
    raise SystemExit("playPresetDialog missing")
t = t.replace(old, new, 1)
print("dialog ok")

old = """    private fun playYesNoJudge() {
        speak(InteractLines.YESNO_ANSWER_TEXT, holdMs = 0)
        mainHandler.postDelayed({
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

    private fun scheduleResumeWalking(afterMs: Long) {
        mainHandler.postDelayed({
            resumeWalkingAfterPause()
        }, afterMs.coerceAtLeast(200L))
    }

    private fun abortLocomotionSoft() {
"""
new = """    private fun playYesNoJudge() {
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
"""
if old not in t:
    raise SystemExit("scheduleResumeWalking block missing")
t = t.replace(old, new, 1)
print("resume/interact ok")

# 6) fireIdleAction - avoid double schedule for angry/hi; use beginUserInteract + scheduleResumeWalking
old = """    private fun fireIdleAction(act: String): Boolean {
        idleActionBusy = true
        walkStepsLeft = 0
        val hold = when (act) {
            "squat" -> {
                animator.playPose(listOf(SpriteAssets.SQUAT), PetAnimator.DUR_SQUAT, loop = false)
                PetAnimator.DUR_SQUAT
            }
            "idea" -> {
                fx?.showBulb(PetAnimator.IDEA_STAND_MS + PetAnimator.DUR_IDEA)
                animator.playTimedPose(
                    listOf(
                        SpriteAssets.STAND to PetAnimator.IDEA_STAND_MS,
                        SpriteAssets.EAT2 to PetAnimator.DUR_IDEA,
                    ),
                )
                PetAnimator.IDEA_STAND_MS + PetAnimator.DUR_IDEA
            }
            "question" -> {
                animator.playPose(
                    listOf(SpriteAssets.STAND_QUESTION),
                    PetAnimator.DUR_QUESTION,
                    loop = false,
                )
                banter("question")
                PetAnimator.DUR_QUESTION
            }
            "sad" -> {
                animator.playTimedPose(
                    listOf(
                        SpriteAssets.SQUAT to PetAnimator.SAD_SQUAT_MS,
                        SpriteAssets.SAD1 to PetAnimator.SAD_SAD1_MS,
                        SpriteAssets.SAD2 to PetAnimator.SAD_SAD2_MS,
                    ),
                )
                fx?.showRain(PetAnimator.DUR_SAD)
                banter("sad")
                PetAnimator.DUR_SAD
            }
            "angry" -> {
                playExpression("expr_angry")
                PetAnimator.DUR_ANGRY + 10 * PetAnimator.ANGRY_FRAME_MS
            }
            "happy" -> {
                animator.setMode(PetAnimator.Mode.HAPPY)
                fx?.showHappy()
                PetAnimator.DUR_HAPPY
            }
            "like" -> {
                animator.playPose(listOf(SpriteAssets.LIKE), PetAnimator.DUR_LIKE, loop = false)
                fx?.showLike()
                PetAnimator.DUR_LIKE
            }
            "hi" -> {
                playAction("act_hi")
                4200L
            }
            else -> {
                idleActionBusy = false
                return false
            }
        }
        mainHandler.postDelayed({
            idleActionBusy = false
            resumeWalkingAfterPause()
        }, hold)
        return true
    }
"""
new = """    private fun fireIdleAction(act: String): Boolean {
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
"""
if old not in t:
    raise SystemExit("fireIdleAction missing")
t = t.replace(old, new, 1)
print("fireIdleAction ok")

# 7) destroy cancel resume
old = """    fun destroy() {
        stopMetaIdlePoll()
        stopHungerPoll()
        clearWorkTimer()
        clearSleepInteract()
"""
new = """    fun destroy() {
        endUserInteractHold()
        stopMetaIdlePoll()
        stopHungerPoll()
        clearWorkTimer()
        clearSleepInteract()
"""
if old not in t:
    raise SystemExit("destroy missing")
t = t.replace(old, new, 1)
print("destroy ok")

# 8) maybeFreeIdlePulse also check video/game
old = """    private fun maybeFreeIdlePulse() {
        if (locomotion != Locomotion.FREE || musicMode || idleActionBusy) return
        if (isWorking || isFollowing || isQuiet || isPomodoro || isCollecting) return
"""
new = """    private fun maybeFreeIdlePulse() {
        if (locomotion != Locomotion.FREE || musicMode || idleActionBusy) return
        if (isWorking || isFollowing || isQuiet || isPomodoro || isCollecting) return
        if (videoMode || appGameMode) return
"""
if old not in t:
    raise SystemExit("maybeFreeIdlePulse missing")
t = t.replace(old, new, 1)
print("pulse ok")

p.write_text(t, encoding="utf-8")
print("DONE")
