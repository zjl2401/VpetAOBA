package com.vpet.mobile

import android.graphics.Color
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.view.Gravity
import android.widget.FrameLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.vpet.mobile.databinding.ActivityCollectBinding
import kotlin.random.Random

/** 采集：限时点下落物；入库 + 金币；game_clear 结算。 */
class CollectActivity : AppCompatActivity() {
    private lateinit var binding: ActivityCollectBinding
    private val handler = Handler(Looper.getMainLooper())
    private var score = 0
    private var catches = 0
    private var misses = 0
    private var endsAt = 0L
    private var spawnJob: Runnable? = null
    private var tickJob: Runnable? = null
    private lateinit var params: DifficultyParams.Params
    private var finished = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityCollectBinding.inflate(layoutInflater)
        setContentView(binding.root)
        params = DifficultyParams.of(this)
        FoodInventoryStore.ensureSeeded(this)
        endsAt = SystemClock.elapsedRealtime() + 30_000L
        binding.collectHud.text = "采集 · 难度 ${AppDataStore.difficulty(this)}"
        scheduleSpawn()
        scheduleTick()
    }

    override fun onDestroy() {
        spawnJob?.let { handler.removeCallbacks(it) }
        tickJob?.let { handler.removeCallbacks(it) }
        super.onDestroy()
    }

    private fun scheduleTick() {
        tickJob = Runnable {
            val left = ((endsAt - SystemClock.elapsedRealtime()) / 1000L).coerceAtLeast(0)
            binding.collectHud.text =
                "采集 $score · 接住 $catches · 错过 $misses · ${left}s · ${AppDataStore.difficulty(this)}"
            if (left <= 0) {
                finishRound()
            } else {
                handler.postDelayed(tickJob!!, 200L)
            }
        }
        handler.post(tickJob!!)
    }

    private fun scheduleSpawn() {
        spawnJob = Runnable {
            if (SystemClock.elapsedRealtime() >= endsAt || finished) return@Runnable
            spawnOne()
            val jitter = Random.nextLong(0, 200)
            handler.postDelayed(spawnJob!!, params.gameSpawnMs + jitter)
        }
        handler.postDelayed(spawnJob!!, params.gameSpawnMs)
    }

    private fun spawnOne() {
        val food = FoodCatalog.ALL.random()
        val tv = TextView(this).apply {
            text = food.emoji
            textSize = 28f
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
            tag = food.id
        }
        val size = (56 * resources.displayMetrics.density).toInt()
        val w = binding.collectRoot.width.takeIf { it > 0 } ?: resources.displayMetrics.widthPixels
        val lp = FrameLayout.LayoutParams(size, size).apply {
            leftMargin = Random.nextInt(20, (w - size - 20).coerceAtLeast(40))
            topMargin = 80
        }
        binding.collectRoot.addView(tv, lp)
        tv.setOnClickListener {
            val id = tv.tag as? String ?: return@setOnClickListener
            score += 10
            catches += 1
            FoodInventoryStore.add(this, id, 1)
            AppDataStore.addStaminaMood(this, 1, 1)
            binding.collectRoot.removeView(tv)
        }
        val step = (params.gameSpeed * resources.displayMetrics.density).toInt().coerceAtLeast(4)
        val fall = object : Runnable {
            var y = 80
            override fun run() {
                if (tv.parent == null || finished) return
                y += step
                val p = tv.layoutParams as FrameLayout.LayoutParams
                p.topMargin = y
                tv.layoutParams = p
                if (y > binding.collectRoot.height - size) {
                    misses += 1
                    binding.collectRoot.removeView(tv)
                } else {
                    handler.postDelayed(this, 50L)
                }
            }
        }
        handler.post(fall)
    }

    private fun finishRound() {
        if (finished) return
        finished = true
        spawnJob?.let { handler.removeCallbacks(it) }
        tickJob?.let { handler.removeCallbacks(it) }
        val coinGain = minOf(15, maxOf(0, score / 25 + catches / 3))
        if (coinGain > 0) WalletStore.grantCoins(this, coinGain)
        AppDataStore.unlock(this, "collect_play")
        val bal = WalletStore.coins(this)
        // V-HURT：差劲（错过≥接住 或 0 接）附加 hurt，不挡结算
        if (misses >= catches || catches == 0) {
            GameFailVoice.playHurt(this)
        }
        GameClearUi.show(
            this,
            title = "采集完成！",
            subtitle = "接住 $catches · 得分 $score · 错过 $misses\n金币 +$coinGain · 钱包 $bal\n食物已进背包",
            accentHex = "#44FF88",
            onDismiss = { finish() },
        )
    }
}
