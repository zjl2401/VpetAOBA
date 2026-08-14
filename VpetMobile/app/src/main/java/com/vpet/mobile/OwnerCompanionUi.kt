package com.vpet.mobile

import android.app.Dialog
import android.content.Context
import android.graphics.PixelFormat
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Handler
import android.os.Looper
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import android.view.animation.DecelerateInterpolator
import android.widget.Button
import android.widget.GridLayout
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.view.ContextThemeWrapper
import java.util.Calendar
import java.util.Locale

/**
 * 所属人页：按月展示认主日起已相伴的日子，可翻月；下方相伴时长与分项。
 */
object OwnerCompanionUi {
    private val handler = Handler(Looper.getMainLooper())
    private var openDialog: Dialog? = null

    fun show(context: Context) {
        val name = PetPrefs.ownerName(context)
        if (name.isEmpty()) {
            android.widget.Toast.makeText(context, "尚未认主", android.widget.Toast.LENGTH_SHORT).show()
            return
        }
        openDialog?.dismiss()
        ModeTimeStore.flush(context)

        val themed = ContextThemeWrapper(context, R.style.Theme_VpetMobile)
        val startMs = PetProfileStore.ownerSetAtMs(context).takeIf { it > 0L }
            ?: System.currentTimeMillis()
        val startCal = Calendar.getInstance().apply {
            timeInMillis = startMs
            set(Calendar.HOUR_OF_DAY, 0)
            set(Calendar.MINUTE, 0)
            set(Calendar.SECOND, 0)
            set(Calendar.MILLISECOND, 0)
        }
        val todayCal = Calendar.getInstance().apply {
            set(Calendar.HOUR_OF_DAY, 0)
            set(Calendar.MINUTE, 0)
            set(Calendar.SECOND, 0)
            set(Calendar.MILLISECOND, 0)
        }
        val days = PetPrefs.companionDays(context).coerceAtLeast(1)
        val setAtRaw = PetProfileStore.profile(context).optString("owner_set_at").ifBlank { "—" }
        val total = ModeTimeStore.formatDuration(ModeTimeStore.totalSeconds(context))

        val viewMonth = Calendar.getInstance().apply {
            timeInMillis = todayCal.timeInMillis
            set(Calendar.DAY_OF_MONTH, 1)
        }

        val pad = dp(themed, 14)
        val root = LinearLayout(themed).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(pad, pad, pad, pad)
            background = GradientDrawable().apply {
                setColor(0xE0141824.toInt())
                cornerRadius = dp(themed, 10).toFloat()
                setStroke(dp(themed, 1), 0xFF2A4060.toInt())
            }
        }

        root.addView(TextView(themed).apply {
            text = "所属人"
            setTextColor(0xFFFF88CC.toInt())
            textSize = 16f
            typeface = Typeface.MONOSPACE
            setTypeface(typeface, Typeface.BOLD)
        })
        root.addView(TextView(themed).apply {
            text = name
            setTextColor(0xFFEEF2FF.toInt())
            textSize = 18f
            typeface = Typeface.MONOSPACE
            setPadding(0, dp(themed, 4), 0, 0)
        })
        root.addView(TextView(themed).apply {
            text = "登记于 ${setAtRaw.take(19).replace('T', ' ')}"
            setTextColor(0xFF8899AA.toInt())
            textSize = 11f
            typeface = Typeface.MONOSPACE
            setPadding(0, dp(themed, 2), 0, dp(themed, 8))
        })
        root.addView(TextView(themed).apply {
            text = "相伴第 $days 天"
            setTextColor(0xFF88CCFF.toInt())
            textSize = 15f
            typeface = Typeface.MONOSPACE
            setTypeface(typeface, Typeface.BOLD)
        })
        root.addView(TextView(themed).apply {
            text = if (ModeTimeStore.totalSeconds(context) > 0) "相伴时长：$total" else "相伴时长：还在累积中…"
            setTextColor(0xFFAABBCC.toInt())
            textSize = 12f
            typeface = Typeface.MONOSPACE
            setPadding(0, dp(themed, 2), 0, dp(themed, 10))
        })

        val monthTitle = TextView(themed).apply {
            setTextColor(0xFFEEF2FF.toInt())
            textSize = 14f
            typeface = Typeface.MONOSPACE
            gravity = Gravity.CENTER
            layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
        }
        val gridHost = LinearLayout(themed).apply {
            orientation = LinearLayout.VERTICAL
        }
        val dayCells = mutableListOf<TextView>()

