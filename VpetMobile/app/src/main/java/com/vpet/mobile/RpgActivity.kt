package com.vpet.mobile

import android.animation.AnimatorListenerAdapter
import android.animation.AnimatorSet
import android.animation.ObjectAnimator
import android.content.Intent
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.Typeface
import android.os.Bundle
import android.view.View
import android.view.animation.DecelerateInterpolator
import android.widget.Button
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.vpet.mobile.databinding.ActivityRpgBinding
import kotlin.random.Random

/** Silent Oath：开场（蓝底双 logo）+ Start 菜单 + 选角战役 + DIY。 */
class RpgActivity : AppCompatActivity() {
    private lateinit var binding: ActivityRpgBinding
    private var settling = false
    private var campaignFrom = 0
    private var runCoins = 0
    private var runTreasures = 0
    private var playerKind = "knight"
    private var bgm: RpgBgm? = null
    private var introAnim: AnimatorSet? = null
    private var introEnded = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityRpgBinding.inflate(layoutInflater)
        setContentView(binding.root)
        OverlayGate.pause(this)
        AppDataStore.unlock(this, "rpg_play")
        bgm = RpgBgm(this)
        playerKind = prefs().getString("rpg_player_kind", "knight") ?: "knight"

        stylePixelMenu(binding.btnRpgStartPlay)
        stylePixelMenu(binding.btnRpgStartDiy)
        stylePixelMenu(binding.btnRpgStartBack)

        for (meta in RpgMapLoader.CAMPAIGN) {
            binding.rpgLevelList.addView(
                Button(this).apply {
                    text = meta.name
                    setOnClickListener { pickKindThen { startCampaign(meta.idx) } }
                },
            )
        }
        binding.btnRpgDiy.setOnClickListener {
            pickKindThen {
                val map = RpgMapLoader.loadDiy001(this)
                if (map == null) Toast.makeText(this, "diy_001 加载失败", Toast.LENGTH_SHORT).show()
                else {
                    campaignFrom = -1
                    enterPlay(map)
                }
            }
        }
        binding.btnRpgEditor.setOnClickListener {
            startActivity(Intent(this, RpgDiyEditorActivity::class.java))
        }
        binding.btnRpgMenuBack.setOnClickListener { finish() }
        binding.btnRpgBack.setOnClickListener { showMenu() }

        binding.btnRpgStartPlay.setOnClickListener { showCampaignMenu() }
        binding.btnRpgStartDiy.setOnClickListener {
            startActivity(Intent(this, RpgDiyEditorActivity::class.java))
        }
        binding.btnRpgStartBack.setOnClickListener { finish() }
        binding.rpgIntroSkip.setOnClickListener { finishIntroAnim(showMenuButtons = true) }

        intent.getStringExtra(RpgDiyEditorActivity.EXTRA_PLAY_PATH)?.let { path ->
            val map = RpgMapLoader.loadFromFile(path)
            if (map != null) {
                campaignFrom = -2
                binding.rpgStart.visibility = View.GONE
                binding.rpgIntro.visibility = View.GONE
                pickKindThen { enterPlay(map) }
                return
            }
        }

        binding.rpgView.listener = object : RpgView.Listener {
            override fun onHud(hp: Int, coins: Int, treasures: Int, layer: String, msg: String?) {
                binding.rpgHud.text = "HP $hp · 金 $coins · 箱 $treasures · $layer"
                if (!msg.isNullOrBlank()) {
                    Toast.makeText(this@RpgActivity, msg, Toast.LENGTH_SHORT).show()
                }
            }
            override fun onTreasure(tx: Int, ty: Int) = beginChestEvent(tx, ty)
            override fun onLevelClear(coins: Int, treasures: Int, levelIdx: Int) {
                if (settling) return
                runCoins += coins
                runTreasures += treasures
                if (campaignFrom >= 0 && levelIdx >= 0 && levelIdx + 1 < RpgMapLoader.CAMPAIGN.size) {
                    val next = RpgMapLoader.CAMPAIGN[levelIdx + 1]
                    Toast.makeText(this@RpgActivity, "通关！进入 ${next.name}", Toast.LENGTH_SHORT).show()
                    val map = RpgMapLoader.loadCampaign(this@RpgActivity, next.asset)
                    if (map != null) {
                        binding.rpgView.loadLevel(map)
                        return
                    }
                }
                finishCampaign(runCoins)
            }
            override fun onDead() {
                Toast.makeText(this@RpgActivity, "倒下了…返回菜单", Toast.LENGTH_LONG).show()
                showMenu()
            }
        }

