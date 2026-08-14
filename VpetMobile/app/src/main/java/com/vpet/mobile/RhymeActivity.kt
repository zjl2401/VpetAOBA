package com.vpet.mobile

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.TypedValue
import androidx.appcompat.app.AppCompatActivity
import com.vpet.mobile.databinding.ActivityRhymeBinding
import kotlin.math.max
import kotlin.random.Random

/**
 * 莱姆回合制：选招 → 掷骰画面判定 → 同时结算（对照桌面 `_begin_rhyme_fight`）。
 * 败后首次触发金目觉醒秒杀；真正战败保留约 1.6s。
 */
class RhymeActivity : AppCompatActivity() {
    companion object {
        const val LOSE_HOLD_MS = 1600L
        private const val SPECIAL_COOLDOWN = 3
        private val ACTION_NAME = mapOf(
            "attack" to "攻击",
            "defense" to "防御",
            "special" to "必杀",
        )
    }

    private lateinit var binding: ActivityRhymeBinding
    private val handler = Handler(Looper.getMainLooper())

    private var playerHp = 100
    private var enemyHp = 100
    private val playerMax = 100
    private val enemyMax = 100
    private var round = 1
    private var phase = "choose" // choose | judge | resolve
    private var over = false
    private var specialReadyRound = 1
    private var enemySpecialReadyRound = 1
    private var jinmu = false
    private var jinmuUsed = false
    private var pendingPlayer = ""
    private var pendingEnemy = ""
    private var playerRoll = 0
    private var enemyRoll = 0
    private var logText = "第 1 回合 · 请选择攻击 / 防御 / 必杀（随后掷骰判定）"
    private var difficulty = "中"
    private var difficultyT = 0.5f
    private var playerMult = 1f
    private var enemyMult = 1f
    private var barW = 280
    private var dieSize = 48
    private var iconSize = 56

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityRhymeBinding.inflate(layoutInflater)
        setContentView(binding.root)
        OverlayGate.pause(this)
        FirstPlayGuides.maybeShow(this, "rhyme")

