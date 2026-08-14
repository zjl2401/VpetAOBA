package com.vpet.mobile

import android.graphics.Color
import android.media.AudioAttributes
import android.media.MediaPlayer
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.view.MotionEvent
import android.widget.Button
import androidx.appcompat.app.AppCompatActivity
import com.vpet.mobile.databinding.ActivityRhythmBinding
import kotlin.math.abs
import kotlin.math.max

/**
 * 音游：四轨 BPM 谱 + 判定线 + 毫秒窗判定；尽量跟音乐同步。
 * 对照桌面 rhythm（D/F/J/K、Perfect/Great/Good/Miss、长按）。
 */
class RhythmActivity : AppCompatActivity() {
    private lateinit var binding: ActivityRhythmBinding
    private val handler = Handler(Looper.getMainLooper())
    private var player: MediaPlayer? = null
    private var notes: MutableList<RhythmChart.Note> = mutableListOf()
    private var songStartElapsed = 0L
    private var usePlayerClock = false
    private var durationMs = RhythmChart.SHORT_CAP_MS
    private var finished = false
    private var scanI = 0
    private var score = 0
    private var perfect = 0
    private var great = 0
    private var good = 0
    private var miss = 0
    private var combo = 0
    private val keysDown = mutableSetOf<Int>()
    private val laneFlashUntil = LongArray(RhythmChart.LANES)
    private var trackLabel = "节拍谱"

