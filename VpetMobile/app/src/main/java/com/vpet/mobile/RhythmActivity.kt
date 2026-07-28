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
import com.vpet.mobile.databinding.ActivityRhythmBinding
import kotlin.math.abs
import kotlin.random.Random

/** 音游：四轨下落；P/G/Good/Miss → 准确率 → D~S + 金币。 */
class RhythmActivity : AppCompatActivity() {
    private lateinit var binding: ActivityRhythmBinding
    private val handler = Handler(Looper.getMainLooper())
    private var score = 0
    private var perfect = 0
    private var great = 0
    private var good = 0
    private var miss = 0
    private var endsAt = 0L
    private var finished = false
    private val lanes = Array(4) { mutableListOf<TextView>() }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityRhythmBinding.inflate(layoutInflater)
        setContentView(binding.root)
        endsAt = SystemClock.elapsedRealtime() + 40_000L
        binding.btnD.setOnClickListener { hit(0) }
        binding.btnF.setOnClickListener { hit(1) }
        binding.btnJ.setOnClickListener { hit(2) }
        binding.btnK.setOnClickListener { hit(3) }
        spawnLoop()
        tick()
    }

    override fun onDestroy() {
        handler.removeCallbacksAndMessages(null)
        super.onDestroy()
    }

    private fun tick() {
        handler.postDelayed({
            if (finished) return@postDelayed
            val left = ((endsAt - SystemClock.elapsedRealtime()) / 1000).coerceAtLeast(0)
            binding.rhythmHud.text =
                "音游 · $score · P$perfect G$great g$good M$miss · ${left}s"
            if (left <= 0) {
                finishRound()
            } else {
                tick()
            }
        }, 250L)
    }

    private fun spawnLoop() {
        handler.postDelayed({
            if (finished || SystemClock.elapsedRealtime() >= endsAt) return@postDelayed
            spawnNote(Random.nextInt(4))
            spawnLoop()
        }, Random.nextLong(450, 800))
    }

    private fun spawnNote(lane: Int) {
        val field = binding.rhythmField
        val w = field.width.coerceAtLeast(1)
        val laneW = w / 4
        val note = TextView(this).apply {
            text = "●"
            textSize = 22f
            setTextColor(Color.parseColor("#88FFCC"))
            gravity = Gravity.CENTER
            tag = lane
        }
        val size = (40 * resources.displayMetrics.density).toInt()
        val lp = FrameLayout.LayoutParams(size, size).apply {
            leftMargin = lane * laneW + (laneW - size) / 2
            topMargin = 0
        }
        field.addView(note, lp)
        lanes[lane].add(note)
        val dens = resources.displayMetrics.density
        val fall = object : Runnable {
            var y = 0
            override fun run() {
                if (finished || note.parent == null) return
                y += (12 * dens).toInt()
                val p = note.layoutParams as FrameLayout.LayoutParams
                p.topMargin = y
                note.layoutParams = p
                if (y > field.height) {
                    lanes[lane].remove(note)
                    field.removeView(note)
                    miss += 1
                } else {
                    handler.postDelayed(this, 40L)
                }
            }
        }
        handler.post(fall)
    }

    private fun hit(lane: Int) {
        if (finished) return
        val field = binding.rhythmField
        val dens = resources.displayMetrics.density
        val hitLine = field.height - (80 * dens).toInt()
        val list = lanes[lane]
        val note = list.firstOrNull() ?: return
        val y = (note.layoutParams as FrameLayout.LayoutParams).topMargin
        val dist = abs(y - hitLine) / dens
        when {
            dist <= RhythmGrades.HIT_PERFECT_PX -> {
                perfect += 1
                score += RhythmGrades.SCORE_PERFECT
            }
            dist <= RhythmGrades.HIT_GREAT_PX -> {
                great += 1
                score += RhythmGrades.SCORE_GREAT
            }
            dist <= RhythmGrades.HIT_GOOD_PX -> {
                good += 1
                score += RhythmGrades.SCORE_GOOD
            }
            else -> return
        }
        list.remove(note)
        field.removeView(note)
    }

    private fun finishRound() {
        if (finished) return
        finished = true
        handler.removeCallbacksAndMessages(null)
        val acc = RhythmGrades.accuracy(perfect, great, good, miss)
        val r = RhythmGrades.gradeOf(acc)
        if (r.coinGain > 0) WalletStore.grantCoins(this, r.coinGain)
        val bal = WalletStore.coins(this)
        // V-HURT：D/C 评级附加 hurt
        if (r.grade == "D" || r.grade == "C") {
            GameFailVoice.playHurt(this)
        }
        GameClearUi.show(
            this,
            title = "音游结束！",
            subtitle = "评级 ${r.grade}（${r.label}）· 准确率 ${r.accuracy}%\n" +
                "P$perfect G$great g$good M$miss · 分数 $score\n金币 +${r.coinGain} · 钱包 $bal",
            heroGrade = r.grade,
            accentHex = r.colorHex,
            onDismiss = { finish() },
        )
    }
}
