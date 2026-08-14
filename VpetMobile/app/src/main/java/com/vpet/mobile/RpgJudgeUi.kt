package com.vpet.mobile

import android.app.Activity
import android.os.Handler
import android.os.Looper
import android.util.TypedValue
import android.view.Gravity
import android.widget.Button
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import kotlin.random.Random

/** RPG 宝箱：掷骰 / 猜拳带动画画面（对照桌面 dice_spin / rps_spin）。 */
object RpgJudgeUi {
    private val RPS_NAMES = arrayOf("", "石头", "剪刀", "布")
    private const val NEED = 4

    fun showDice(
        activity: Activity,
        onResult: (won: Boolean, detail: String) -> Unit,
        onCancel: () -> Unit,
    ) {
        val dens = activity.resources.displayMetrics.density
        val pad = (14 * dens).toInt()
        val diePx = TypedValue.applyDimension(
            TypedValue.COMPLEX_UNIT_DIP,
            72f,
            activity.resources.displayMetrics,
        ).toInt()
        val root = LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(pad, pad, pad, pad)
            gravity = Gravity.CENTER_HORIZONTAL
        }
        val title = TextView(activity).apply {
            text = "宝箱判定 · 掷骰子"
            textSize = 17f
            setTextColor(0xFFFFCC66.toInt())
            gravity = Gravity.CENTER
        }
        val hint = TextView(activity).apply {
            text = "需 ≥$NEED 点才能打开\n点「掷骰」试试手气"
            textSize = 14f
            setTextColor(0xFFCCCCCC.toInt())
            gravity = Gravity.CENTER
            setPadding(0, pad / 2, 0, pad)
        }
        val dieView = ImageView(activity).apply {
            setImageBitmap(PixelFightArt.dieBitmap(diePx, 1))
            layoutParams = LinearLayout.LayoutParams(diePx, diePx)
        }
        val status = TextView(activity).apply {
            text = ""
            textSize = 14f
            setTextColor(0xFFAAAAAA.toInt())
            gravity = Gravity.CENTER
            setPadding(0, pad / 2, 0, pad / 2)
        }
        val btnRoll = Button(activity).apply { text = "掷骰" }
        val btnCancel = Button(activity).apply { text = "取消" }
        root.addView(title)
        root.addView(hint)
        root.addView(dieView)
        root.addView(status)
        root.addView(btnRoll)
        root.addView(btnCancel)

        val handler = Handler(Looper.getMainLooper())
        var finished = false
        val dialog = AlertDialog.Builder(activity)
            .setView(root)
            .setCancelable(true)
            .setOnCancelListener {
                if (!finished) onCancel()
            }
            .create()

