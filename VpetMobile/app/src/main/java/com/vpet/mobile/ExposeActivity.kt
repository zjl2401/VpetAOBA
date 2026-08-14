package com.vpet.mobile

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.View
import android.widget.FrameLayout
import androidx.appcompat.app.AppCompatActivity
import com.vpet.mobile.databinding.ActivityExposeBinding

/**
 * 暴露 QTE：难度影响扇区/指针；连中 N 次通关。
 * 首败整局结束 + 故障层 EXPOSE_FAIL_HOLD_MS（不用 game_clear）。
 */
class ExposeActivity : AppCompatActivity() {
    companion object {
        const val EXPOSE_FAIL_HOLD_MS = 900L
    }

    private lateinit var binding: ActivityExposeBinding
    private val handler = Handler(Looper.getMainLooper())
    private var x = 0f
    private var dir = 1
    private var hits = 0
    private lateinit var params: DifficultyParams.Params
    private var zoneW = 0
    private var ended = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityExposeBinding.inflate(layoutInflater)
        setContentView(binding.root)
        OverlayGate.pause(this)
        FirstPlayGuides.maybeShow(this, "expose")
        params = DifficultyParams.of(this)
        binding.exposeHud.text = "连击 0/${params.exposeHitsNeed} · 难度 ${AppDataStore.difficulty(this)}"
        binding.btnJudge.setOnClickListener { judge() }
        binding.btnExposeExit.setOnClickListener { finish() }
        binding.exposeZone.post {
            val parent = binding.exposeCursor.parent as FrameLayout
            zoneW = (parent.width * params.exposeZoneWidthFrac).toInt().coerceIn(48, parent.width / 2)
            val lp = binding.exposeZone.layoutParams as FrameLayout.LayoutParams
            lp.width = zoneW
            binding.exposeZone.layoutParams = lp
            move()
        }
    }

    override fun onDestroy() {
        handler.removeCallbacksAndMessages(null)
        OverlayGate.resume(this)
        super.onDestroy()
    }

    private fun move() {
        if (ended) return
        handler.postDelayed({
            if (ended) return@postDelayed
            val parent = binding.exposeCursor.parent as FrameLayout
            val max = (parent.width - binding.exposeCursor.width).coerceAtLeast(1)
            val step = params.exposePointerSpeedDp * resources.displayMetrics.density *
                (1f + hits * 0.42f)
            x += dir * step
            if (x < 0) {
                x = 0f; dir = 1
            } else if (x > max) {
                x = max.toFloat(); dir = -1
            }
            val lp = binding.exposeCursor.layoutParams as FrameLayout.LayoutParams
            lp.leftMargin = x.toInt()
            lp.gravity = android.view.Gravity.START
            binding.exposeCursor.layoutParams = lp
            move()
        }, 16L)
    }

    private fun judge() {
        if (ended) return
        val parent = binding.exposeCursor.parent as FrameLayout
        val zone = binding.exposeZone
        val cursorCenter = x + binding.exposeCursor.width / 2f
        val zoneLeft = (parent.width - zone.width) / 2f
        val zoneRight = zoneLeft + zone.width
        if (cursorCenter in zoneLeft..zoneRight) {
            hits += 1
            binding.exposeHud.text = "连击 $hits/${params.exposeHitsNeed}"
            if (hits >= params.exposeHitsNeed) {
                ended = true
                handler.removeCallbacksAndMessages(null)
                AppDataStore.addStaminaMood(this, 0, params.exposeClearMood)
                GameClearUi.show(
                    this,
                    title = "暴露通关！",
                    subtitle = "连中 ${params.exposeHitsNeed} 次 · 心情 +${params.exposeClearMood}",
                    accentHex = "#44FF88",
                    onDismiss = { finish() },
                )
            }
        } else {
            failSession()
        }
    }

    private fun failSession() {
        if (ended) return
        ended = true
        handler.removeCallbacksAndMessages(null)
        val s = AppDataStore.stamina(this)
        val m = AppDataStore.mood(this)
        val ds = (-(s * params.exposeFailStaminaPct).toInt()).coerceAtMost(-1)
        val dm = (-(m * params.exposeFailMoodPct).toInt()).coerceAtMost(-1)
        AppDataStore.addStaminaMood(this, ds, dm)
        binding.exposeFailLayer.visibility = View.VISIBLE
        binding.exposeFailText.text = "暴露失败…\n体$ds 心$dm"
        // H-EXPOSE-NOSUB：hurt 无字幕（故障层已有文案）
        GameFailVoice.playHurt(this)
        handler.postDelayed({ finish() }, EXPOSE_FAIL_HOLD_MS)
    }
}