    private val tick = object : Runnable {
        override fun run() {
            if (finished) return
            val now = nowMs()
            missExpired(now)
            binding.playView.nowMs = now
            binding.playView.keysDown = keysDown.toSet()
            binding.playView.laneFlashUntil = laneFlashUntil
            binding.playView.combo = combo
            binding.playView.invalidate()
            updateHud(now)
            if (now >= durationMs) {
                finishRound()
            } else {
                handler.postDelayed(this, 16L)
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityRhythmBinding.inflate(layoutInflater)
        setContentView(binding.root)
        OverlayGate.pause(this)
        FirstPlayGuides.maybeShow(this, "rhythm_game")
        val diff = AppDataStore.difficulty(this)
        prepareAudio()
        notes = RhythmChart.buildRandom(durationMs, difficulty = diff).toMutableList()
        binding.playView.notes = notes
        binding.playView.travelMs = RhythmChart.TRAVEL_MS

        bindLane(binding.btnD, 0)
        bindLane(binding.btnF, 1)
        bindLane(binding.btnJ, 2)
        bindLane(binding.btnK, 3)

        songStartElapsed = SystemClock.elapsedRealtime()
        try {
            player?.start()
            usePlayerClock = player != null
        } catch (_: Exception) {
            usePlayerClock = false
        }
        // 给首批音符下落预热：谱从 2.2s 起，开局即可看见下落
        handler.post(tick)
    }

    override fun onDestroy() {
        finished = true
        handler.removeCallbacksAndMessages(null)
        releasePlayer()
        OverlayGate.resume(this)
        super.onDestroy()
    }

    private fun prepareAudio() {
        val uriStr = PetProfileStore.musicUri(this)
        if (!uriStr.isNullOrBlank()) {
            try {
                val mp = MediaPlayer().apply {
                    setAudioAttributes(
                        AudioAttributes.Builder()
                            .setUsage(AudioAttributes.USAGE_GAME)
                            .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                            .build(),
                    )
                    setDataSource(this@RhythmActivity, Uri.parse(uriStr))
                    prepare()
                }
                player = mp
                durationMs = minOf(mp.duration.coerceAtLeast(15_000), RhythmChart.SHORT_CAP_MS)
                trackLabel = PetProfileStore.musicTitle(this).ifBlank { "本地曲" }
                mp.setOnCompletionListener { if (!finished) finishRound() }
                return
            } catch (_: Exception) {
                releasePlayer()
            }
        }
        val track = BundledMusic.tracks(this).randomOrNull()
        if (track != null) {
            try {
                val afd = assets.openFd(track.assetPath)
                val mp = MediaPlayer().apply {
                    setAudioAttributes(
                        AudioAttributes.Builder()
                            .setUsage(AudioAttributes.USAGE_GAME)
                            .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                            .build(),
                    )
                    setDataSource(afd.fileDescriptor, afd.startOffset, afd.length)
                    prepare()
                }
                afd.close()
                player = mp
                durationMs = minOf(mp.duration.coerceAtLeast(15_000), RhythmChart.SHORT_CAP_MS)
                trackLabel = track.label
                mp.setOnCompletionListener { if (!finished) finishRound() }
                return
            } catch (_: Exception) {
                releasePlayer()
            }
        }
        durationMs = 60_000
        trackLabel = "无曲 · BPM ${RhythmChart.BPM}"
    }

    private fun releasePlayer() {
        try {
            player?.stop()
        } catch (_: Exception) {
        }
        try {
            player?.release()
        } catch (_: Exception) {
        }
        player = null
    }

    private fun nowMs(): Int {
        if (usePlayerClock) {
            val p = player
            if (p != null) {
                try {
                    return p.currentPosition.coerceAtLeast(0)
                } catch (_: Exception) {
                }
            }
        }
        return (SystemClock.elapsedRealtime() - songStartElapsed).toInt()
    }

    private fun bindLane(btn: Button, lane: Int) {
        val colors = intArrayOf(0xFF66CCFF.toInt(), 0xFF88FFAA.toInt(), 0xFFFFCC66.toInt(), 0xFFFF88CC.toInt())
        btn.setBackgroundColor(colors[lane] and 0x00FFFFFF or 0x55000000)
        btn.setTextColor(Color.WHITE)
        btn.setOnTouchListener { v, e ->
            when (e.actionMasked) {
                MotionEvent.ACTION_DOWN, MotionEvent.ACTION_POINTER_DOWN -> {
                    v.isPressed = true
                    pressLane(lane)
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_POINTER_UP, MotionEvent.ACTION_CANCEL -> {
                    v.isPressed = false
                    releaseLane(lane)
                    true
                }
                else -> false
            }
        }
    }

    private fun pressLane(lane: Int) {
        if (finished || lane in keysDown) return
        keysDown += lane
        val now = nowMs()
        laneFlashUntil[lane] = System.currentTimeMillis() + 100L
        var best: RhythmChart.Note? = null
        var bestAbs = RhythmChart.HIT_GOOD_MS + 1
        val start = max(0, scanI - 8)
        for (i in start until notes.size) {
            val note = notes[i]
            if (note.lane != lane || note.hit || note.missed) continue
            if (note.headHit || note.holding) continue
            val t = note.t
            if (t > now + RhythmChart.HIT_GOOD_MS + 80) break
            if (t < now - RhythmChart.HIT_GOOD_MS - 80) continue
            val ad = abs(now - t)
            if (ad < bestAbs) {
                bestAbs = ad
                best = note
            }
        }
        val note = best ?: return
        val (judge, pts) = RhythmChart.judgment(now - note.t)
        if (judge == "Miss") return
        laneFlashUntil[lane] = System.currentTimeMillis() + 140L
        if (note.isHold()) {
            note.headHit = true
            note.holding = true
            applyJudgment(judge, max(50, pts / 2))
        } else {
            note.hit = true
            applyJudgment(judge, pts)
        }
    }

    private fun releaseLane(lane: Int) {
        if (lane !in keysDown) return
        keysDown -= lane
        if (finished) return
        val now = nowMs()
        val start = max(0, scanI - 8)
        for (i in start until notes.size) {
            val note = notes[i]
            if (note.lane != lane) continue
            if (note.hit || note.missed) continue
            if (!(note.holding && note.headHit)) continue
            val end = note.end
            if (now < end - RhythmChart.HOLD_RELEASE_MS) {
                note.holding = false
                note.missed = true
                applyJudgment("Miss", 0)
                return
            }
            val (judge, pts) = RhythmChart.holdTailJudgment(now - end)
            if (judge == "Miss") {
                note.holding = false
                note.missed = true
                applyJudgment("Miss", 0)
            } else {
                note.holding = false
                note.hit = true
                note.tailDone = true
                applyJudgment(judge, max(50, pts / 2))
            }
            return
        }
    }

    private fun missExpired(now: Int) {
        while (scanI < notes.size && notes[scanI].t < now - RhythmChart.HIT_GOOD_MS - 120) {
            val n = notes[scanI]
            if (!n.hit && !n.missed && !n.headHit) {
                n.missed = true
                applyJudgment("Miss", 0)
            } else if (n.isHold() && n.headHit && !n.tailDone && !n.missed && now > n.end + RhythmChart.HOLD_RELEASE_MS) {
                n.holding = false
                n.missed = true
                applyJudgment("Miss", 0)
            }
            scanI++
        }
        // 长按尾超时（已扫过的）
        for (i in max(0, scanI - 24) until minOf(notes.size, scanI + 8)) {
            val n = notes[i]
            if (n.isHold() && n.headHit && n.holding && !n.tailDone && !n.missed &&
                now > n.end + RhythmChart.HOLD_RELEASE_MS
            ) {
                n.holding = false
                n.missed = true
                applyJudgment("Miss", 0)
            }
        }
    }

    private fun applyJudgment(judge: String, pts: Int) {
        when (judge) {
            "Perfect" -> {
                perfect++
                combo++
                score += pts
            }
            "Great" -> {
                great++
                combo++
                score += pts
            }
            "Good" -> {
                good++
                combo++
                score += pts
            }
            else -> {
                miss++
                combo = 0
            }
        }
        binding.playView.judgeText = judge
        binding.playView.judgeUntilMs = System.currentTimeMillis() + 420L
    }

    private fun updateHud(now: Int) {
        val left = ((durationMs - now) / 1000).coerceAtLeast(0)
        binding.rhythmHud.text =
            "$trackLabel · $score · P$perfect G$great g$good M$miss · ${combo}x · ${left}s"
    }

    private fun finishRound() {
        if (finished) return
        finished = true
        handler.removeCallbacksAndMessages(null)
        releasePlayer()
        // 未处理音符记 Miss
        for (n in notes) {
            if (!n.hit && !n.missed && !n.tailDone) {
                if (n.headHit && !n.tailDone) {
                    miss++
                } else if (!n.headHit) {
                    miss++
                }
                n.missed = true
            }
        }
        val acc = RhythmGrades.accuracy(perfect, great, good, miss)
        val r = RhythmGrades.gradeOf(acc)
        if (r.coinGain > 0) WalletStore.grantCoins(this, r.coinGain)
        val bal = WalletStore.coins(this)
        if (r.grade == "D" || r.grade == "C") {
            GameFailVoice.playHurt(this)
        }
        AppDataStore.unlock(this, "rhythm_play")
        if (r.grade == "S" || r.grade == "A") {
            AppDataStore.unlock(this, "rhythm_great")
        }
        GameClearUi.show(
            this,
            title = "音游结束！",
            subtitle = "评级 ${r.grade}（${r.label}）· 准确率 ${r.accuracy}%\n" +
                "P$perfect G$great g$good M$miss · 分数 $score · 最大连击参考见局内\n" +
                "金币 +${r.coinGain} · 钱包 $bal",
            heroGrade = r.grade,
            accentHex = r.colorHex,
            onDismiss = { finish() },
        )
    }
}
