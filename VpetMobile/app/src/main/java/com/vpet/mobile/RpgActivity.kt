package com.vpet.mobile

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.vpet.mobile.databinding.ActivityRpgBinding
import kotlin.random.Random

/** Silent Oath：选角 + 战役连关 + 宝箱判定 + BGM + DIY 试玩。 */
class RpgActivity : AppCompatActivity() {
    private lateinit var binding: ActivityRpgBinding
    private var settling = false
    private var campaignFrom = 0
    private var runCoins = 0
    private var runTreasures = 0
    private var playerKind = "knight"
    private var bgm: RpgBgm? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityRpgBinding.inflate(layoutInflater)
        setContentView(binding.root)
        AppDataStore.unlock(this, "rpg_play")
        bgm = RpgBgm(this)
        playerKind = prefs().getString("rpg_player_kind", "knight") ?: "knight"

        refreshMenuKindHint()
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
                if (map == null) {
                    Toast.makeText(this, "diy_001 加载失败", Toast.LENGTH_SHORT).show()
                } else {
                    campaignFrom = -1
                    enterPlay(map)
                }
            }
        }
        binding.btnRpgEditor.setOnClickListener {
            startActivity(Intent(this, RpgDiyEditorActivity::class.java))
        }
        binding.btnRpgMenuBack.setOnClickListener { finish() }

        intent.getStringExtra(RpgDiyEditorActivity.EXTRA_PLAY_PATH)?.let { path ->
            val map = RpgMapLoader.loadFromFile(path)
            if (map != null) {
                campaignFrom = -2
                pickKindThen { enterPlay(map) }
            }
        }
        binding.btnRpgBack.setOnClickListener { showMenu() }

        binding.rpgView.listener = object : RpgView.Listener {
            override fun onHud(hp: Int, coins: Int, treasures: Int, layer: String, msg: String?) {
                binding.rpgHud.text = "HP $hp · 金 $coins · 箱 $treasures · $layer"
                if (!msg.isNullOrBlank()) {
                    Toast.makeText(this@RpgActivity, msg, Toast.LENGTH_SHORT).show()
                }
            }

            override fun onTreasure(tx: Int, ty: Int) {
                beginChestEvent(tx, ty)
            }

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
    }

    override fun onDestroy() {
        bgm?.stop()
        bgm = null
        super.onDestroy()
    }

    private fun prefs() = getSharedPreferences("vpet_rpg", MODE_PRIVATE)

    private fun refreshMenuKindHint() {
        // 菜单副标题在 layout 里是静态文案；用 Toast/Hud 提示当前角色
    }

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
            AlertDialog.Builder(this)
                .setTitle("宝箱判定：掷骰子")
                .setMessage("需 ≥4 点才能打开。点「掷骰」试试手气。")
                .setPositiveButton("掷骰") { _, _ ->
                    val roll = Random.nextInt(1, 7)
                    val won = roll >= 4
                    val detail = "你掷出 $roll 点"
                    val msg = binding.rpgView.finishChest(tx, ty, won)
                    AlertDialog.Builder(this)
                        .setTitle(if (won) "成功！" else "失败…")
                        .setMessage("$detail\n$msg")
                        .setPositiveButton("好", null)
                        .show()
                }
                .setNegativeButton("取消") { _, _ -> binding.rpgView.cancelChest() }
                .setOnCancelListener { binding.rpgView.cancelChest() }
                .show()
        } else {
            AlertDialog.Builder(this)
                .setTitle("宝箱判定：猜拳")
                .setMessage("选你的出拳（对手随机）")
                .setItems(arrayOf("石头", "剪刀", "布")) { _, which ->
                    val pr = which + 1
                    val er = Random.nextInt(1, 4)
                    val res = rpsBeats(pr, er)
                    val names = arrayOf("", "石头", "剪刀", "布")
                    when (res) {
                        0 -> {
                            Toast.makeText(this, "平局！再来一次", Toast.LENGTH_SHORT).show()
                            beginChestEvent(tx, ty)
                        }
                        else -> {
                            val won = res > 0
                            val detail = "你出${names[pr]} · 对手出${names[er]}"
                            val msg = binding.rpgView.finishChest(tx, ty, won)
                            AlertDialog.Builder(this)
                                .setTitle(if (won) "成功！" else "失败…")
                                .setMessage("$detail\n$msg")
                                .setPositiveButton("好", null)
                                .show()
                        }
                    }
                }
                .setNegativeButton("取消") { _, _ -> binding.rpgView.cancelChest() }
                .setOnCancelListener { binding.rpgView.cancelChest() }
                .show()
        }
    }

    /** 1石 2剪 3布；1=胜 0=平 -1=负 */
    private fun rpsBeats(a: Int, b: Int): Int {
        if (a == b) return 0
        if ((a == 1 && b == 2) || (a == 2 && b == 3) || (a == 3 && b == 1)) return 1
        return -1
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