        btnCancel.setOnClickListener {
            if (finished) return@setOnClickListener
            finished = true
            dialog.dismiss()
            onCancel()
        }
        btnRoll.setOnClickListener {
            if (finished) return@setOnClickListener
            btnRoll.isEnabled = false
            btnCancel.isEnabled = false
            dialog.setCancelable(false)
            val final = Random.nextInt(1, 7)
            var i = 0
            status.text = "骰子转动中…"
            val tick = object : Runnable {
                override fun run() {
                    if (!dialog.isShowing) return
                    i++
                    if (i < 12) {
                        dieView.setImageBitmap(PixelFightArt.dieBitmap(diePx, Random.nextInt(1, 7)))
                        handler.postDelayed(this, 70)
                        return
                    }
                    dieView.setImageBitmap(PixelFightArt.dieBitmap(diePx, final))
                    val won = final >= NEED
                    val detail = "你掷出 $final 点（需≥$NEED）— ${if (won) "成功！" else "失败…"}"
                    status.setTextColor(if (won) 0xFF88DD88.toInt() else 0xFFFF6688.toInt())
                    status.text = detail
                    finished = true
                    handler.postDelayed({
                        if (dialog.isShowing) dialog.dismiss()
                        onResult(won, detail)
                    }, 700)
                }
            }
            handler.post(tick)
        }
        dialog.show()
    }

    fun showRps(
        activity: Activity,
        onResult: (won: Boolean, detail: String) -> Unit,
        onCancel: () -> Unit,
        onTieRetry: () -> Unit,
    ) {
        val dens = activity.resources.displayMetrics.density
        val pad = (14 * dens).toInt()
        val iconPx = TypedValue.applyDimension(
            TypedValue.COMPLEX_UNIT_DIP,
            64f,
            activity.resources.displayMetrics,
        ).toInt()
        val root = LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(pad, pad, pad, pad)
            gravity = Gravity.CENTER_HORIZONTAL
        }
        val title = TextView(activity).apply {
            text = "宝箱判定 · 石头剪刀布"
            textSize = 17f
            setTextColor(0xFFFFCC66.toInt())
            gravity = Gravity.CENTER
        }
        val hint = TextView(activity).apply {
            text = "点选你的出拳（对手随机）"
            textSize = 14f
            setTextColor(0xFFCCCCCC.toInt())
            gravity = Gravity.CENTER
            setPadding(0, pad / 2, 0, pad)
        }
        val arena = LinearLayout(activity).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER
        }
        val youLabel = TextView(activity).apply {
            text = "你"
            textSize = 12f
            setTextColor(0xFF88CCFF.toInt())
            gravity = Gravity.CENTER
        }
        val youIcon = ImageView(activity).apply {
            setImageBitmap(PixelFightArt.rpsBitmap(iconPx, 1))
            layoutParams = LinearLayout.LayoutParams(iconPx, iconPx).also {
                it.marginEnd = (8 * dens).toInt()
            }
        }
        val vs = TextView(activity).apply {
            text = "VS"
            textSize = 16f
            setTextColor(0xFFFFCC44.toInt())
            setPadding((8 * dens).toInt(), 0, (8 * dens).toInt(), 0)
        }
        val foeIcon = ImageView(activity).apply {
            setImageBitmap(PixelFightArt.rpsBitmap(iconPx, 1))
            layoutParams = LinearLayout.LayoutParams(iconPx, iconPx).also {
                it.marginStart = (8 * dens).toInt()
            }
        }
        val foeLabel = TextView(activity).apply {
            text = "对手"
            textSize = 12f
            setTextColor(0xFFFF8844.toInt())
            gravity = Gravity.CENTER
        }
        val colYou = LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            addView(youLabel)
            addView(youIcon)
        }
        val colFoe = LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            addView(foeLabel)
            addView(foeIcon)
        }
        arena.addView(colYou)
        arena.addView(vs)
        arena.addView(colFoe)

        val status = TextView(activity).apply {
            text = ""
            textSize = 14f
            setTextColor(0xFFAAAAAA.toInt())
            gravity = Gravity.CENTER
            setPadding(0, pad, 0, pad / 2)
        }
        val pickRow = LinearLayout(activity).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER
        }
        val btnCancel = Button(activity).apply { text = "取消" }

        root.addView(title)
        root.addView(hint)
        root.addView(arena)
        root.addView(status)
        root.addView(pickRow)
        root.addView(btnCancel)

        val handler = Handler(Looper.getMainLooper())
        var finished = false
        val dialog = AlertDialog.Builder(activity)
            .setView(root)
            .setCancelable(true)
            .setOnCancelListener {
                if (!finished) onCancel()
            }
            .create()

        fun disablePicks() {
            for (i in 0 until pickRow.childCount) {
                pickRow.getChildAt(i).isEnabled = false
            }
            btnCancel.isEnabled = false
            dialog.setCancelable(false)
        }

        fun addPick(kind: Int) {
            val iv = ImageView(activity).apply {
                setImageBitmap(PixelFightArt.rpsBitmap(iconPx, kind))
                layoutParams = LinearLayout.LayoutParams(iconPx, iconPx).also {
                    it.marginEnd = (6 * dens).toInt()
                }
                setOnClickListener {
                    if (finished) return@setOnClickListener
                    disablePicks()
                    val er = Random.nextInt(1, 4)
                    youIcon.setImageBitmap(PixelFightArt.rpsBitmap(iconPx, kind, selected = true))
                    status.text = "你出了${RPS_NAMES[kind]}！对手正在出拳…"
                    var i = 0
                    val tick = object : Runnable {
                        override fun run() {
                            if (!dialog.isShowing) return
                            i++
                            if (i < 10) {
                                foeIcon.setImageBitmap(PixelFightArt.rpsBitmap(iconPx, Random.nextInt(1, 4)))
                                handler.postDelayed(this, 80)
                                return
                            }
                            foeIcon.setImageBitmap(PixelFightArt.rpsBitmap(iconPx, er, selected = true))
                            val res = rpsBeats(kind, er)
                            when {
                                res == 0 -> {
                                    status.setTextColor(0xFFFFCC66.toInt())
                                    status.text = "平局（双方${RPS_NAMES[kind]}）！再出一次"
                                    finished = true
                                    handler.postDelayed({
                                        if (dialog.isShowing) dialog.dismiss()
                                        onTieRetry()
                                    }, 650)
                                }
                                res > 0 -> {
                                    val detail = "你出${RPS_NAMES[kind]}，对手${RPS_NAMES[er]} — 你赢了！"
                                    status.setTextColor(0xFF88DD88.toInt())
                                    status.text = detail
                                    finished = true
                                    handler.postDelayed({
                                        if (dialog.isShowing) dialog.dismiss()
                                        onResult(true, detail)
                                    }, 700)
                                }
                                else -> {
                                    val detail = "你出${RPS_NAMES[kind]}，对手${RPS_NAMES[er]} — 输了…"
                                    status.setTextColor(0xFFFF6688.toInt())
                                    status.text = detail
                                    finished = true
                                    handler.postDelayed({
                                        if (dialog.isShowing) dialog.dismiss()
                                        onResult(false, detail)
                                    }, 700)
                                }
                            }
                        }
                    }
                    handler.post(tick)
                }
            }
            pickRow.addView(iv)
        }
        addPick(1)
        addPick(2)
        addPick(3)

        btnCancel.setOnClickListener {
            if (finished) return@setOnClickListener
            finished = true
            dialog.dismiss()
            onCancel()
        }
        dialog.show()
    }

    private fun rpsBeats(a: Int, b: Int): Int {
        if (a == b) return 0
        if ((a == 1 && b == 2) || (a == 2 && b == 3) || (a == 3 && b == 1)) return 1
        return -1
    }
}