        playIntro()
    }

    private fun stylePixelMenu(tv: View) {
        if (tv !is android.widget.TextView) return
        tv.typeface = Typeface.MONOSPACE
        tv.setTextColor(Color.WHITE)
        tv.setShadowLayer(2f, 1f, 1f, 0x88000000.toInt())
    }

    override fun onDestroy() {
        introAnim?.cancel()
        binding.rpgStart.removeCallbacks(null)
        bgm?.stop()
        bgm = null
        OverlayGate.resume(this)
        super.onDestroy()
    }

    private fun loadAssetBmp(path: String) = try {
        assets.open(path).use { BitmapFactory.decodeStream(it) }
    } catch (_: Exception) {
        null
    }

    /** 从 startcolor.png 采样主蓝，作大面积纯色底（不用整张 start 插画）。 */
    private fun applyStartBlueBg() {
        val bmp = loadAssetBmp("rpg/ui/startcolor.png")
        val color = if (bmp != null && !bmp.isRecycled) {
            val x = (bmp.width * 0.5f).toInt().coerceIn(0, bmp.width - 1)
            val y = (bmp.height * 0.5f).toInt().coerceIn(0, bmp.height - 1)
            bmp.getPixel(x, y) or 0xFF000000.toInt()
        } else {
            Color.parseColor("#456890")
        }
        binding.rpgStartBgColor.setBackgroundColor(color)
    }

    private fun playIntro() {
        introEnded = false
        binding.rpgStart.visibility = View.VISIBLE
        binding.rpgIntro.visibility = View.GONE
        binding.rpgMenu.visibility = View.GONE
        binding.rpgView.visibility = View.GONE
        binding.rpgPlayHud.visibility = View.GONE
        applyStartBlueBg()
        loadAssetBmp("rpg/ui/startlogo1.png")?.let { binding.rpgStartLogo1.setImageBitmap(it) }
        loadAssetBmp("rpg/ui/startlogo2.png")?.let { binding.rpgStartLogo2.setImageBitmap(it) }
        binding.rpgStartMenu.alpha = 0f
        binding.rpgStartMenu.visibility = View.INVISIBLE
        binding.rpgIntroSkip.visibility = View.VISIBLE
        bgm?.playIntroOnly()

        binding.rpgStart.post {
            val h = binding.rpgStart.height.coerceAtLeast(1).toFloat()
            val l1 = binding.rpgStartLogo1
            val l2 = binding.rpgStartLogo2
            // 布局已在顶部；用 translationY 飞入，终点同在上 1/4，且同时结束
            val end1 = 0f
            val end2 = 0f
            val start1 = -h * 0.28f
            val start2 = h * 0.38f
            l1.alpha = 0f
            l2.alpha = 0f
            l1.translationY = start1
            l2.translationY = start2
            val dur = 1600L
            val a1 = AnimatorSet().apply {
                playTogether(
                    ObjectAnimator.ofFloat(l1, View.ALPHA, 0f, 1f),
                    ObjectAnimator.ofFloat(l1, View.TRANSLATION_Y, start1, end1),
                )
                duration = dur
                interpolator = DecelerateInterpolator()
            }
            val a2 = AnimatorSet().apply {
                playTogether(
                    ObjectAnimator.ofFloat(l2, View.ALPHA, 0f, 1f),
                    ObjectAnimator.ofFloat(l2, View.TRANSLATION_Y, start2, end2),
                )
                duration = dur
                interpolator = DecelerateInterpolator()
            }
            introAnim = AnimatorSet().apply {
                playTogether(a1, a2)
                addListener(object : AnimatorListenerAdapter() {
                    override fun onAnimationEnd(animation: android.animation.Animator) {
                        finishIntroAnim(showMenuButtons = true)
                    }
                })
                start()
            }
        }
    }

    private fun finishIntroAnim(showMenuButtons: Boolean) {
        if (introEnded) return
        introEnded = true
        introAnim?.cancel()
        introAnim = null
        binding.rpgIntroSkip.visibility = View.GONE
        binding.rpgStartLogo1.alpha = 1f
        binding.rpgStartLogo2.alpha = 1f
        binding.rpgStartLogo1.translationY = 0f
        binding.rpgStartLogo2.translationY = 0f
        if (showMenuButtons) {
            binding.rpgStartMenu.visibility = View.VISIBLE
            binding.rpgStartMenu.animate().alpha(1f).setDuration(400L).start()
        }
    }

    private fun showCampaignMenu() {
        bgm?.stop()
        binding.rpgStart.visibility = View.GONE
        binding.rpgIntro.visibility = View.GONE
        binding.rpgView.visibility = View.GONE
        binding.rpgPlayHud.visibility = View.GONE
        binding.rpgMenu.visibility = View.VISIBLE
    }

    private fun prefs() = getSharedPreferences("vpet_rpg", MODE_PRIVATE)

    private fun pickKindThen(then: () -> Unit) {
        val labels = RpgView.PLAYER_KINDS.map { RpgView.kindLabel(it) }.toTypedArray()
        val cur = RpgView.PLAYER_KINDS.indexOf(playerKind).coerceAtLeast(0)
        AlertDialog.Builder(this)
            .setTitle("选择角色")
            .setSingleChoiceItems(labels, cur) { _, which ->
                playerKind = RpgView.PLAYER_KINDS[which]
            }
            .setPositiveButton("出发") { _, _ ->
                prefs().edit().putString("rpg_player_kind", playerKind).apply()
                then()
            }
            .setNegativeButton("取消", null)
            .show()
    }

    private fun beginChestEvent(tx: Int, ty: Int) {
        val mode = if (Random.nextBoolean()) "dice" else "rps"
        if (mode == "dice") {
            RpgJudgeUi.showDice(
                this,
                onResult = { won, detail ->
                    val msg = binding.rpgView.finishChest(tx, ty, won)
                    AlertDialog.Builder(this)
                        .setTitle(if (won) "成功！" else "失败…")
                        .setMessage("$detail\n$msg")
                        .setPositiveButton("好", null)
                        .show()
                },
                onCancel = { binding.rpgView.cancelChest() },
            )
        } else {
            showRpsPick(tx, ty)
        }
    }

    /** 猜拳：像素图标选拳 + 对手出拳动画。 */
    private fun showRpsPick(tx: Int, ty: Int) {
        RpgJudgeUi.showRps(
            this,
            onResult = { won, detail ->
                val msg = binding.rpgView.finishChest(tx, ty, won)
                AlertDialog.Builder(this)
                    .setTitle(if (won) "成功！" else "失败…")
                    .setMessage("$detail\n$msg")
                    .setPositiveButton("好", null)
                    .show()
            },
            onCancel = { binding.rpgView.cancelChest() },
            onTieRetry = { showRpsPick(tx, ty) },
        )
    }

    private fun startCampaign(fromIdx: Int) {
        campaignFrom = fromIdx
        runCoins = 0
        runTreasures = 0
        settling = false
        val meta = RpgMapLoader.CAMPAIGN[fromIdx]
        val map = RpgMapLoader.loadCampaign(this, meta.asset)
        if (map == null) {
            Toast.makeText(this, "关卡加载失败", Toast.LENGTH_SHORT).show()
            return
        }
        enterPlay(map)
    }

    private fun enterPlay(map: RpgMapLoader.CampaignMap) {
        settling = false
        binding.rpgIntro.visibility = View.GONE
        binding.rpgStart.visibility = View.GONE
        binding.rpgMenu.visibility = View.GONE
        binding.rpgView.visibility = View.VISIBLE
        binding.rpgPlayHud.visibility = View.VISIBLE
        binding.rpgView.setPlayerKind(playerKind)
        binding.rpgView.loadLevel(map)
        bgm?.startAdventure()
    }

    private fun showMenu() {
        bgm?.stop()
        binding.rpgView.visibility = View.GONE
        binding.rpgPlayHud.visibility = View.GONE
        binding.rpgMenu.visibility = View.VISIBLE
        settling = false
        runCoins = 0
        runTreasures = 0
    }

    private fun finishCampaign(coins: Int) {
        if (settling) return
        settling = true
        bgm?.stop()
        val gain = coins.coerceAtLeast(0)
        if (gain > 0) WalletStore.grantCoins(this, gain)
        AppDataStore.addStaminaMood(this, -5, 8)
        val bal = WalletStore.coins(this)
        GameClearUi.show(
            this,
            title = if (campaignFrom >= 0) "战役通关！" else "DIY 通关！",
            subtitle = "本局金币 $gain · 宝箱 $runTreasures → 钱包 $bal\n心情 +8 · 体力 -5",
            accentHex = "#44CC88",
            onDismiss = { showMenu() },
        )
    }
}