        fun ymd(c: Calendar): Int =
            c.get(Calendar.YEAR) * 10000 + c.get(Calendar.MONTH) * 100 + c.get(Calendar.DAY_OF_MONTH)

        fun sameDay(a: Calendar, b: Calendar): Boolean = ymd(a) == ymd(b)

        fun rebuildGrid() {
            gridHost.removeAllViews()
            dayCells.clear()
            monthTitle.text = String.format(
                Locale.CHINA,
                "%d年%d月",
                viewMonth.get(Calendar.YEAR),
                viewMonth.get(Calendar.MONTH) + 1,
            )

            val weekRow = LinearLayout(themed).apply {
                orientation = LinearLayout.HORIZONTAL
                setPadding(0, 0, 0, dp(themed, 4))
            }
            for (w in listOf("日", "一", "二", "三", "四", "五", "六")) {
                weekRow.addView(TextView(themed).apply {
                    text = w
                    setTextColor(0xFF667788.toInt())
                    textSize = 11f
                    typeface = Typeface.MONOSPACE
                    gravity = Gravity.CENTER
                    layoutParams = LinearLayout.LayoutParams(0, dp(themed, 22), 1f)
                })
            }
            gridHost.addView(weekRow)

            val grid = GridLayout(themed).apply {
                columnCount = 7
                rowCount = 6
            }
            val first = viewMonth.clone() as Calendar
            val lead = first.get(Calendar.DAY_OF_WEEK) - Calendar.SUNDAY // 0=Sun
            val daysInMonth = first.getActualMaximum(Calendar.DAY_OF_MONTH)
            val cellH = dp(themed, 34)
            val totalSlots = 42
            for (i in 0 until totalSlots) {
                val cell = TextView(themed).apply {
                    gravity = Gravity.CENTER
                    textSize = 12f
                    typeface = Typeface.MONOSPACE
                    layoutParams = GridLayout.LayoutParams().apply {
                        width = 0
                        height = cellH
                        columnSpec = GridLayout.spec(i % 7, 1f)
                        rowSpec = GridLayout.spec(i / 7)
                        setMargins(dp(themed, 2), dp(themed, 2), dp(themed, 2), dp(themed, 2))
                    }
                }
                val dayNum = i - lead + 1
                if (dayNum in 1..daysInMonth) {
                    val dayCal = (first.clone() as Calendar).apply { set(Calendar.DAY_OF_MONTH, dayNum) }
                    cell.text = dayNum.toString()
                    val inRange = !dayCal.before(startCal) && !dayCal.after(todayCal)
                    val isToday = sameDay(dayCal, todayCal)
                    val isStart = sameDay(dayCal, startCal)
                    when {
                        isToday -> {
                            cell.setTextColor(0xFF141824.toInt())
                            cell.background = pill(themed, 0xFFFF88CC.toInt())
                            cell.alpha = 0f
                            dayCells.add(cell)
                        }
                        inRange -> {
                            cell.setTextColor(0xFFEEF2FF.toInt())
                            cell.background = pill(themed, if (isStart) 0xFF4488DD.toInt() else 0xFF2A5080.toInt())
                            cell.alpha = 0f
                            dayCells.add(cell)
                        }
                        dayCal.after(todayCal) -> {
                            cell.setTextColor(0xFF445566.toInt())
                            cell.setBackgroundColor(0x00000000)
                        }
                        else -> {
                            cell.setTextColor(0xFF556677.toInt())
                            cell.setBackgroundColor(0x00000000)
                        }
                    }
                } else {
                    cell.text = ""
                    cell.setBackgroundColor(0x00000000)
                }
                grid.addView(cell)
            }
            gridHost.addView(grid)
            playMarkAnim(dayCells)
        }

