package com.vpet.mobile

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import androidx.appcompat.app.AppCompatActivity
import com.vpet.mobile.databinding.ActivityRhymeBinding
import kotlin.random.Random

/** 莱姆本地练习对战：胜 game_clear；败保留约 1.6s（G07/G08）。 */
class RhymeActivity : AppCompatActivity() {
    companion object {
        const val LOSE_HOLD_MS = 1600L
    }

    private lateinit var binding: ActivityRhymeBinding
    private val handler = Handler(Looper.getMainLooper())
    private var hp = 100
    private var enemy = 100
    private var ended = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityRhymeBinding.inflate(layoutInflater)
        setContentView(binding.root)
        refresh("对战开始！")
        binding.btnAttack.setOnClickListener {
            if (ended) return@setOnClickListener
            val dmg = Random.nextInt(8, 18)
            enemy = (enemy - dmg).coerceAtLeast(0)
            val back = Random.nextInt(5, 14)
            hp = (hp - back).coerceAtLeast(0)
            refresh("你造成 $dmg 伤害，对方反击 $back")
            checkEnd()
        }
        binding.btnHeal.setOnClickListener {
            if (ended) return@setOnClickListener
            val heal = Random.nextInt(10, 20)
            hp = (hp + heal).coerceAtMost(100)
            val back = Random.nextInt(4, 12)
            hp = (hp - back).coerceAtLeast(0)
            refresh("回复 $heal，仍被打了 $back")
            checkEnd()
        }
        binding.btnRhymeExit.setOnClickListener { finish() }
    }

    override fun onDestroy() {
        handler.removeCallbacksAndMessages(null)
        super.onDestroy()
    }

    private fun refresh(msg: String) {
        binding.rhymeLog.text = "$msg\n\n你 HP $hp\n对手 HP $enemy"
    }

    private fun checkEnd() {
        if (ended) return
        when {
            enemy <= 0 -> {
                ended = true
                binding.btnAttack.isEnabled = false
                binding.btnHeal.isEnabled = false
                AppDataStore.addStaminaMood(this, -5, 10)
                GameClearUi.show(
                    this,
                    title = "对战胜利！",
                    subtitle = "莱姆练习 · 心情 +10 · 体力 -5",
                    accentHex = "#88DD88",
                    onDismiss = { finish() },
                )
            }
            hp <= 0 -> {
                ended = true
                binding.btnAttack.isEnabled = false
                binding.btnHeal.isEnabled = false
                AppDataStore.addStaminaMood(this, -10, -8)
                binding.rhymeLog.text = "战败…\n\n你 HP 0\n对手 HP $enemy\n（稍候关闭）"
                binding.rhymeLog.setTextColor(0xFFFF6688.toInt())
                GameFailVoice.playHurt(this)
                // G08：败局面保留约 1.6s，不用 game_clear
                handler.postDelayed({ finish() }, LOSE_HOLD_MS)
            }
        }
    }
}
