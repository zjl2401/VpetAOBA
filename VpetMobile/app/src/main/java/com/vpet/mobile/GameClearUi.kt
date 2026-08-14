package com.vpet.mobile

import android.app.Dialog
import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.drawable.GradientDrawable
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.View
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import kotlin.random.Random

/**
 * 结算浮层：对照桌面 `_show_game_clear` + `_spawn_game_clear_particles`。
 */
object GameClearUi {
    const val GAME_CLEAR_HOLD_MS = 2000L

    fun show(
        context: Context,
        title: String,
        subtitle: String,
        heroGrade: String? = null,
        accentHex: String = "#FFCC44",
        holdMs: Long = GAME_CLEAR_HOLD_MS,
        onDismiss: (() -> Unit)? = null,
    ) {
        val dialog = Dialog(context)
        dialog.setCancelable(false)
        val accent = Color.parseColor(accentHex)
        val root = FrameLayout(context)
        val content = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(36, 28, 36, 28)
            background = GradientDrawable().apply {
                setColor(Color.parseColor("#F0120818"))
                setStroke(3, accent)
                cornerRadius = 8f
            }
            minimumWidth = (280 * context.resources.displayMetrics.density).toInt()
        }
        if (!heroGrade.isNullOrBlank()) {
            content.addView(
                TextView(context).apply {
                    text = heroGrade
                    textSize = 42f
                    setTextColor(accent)
                    gravity = Gravity.CENTER
                    setPadding(0, 0, 0, 8)
                },
            )
        }
        content.addView(
            TextView(context).apply {
                text = title
                textSize = 18f
                setTextColor(Color.WHITE)
                gravity = Gravity.CENTER
            },
        )
        content.addView(
            TextView(context).apply {
                text = subtitle
                textSize = 13f
                setTextColor(Color.parseColor("#CCDDEE"))
                gravity = Gravity.CENTER
                setPadding(0, 12, 0, 0)
            },
        )
        val particleView = ParticleView(context, accentHex)
        root.addView(
            particleView,
            FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT,
            ),
        )
        root.addView(
            content,
            FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,
                FrameLayout.LayoutParams.WRAP_CONTENT,
                Gravity.CENTER,
            ),
        )
        dialog.setContentView(root)
        dialog.window?.let { w ->
            if (context !is android.app.Activity) {
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                    w.setType(android.view.WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY)
                } else {
                    @Suppress("DEPRECATION")
                    w.setType(android.view.WindowManager.LayoutParams.TYPE_PHONE)
                }
            }
            w.setLayout(
                (320 * context.resources.displayMetrics.density).toInt(),
                (280 * context.resources.displayMetrics.density).toInt(),
            )
        }
        dialog.show()
        particleView.start()
        Handler(Looper.getMainLooper()).postDelayed({
            particleView.stop()
            try {
                dialog.dismiss()
            } catch (_: Exception) {
            }
            onDismiss?.invoke()
        }, holdMs)
    }

    private class ParticleView(context: Context, accentHex: String) : View(context) {
        private data class P(
            var x: Float, var y: Float, var vx: Float, var vy: Float,
            var life: Int, val size: Float, val color: Int,
        )

        private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
        private val parts = mutableListOf<P>()
        private val handler = Handler(Looper.getMainLooper())
        private var running = false
        private val accent = Color.parseColor(accentHex)
        private val tick = object : Runnable {
            override fun run() {
                if (!running) return
                for (p in parts) {
                    p.x += p.vx
                    p.y += p.vy
                    p.life--
                }
                parts.removeAll { it.life <= 0 }
                if (parts.size < 12) spawn(8)
                invalidate()
                handler.postDelayed(this, 33L)
            }
        }

        fun start() {
            running = true
            spawn(28)
            handler.post(tick)
        }

        fun stop() {
            running = false
            handler.removeCallbacks(tick)
        }

        private fun spawn(n: Int) {
            val w = width.coerceAtLeast(280).toFloat()
            val h = height.coerceAtLeast(200).toFloat()
            val rng = Random(accent.hashCode() xor parts.size)
            repeat(n) {
                parts += P(
                    x = rng.nextFloat() * (w - 24f) + 12f,
                    y = rng.nextFloat() * (h - 36f) + 18f,
                    vx = rng.nextFloat() * 3.2f - 1.6f,
                    vy = -(rng.nextFloat() * 1.8f + 0.4f),
                    life = rng.nextInt(8, 27),
                    size = listOf(2f, 3f, 4f).random(rng) * resources.displayMetrics.density,
                    color = when {
                        rng.nextFloat() < 0.55f -> accent
                        rng.nextFloat() < 0.5f -> Color.parseColor("#FF4DB8")
                        else -> Color.parseColor("#66F0FF")
                    },
                )
            }
        }

        override fun onDraw(canvas: Canvas) {
            for (p in parts) {
                paint.color = p.color
                canvas.drawRect(p.x, p.y, p.x + p.size, p.y + p.size, paint)
            }
        }
    }
}