        val nav = LinearLayout(themed).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, 0, 0, dp(themed, 6))
            addView(TextView(themed).apply {
                text = "‹"
                setTextColor(0xFFFF88CC.toInt())
                textSize = 22f
                typeface = Typeface.MONOSPACE
                setPadding(dp(themed, 10), 0, dp(themed, 10), 0)
                setOnClickListener {
                    viewMonth.add(Calendar.MONTH, -1)
                    rebuildGrid()
                }
            })
            addView(monthTitle)
            addView(TextView(themed).apply {
                text = "›"
                setTextColor(0xFFFF88CC.toInt())
                textSize = 22f
                typeface = Typeface.MONOSPACE
                setPadding(dp(themed, 10), 0, dp(themed, 10), 0)
                setOnClickListener {
                    viewMonth.add(Calendar.MONTH, 1)
                    rebuildGrid()
                }
            })
        }
        root.addView(nav)
        root.addView(gridHost)

        root.addView(TextView(themed).apply {
            text = "蓝＝认主日 · 青格＝已相伴 · 粉＝今天"
            setTextColor(0xFF667788.toInt())
            textSize = 10f
            typeface = Typeface.MONOSPACE
            setPadding(0, dp(themed, 6), 0, dp(themed, 4))
        })

        val detailHost = LinearLayout(themed).apply {
            orientation = LinearLayout.VERTICAL
            visibility = View.GONE
            setPadding(0, dp(themed, 4), 0, 0)
        }
        val labels = listOf(
            "free" to "一起自由",
            "follow" to "一起跟随",
            "stroll" to "一起漫步",
            "quiet" to "一起睡眠",
            "work" to "一起工作",
            "game" to "一起游戏",
            "music" to "一起听歌",
            "video" to "一起看视频",
        )
        val secMap = ModeTimeStore.secondsMap(context)
        for ((k, label) in labels) {
            val sec = secMap[k]?.toLong() ?: 0L
            detailHost.addView(TextView(themed).apply {
                text = "$label  ${ModeTimeStore.formatDuration(sec)}"
                setTextColor(if (sec > 0) 0xFF88FFCC.toInt() else 0xFF556677.toInt())
                textSize = 12f
                typeface = Typeface.MONOSPACE
                setPadding(0, dp(themed, 2), 0, 0)
            })
        }

        val detailBtn = TextView(themed).apply {
            text = "查看详细 · 一起听歌/工作 ▾"
            setTextColor(0xFFFF88CC.toInt())
            textSize = 12f
            typeface = Typeface.MONOSPACE
            setPadding(0, dp(themed, 6), 0, 0)
            setOnClickListener {
                val open = detailHost.visibility != View.VISIBLE
                detailHost.visibility = if (open) View.VISIBLE else View.GONE
                text = if (open) "收起详细 ▴" else "查看详细 · 一起听歌/工作 ▾"
            }
        }
        root.addView(detailBtn)
        root.addView(detailHost)

        root.addView(Button(themed).apply {
            text = "关闭"
            setOnClickListener { openDialog?.dismiss() }
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT,
            ).also {
                it.gravity = Gravity.END
                it.topMargin = dp(themed, 10)
            }
        })

        val scroll = ScrollView(themed).apply {
            addView(root)
            isFillViewport = true
        }

        rebuildGrid()

        val dialog = Dialog(themed)
        dialog.setContentView(scroll)
        dialog.setCancelable(true)
        dialog.setOnDismissListener { openDialog = null }
        dialog.window?.apply {
            setBackgroundDrawableResource(android.R.color.transparent)
            setLayout(
                (themed.resources.displayMetrics.widthPixels * 0.9f).toInt(),
                WindowManager.LayoutParams.WRAP_CONTENT,
            )
            try {
                setType(WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY)
            } catch (_: Exception) {
            }
            addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND)
            attributes = attributes?.also {
                it.dimAmount = 0.45f
                it.format = PixelFormat.TRANSLUCENT
            }
        }
        openDialog = dialog
        dialog.show()
        // 整板轻弹入
        scroll.alpha = 0f
        scroll.translationY = dp(themed, 24).toFloat()
        scroll.animate()
            .alpha(1f)
            .translationY(0f)
            .setDuration(280L)
            .setInterpolator(DecelerateInterpolator())
            .start()
    }

    private fun playMarkAnim(cells: List<TextView>) {
        cells.forEachIndexed { i, v ->
            v.animate().cancel()
            v.alpha = 0f
            v.scaleX = 0.6f
            v.scaleY = 0.6f
            handler.postDelayed({
                if (v.isAttachedToWindow) {
                    v.animate()
                        .alpha(1f)
                        .scaleX(1f)
                        .scaleY(1f)
                        .setDuration(160L)
                        .setInterpolator(DecelerateInterpolator())
                        .start()
                }
            }, 40L * i)
        }
    }

    private fun pill(context: Context, color: Int): GradientDrawable =
        GradientDrawable().apply {
            shape = GradientDrawable.RECTANGLE
            cornerRadius = dp(context, 6).toFloat()
            setColor(color)
        }

    private fun dp(context: Context, v: Int): Int =
        TypedValue.applyDimension(
            TypedValue.COMPLEX_UNIT_DIP,
            v.toFloat(),
            context.resources.displayMetrics,
        ).toInt()
}