        difficulty = AppDataStore.difficulty(this)
        difficultyT = PixelFightArt.difficultyT(difficulty)
        playerMult = PixelFightArt.playerMult(difficulty)
        enemyMult = PixelFightArt.enemyMult(difficulty)
        val dens = resources.displayMetrics.density
        barW = (resources.displayMetrics.widthPixels - (16 * dens * 2 + 72 * dens + 40 * dens)).toInt()
            .coerceAtLeast(120)
        dieSize = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, 48f, resources.displayMetrics).toInt()
        iconSize = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, 56f, resources.displayMetrics).toInt()

        binding.rhymePlayerIcon.setImageBitmap(PixelFightArt.fighterBitmap(iconSize, "player"))
        binding.rhymeEnemyIcon.setImageBitmap(PixelFightArt.fighterBitmap(iconSize, "opponent"))
        binding.rhymePlayerDie.setImageBitmap(PixelFightArt.dieBitmap(dieSize, 1))
        binding.rhymeEnemyDie.setImageBitmap(PixelFightArt.dieBitmap(dieSize, 1))

        binding.btnAttack.setOnClickListener { onPlayerChoose("attack") }
        binding.btnDefense.setOnClickListener { onPlayerChoose("defense") }
        binding.btnSpecial.setOnClickListener { onPlayerChoose("special") }
        binding.btnRoll.setOnClickListener { animateDiceThenResolve() }
        binding.btnRhymeExit.setOnClickListener { finish() }

        setChooseButtons(true)
        setRollEnabled(false)
        refreshUi()
    }

    override fun onDestroy() {
        handler.removeCallbacksAndMessages(null)
        OverlayGate.resume(this)
        super.onDestroy()
    }

    private fun specialReady(): Boolean = round >= specialReadyRound

    private fun setChooseButtons(enabled: Boolean) {
        if (!enabled) {
            binding.btnAttack.isEnabled = false
            binding.btnDefense.isEnabled = false
            binding.btnSpecial.isEnabled = false
            return
        }
        binding.btnAttack.isEnabled = true
        binding.btnDefense.isEnabled = true
        refreshSpecialBtn()
    }

    private fun setRollEnabled(enabled: Boolean) {
        binding.btnRoll.isEnabled = enabled
    }

    private fun refreshSpecialBtn() {
        if (over || jinmu || phase != "choose") {
            binding.btnSpecial.isEnabled = false
            binding.btnSpecial.text = "必杀"
            return
        }
        if (!specialReady()) {
            val left = max(1, specialReadyRound - round)
            binding.btnSpecial.isEnabled = false
            binding.btnSpecial.text = "必杀 ${left}回合"
        } else {
            binding.btnSpecial.isEnabled = true
            binding.btnSpecial.text = "必杀"
        }
    }

    private fun refreshUi() {
        val pFill = if (jinmu) "#44DDFF" else "#44FF88"
        binding.rhymePlayerBar.setImageBitmap(
            PixelFightArt.hpBarBitmap(barW, 16, playerHp, playerMax, pFill),
        )
        binding.rhymeEnemyBar.setImageBitmap(
            PixelFightArt.hpBarBitmap(barW, 16, enemyHp, enemyMax, "#FF8844"),
        )
        binding.rhymePlayerHp.text = playerHp.toString()
        binding.rhymeEnemyHp.text = enemyHp.toString()
        if (playerRoll in 1..6) {
            binding.rhymePlayerDie.setImageBitmap(PixelFightArt.dieBitmap(dieSize, playerRoll))
        }
        if (enemyRoll in 1..6) {
            binding.rhymeEnemyDie.setImageBitmap(PixelFightArt.dieBitmap(dieSize, enemyRoll))
        }
        when {
            jinmu -> {
                binding.rhymePhase.text = "阶段 2 · 金目觉醒  [$difficulty]"
                binding.rhymePhase.setTextColor(0xFFFF66AA.toInt())
                binding.rhymeYouName.text = "金目 耐久"
                binding.rhymeYouName.setTextColor(0xFF66B0EE.toInt())
                binding.rhymeDiceHint.text = ""
            }
            phase == "judge" -> {
                binding.rhymePhase.text = "第 $round 回合 · 掷骰判定  [$difficulty]"
                binding.rhymePhase.setTextColor(0xFFCC99FF.toInt())
                binding.rhymeYouName.text = "你 耐久"
                binding.rhymeYouName.setTextColor(0xFF88CCFF.toInt())
                val need = PixelFightArt.diceThreshold(pendingPlayer.ifBlank { "attack" }, difficultyT)
                binding.rhymeDiceHint.text =
                    if (pendingPlayer == "defense") "完美格挡 ≥$need" else "你需 ≥$need"
            }
            phase == "resolve" -> {
                binding.rhymePhase.text = "第 $round 回合 · 结算  [$difficulty]"
                binding.rhymePhase.setTextColor(0xFFFFCC66.toInt())
                binding.rhymeYouName.text = "你 耐久"
                binding.rhymeYouName.setTextColor(0xFF88CCFF.toInt())
                binding.rhymeDiceHint.text = ""
            }
            else -> {
                binding.rhymePhase.text = "第 $round 回合 · 选招  [$difficulty]"
                binding.rhymePhase.setTextColor(0xFFAAAAAA.toInt())
                binding.rhymeYouName.text = "你 耐久"
                binding.rhymeYouName.setTextColor(0xFF88CCFF.toInt())
                binding.rhymeDiceHint.text = "选招后掷骰判定成败"
            }
        }
        binding.rhymeLog.text = logText
        refreshSpecialBtn()
    }

    private fun pickEnemyAction(): String {
        val canSpecial = round >= enemySpecialReadyRound
        if (canSpecial && enemyHp <= 45 && Random.nextFloat() < 0.45f) return "special"
        if (playerHp >= 70 && enemyHp <= 55 && Random.nextFloat() < 0.35f) return "defense"
        if (Random.nextFloat() < 0.22f) return "defense"
        if (canSpecial && Random.nextFloat() < 0.18f) return "special"
        return "attack"
    }

    private fun calcOutgoing(action: String, player: Boolean, roll: Int): Pair<Int, String> {
        val mult = if (player) playerMult else enemyMult
        val need = PixelFightArt.diceThreshold(action, difficultyT)
        if (action == "defense") return 0 to "防御"
        if (roll < need) {
            return 0 to if (action == "special") "必杀判定失败" else "攻击未中"
        }
        if (action == "special") {
            val dmg = (22 * mult).toInt()
            return if (roll >= 6) (dmg * 1.35f).toInt() to "必杀暴击" else dmg to "必杀"
        }
        val dmg = (12 * mult).toInt()
        return if (roll >= 6) (dmg * 1.4f).toInt() to "攻击暴击" else dmg to "攻击"
    }

    private fun applyBlock(dmg: Int, defenderAction: String, defenderRoll: Int): Pair<Int, String> {
        if (dmg <= 0) return 0 to ""
        if (defenderAction != "defense") return dmg to ""
        val need = PixelFightArt.diceThreshold("defense", difficultyT)
        return if (defenderRoll >= need) {
            max(1, dmg / 5) to "完美格挡"
        } else {
            max(1, dmg / 3) to "格挡"
        }
    }

    private fun onPlayerChoose(action: String) {
        if (over || jinmu || phase != "choose") return
        if (action == "special" && !specialReady()) {
            logText = "必杀冷却中（还需 ${max(1, specialReadyRound - round)} 回合）"
            refreshUi()
            return
        }
        phase = "judge"
        pendingPlayer = action
        pendingEnemy = pickEnemyAction()
        playerRoll = 0
        enemyRoll = 0
        setChooseButtons(false)
        setRollEnabled(true)
        val need = PixelFightArt.diceThreshold(action, difficultyT)
        val tip = if (action == "defense") "完美格挡需 ≥$need" else "成功需 ≥$need（6=暴击）"
        logText = "你选择了${ACTION_NAME[action]}！\n$tip\n点击「掷骰判定」"
        refreshUi()
    }

    private fun animateDiceThenResolve() {
        if (over || phase != "judge") return
        setRollEnabled(false)
        val finalP = Random.nextInt(1, 7)
        val finalE = Random.nextInt(1, 7)
        var i = 0
        val tick = object : Runnable {
            override fun run() {
                if (over || isFinishing) return
                i++
                if (i < 8) {
                    binding.rhymePlayerDie.setImageBitmap(PixelFightArt.dieBitmap(dieSize, Random.nextInt(1, 7)))
                    binding.rhymeEnemyDie.setImageBitmap(PixelFightArt.dieBitmap(dieSize, Random.nextInt(1, 7)))
                    logText = "骰子转动中…"
                    binding.rhymeLog.text = logText
                    handler.postDelayed(this, 55)
                    return
                }
                playerRoll = finalP
                enemyRoll = finalE
                binding.rhymePlayerDie.setImageBitmap(PixelFightArt.dieBitmap(dieSize, finalP))
                binding.rhymeEnemyDie.setImageBitmap(PixelFightArt.dieBitmap(dieSize, finalE))
                val pa = pendingPlayer
                val ea = pendingEnemy
                logText = "判定结果：你 $finalP 点｜对手 $finalE 点"
                refreshUi()
                handler.postDelayed({ resolveRound(pa, ea, finalP, finalE) }, 500)
            }
        }
        handler.post(tick)
    }

    private fun resolveRound(playerAction: String, enemyAction: String, pRoll: Int, eRoll: Int) {
        if (over || jinmu) return
        if (playerAction == "special") specialReadyRound = round + SPECIAL_COOLDOWN
        if (enemyAction == "special") enemySpecialReadyRound = round + SPECIAL_COOLDOWN

        val (pRaw, pTag) = calcOutgoing(playerAction, player = true, roll = pRoll)
        val (eRaw, eTag) = calcOutgoing(enemyAction, player = false, roll = eRoll)
        val (pDmg, pBlock) = applyBlock(pRaw, enemyAction, eRoll)
        val (eDmg, eBlock) = applyBlock(eRaw, playerAction, pRoll)

        enemyHp = max(0, enemyHp - pDmg)
        playerHp = max(0, playerHp - eDmg)
        phase = "resolve"

        val lines = mutableListOf(
            "第 $round 回合结算  骰子 你$pRoll｜对手$eRoll",
            "你：${ACTION_NAME[playerAction]}｜对手：${ACTION_NAME[enemyAction]}",
        )
        when {
            playerAction == "defense" ->
                lines += "你进入防御姿态" + if (eBlock == "完美格挡") "（完美格挡）" else ""
            pTag == "攻击未中" || pTag == "必杀判定失败" ->
                lines += "你的${ACTION_NAME[playerAction]}判定失败！"
            pDmg > 0 ->
                lines += "你$pTag 造成 $pDmg 伤害" + if (pBlock.isNotEmpty()) "（$pBlock）" else ""
            else -> lines += "你本回合未造成伤害"
        }
        when {
            enemyAction == "defense" ->
                lines += "对手进入防御姿态" + if (pBlock == "完美格挡") "（完美格挡）" else ""
            eTag == "攻击未中" || eTag == "必杀判定失败" ->
                lines += "对手${ACTION_NAME[enemyAction]}判定失败！"
            eDmg > 0 ->
                lines += "对手$eTag 造成 $eDmg 伤害" + if (eBlock.isNotEmpty()) "（$eBlock）" else ""
            else -> lines += "对手本回合未造成伤害"
        }
        logText = lines.joinToString("\n")
        refreshUi()

        when {
            enemyHp <= 0 -> handler.postDelayed({ endFight(won = true) }, 700)
            playerHp <= 0 -> {
                if (!jinmuUsed) {
                    handler.postDelayed({ awakenJinmu() }, 650)
                } else {
                    handler.postDelayed({ endFight(won = false) }, 700)
                }
            }
            else -> handler.postDelayed({ beginNextRound() }, 1600)
        }
    }

    private fun beginNextRound() {
        if (over || jinmu) return
        round++
        phase = "choose"
        pendingPlayer = ""
        pendingEnemy = ""
        playerRoll = 0
        enemyRoll = 0
        logText = "第 $round 回合 · 请选择攻击 / 防御 / 必杀"
        setChooseButtons(true)
        setRollEnabled(false)
        refreshUi()
    }

    private fun awakenJinmu() {
        if (jinmuUsed || over) return
        jinmuUsed = true
        jinmu = true
        phase = "resolve"
        setChooseButtons(false)
        setRollEnabled(false)
        playerHp = max(45, (playerMax * 0.55f).toInt())
        logText = "耐久归零…第二人格·金目觉醒！"
        binding.rhymePlayerIcon.setImageBitmap(PixelFightArt.fighterBitmap(iconSize, "jinmu"))
        refreshUi()
        handler.postDelayed({
            if (over || isFinishing) return@postDelayed
            logText = "金目开始自动攻击…"
            refreshUi()
            handler.postDelayed({
                if (over || isFinishing) return@postDelayed
                logText = "金目：零距离切段——秒杀！"
                enemyHp = 0
                refreshUi()
                handler.postDelayed({ endFight(won = true) }, 650)
            }, 900)
        }, 700)
    }

    private fun endFight(won: Boolean) {
        if (over) return
        over = true
        phase = "resolve"
        setChooseButtons(false)
        setRollEnabled(false)
        if (won) {
            val moodGain = if (jinmu) 10 else 5
            AppDataStore.addStaminaMood(this, -5, moodGain)
            logText = if (jinmu) "金目接管结束。对手：…什么人？" else "你赢了！对手：下次我不会输的…"
            refreshUi()
            GameClearUi.show(
                this,
                title = "胜利！",
                subtitle = if (jinmu) "第二人格·金目 秒杀胜利" else "莱姆对战通关",
                accentHex = if (jinmu) "#66B0EE" else "#FF8844",
                onDismiss = { finish() },
            )
        } else {
            AppDataStore.addStaminaMood(this, -10, -8)
            logText = "输了…对手：承让啦~"
            binding.rhymeLog.setTextColor(0xFFFF6688.toInt())
            refreshUi()
            GameFailVoice.playHurt(this)
            handler.postDelayed({ finish() }, LOSE_HOLD_MS)
        }
    }
}
