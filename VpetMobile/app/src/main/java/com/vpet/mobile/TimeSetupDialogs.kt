package com.vpet.mobile

import android.app.Dialog
import android.content.Context
import android.graphics.PixelFormat
import android.text.InputType
import android.util.TypedValue
import android.view.Gravity
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.SeekBar
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.view.ContextThemeWrapper

/** 计时器 / 番茄钟 / 工作自定义 / 音量。 */
object TimeSetupDialogs {

    fun showVolumeSetup(context: Context, voice: Boolean) {
        val themed = ContextThemeWrapper(context, R.style.Theme_VpetMobile)
        val pad = dp(context, 12)
        val box = LinearLayout(themed).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(pad, pad, pad, pad)
            setBackgroundColor(0xE0141824.toInt())
        }
        val title = if (voice) "语音音量" else "音效音量"
        box.addView(header(themed, title))
        box.addView(
            hint(
                themed,
                if (voice) "调节桌宠语音播放响度" else "调节打字等音效响度",
            ),
        )
        val valueTv = TextView(themed).apply {
            text = "${if (voice) AppDataStore.voiceVolume(context) else AppDataStore.sfxVolume(context)}%"
            setTextColor(0xFFFF88CC.toInt())
            textSize = AppDataStore.fontBodySp(context)
            typeface = android.graphics.Typeface.MONOSPACE
        }
        box.addView(valueTv)
        val seek = SeekBar(themed).apply {
            max = 100
            progress = if (voice) AppDataStore.voiceVolume(context) else AppDataStore.sfxVolume(context)
            setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(seekBar: SeekBar?, p: Int, fromUser: Boolean) {
                    valueTv.text = "$p%"
                    if (fromUser) {
                        if (voice) AppDataStore.setVoiceVolume(context, p)
                        else AppDataStore.setSfxVolume(context, p)
                    }
                }
                override fun onStartTrackingTouch(seekBar: SeekBar?) {}
                override fun onStopTrackingTouch(seekBar: SeekBar?) {}
            })
        }
        box.addView(seek)
        val holder = arrayOfNulls<Dialog>(1)
        box.addView(
            Button(themed).apply {
                text = "关闭"
                setOnClickListener { holder[0]?.dismiss() }
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.WRAP_CONTENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT,
                ).also {
                    it.gravity = Gravity.END
                    it.topMargin = dp(context, 10)
                }
            },
        )
        holder[0] = showOverlayDialog(themed, box)
    }

    fun showTimerSetup(context: Context, onStart: (durationMs: Long) -> Unit) {
        val themed = ContextThemeWrapper(context, R.style.Theme_VpetMobile)
        val pad = dp(context, 12)
        val box = LinearLayout(themed).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(pad, pad, pad, pad)
            setBackgroundColor(0xE0141824.toInt())
        }
        box.addView(header(themed, "计时器"))
        box.addView(hint(themed, "自由填分/秒，到点提示"))
        val mins = numField(themed, "25")
        val secs = numField(themed, "0")
        box.addView(
            LinearLayout(themed).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                addView(label(themed, "分"))
                addView(mins)
                addView(label(themed, "秒").also { v ->
                    (v.layoutParams as LinearLayout.LayoutParams).marginStart = dp(context, 12)
                })
                addView(secs)
            },
        )
        val holder = arrayOfNulls<Dialog>(1)
        box.addView(
            actionRow(themed, context, onCancel = { holder[0]?.dismiss() }) {
                val m = mins.text.toString().trim().toIntOrNull() ?: 0
                val s = (secs.text.toString().trim().toIntOrNull() ?: 0).coerceIn(0, 59)
                val totalMs = (m.coerceAtLeast(0) * 60 + s) * 1000L
                if (totalMs < 1000L) {
                    Toast.makeText(context, "至少 1 秒", Toast.LENGTH_SHORT).show()
                    return@actionRow
                }
                holder[0]?.dismiss()
                onStart(totalMs)
            },
        )
        holder[0] = showOverlayDialog(themed, box)
    }

    fun showPomodoroSetup(context: Context, onStart: (workMin: Int, restMin: Int) -> Unit) {
        val themed = ContextThemeWrapper(context, R.style.Theme_VpetMobile)
        val pad = dp(context, 12)
        val box = LinearLayout(themed).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(pad, pad, pad, pad)
            setBackgroundColor(0xE0141824.toInt())
        }
        box.addView(header(themed, "番茄钟"))
        box.addView(hint(themed, "工作=运送 · 休息=睡眠；自由设分钟"))
        val work = numField(themed, "25")
        val rest = numField(themed, "5")
        box.addView(labeledRow(themed, "工作(分)", work))
        box.addView(labeledRow(themed, "休息(分)", rest))
        val holder = arrayOfNulls<Dialog>(1)
        box.addView(
            actionRow(themed, context, onCancel = { holder[0]?.dismiss() }) {
                val w = (work.text.toString().trim().toIntOrNull() ?: 25).coerceIn(1, 180)
                val r = (rest.text.toString().trim().toIntOrNull() ?: 5).coerceIn(1, 60)
                holder[0]?.dismiss()
                onStart(w, r)
            },
        )
        holder[0] = showOverlayDialog(themed, box)
    }

    /**
     * 自定义运送：箱数或时间二选一（对照桌面 `_open_work_custom_dialog`）。
     */
    fun showWorkCustomSetup(
        context: Context,
        onBoxes: (count: Int) -> Unit,
        onTimed: (durationMs: Long) -> Unit,
    ) {
        val themed = ContextThemeWrapper(context, R.style.Theme_VpetMobile)
        val pad = dp(context, 12)
        val box = LinearLayout(themed).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(pad, pad, pad, pad)
            setBackgroundColor(0xE0141824.toInt())
        }
        box.addView(header(themed, "自定义运送"))
        box.addView(hint(themed, "箱数或时间二选一；到量或到点后自动结束（1–30 箱）"))

        var byBoxes = true
        val modeHint = TextView(themed).apply {
            text = "当前：按箱数"
            setTextColor(0xFF88CCFF.toInt())
            textSize = AppDataStore.fontHintSp(context)
            typeface = android.graphics.Typeface.MONOSPACE
            setPadding(0, 0, 0, dp(context, 8))
        }
        box.addView(modeHint)

        val boxesField = numField(themed, "5")
        val mins = numField(themed, "25")
        val secs = numField(themed, "0")
        val boxesRow = labeledRow(themed, "货物数", boxesField)
        val timeRow = LinearLayout(themed).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, dp(context, 8), 0, 0)
            addView(label(themed, "时长"))
            addView(mins)
            addView(label(themed, "分").also { v ->
                (v.layoutParams as LinearLayout.LayoutParams).marginStart = dp(context, 4)
            })
            addView(secs.also { v ->
                (v.layoutParams as LinearLayout.LayoutParams).marginStart = dp(context, 8)
            })
            addView(label(themed, "秒"))
        }
        box.addView(boxesRow)
        box.addView(timeRow)

        fun refreshMode() {
            modeHint.text = if (byBoxes) "当前：按箱数" else "当前：按时间"
            boxesField.isEnabled = byBoxes
            mins.isEnabled = !byBoxes
            secs.isEnabled = !byBoxes
            boxesField.alpha = if (byBoxes) 1f else 0.4f
            mins.alpha = if (byBoxes) 0.4f else 1f
            secs.alpha = if (byBoxes) 0.4f else 1f
        }
        refreshMode()

        box.addView(
            LinearLayout(themed).apply {
                orientation = LinearLayout.HORIZONTAL
                setPadding(0, dp(context, 4), 0, 0)
                addView(Button(themed).apply {
                    text = "按箱数"
                    setOnClickListener {
                        byBoxes = true
                        refreshMode()
                    }
                })
                addView(Button(themed).apply {
                    text = "按时间"
                    setOnClickListener {
                        byBoxes = false
                        refreshMode()
                    }
                    layoutParams = LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.WRAP_CONTENT,
                        LinearLayout.LayoutParams.WRAP_CONTENT,
                    ).also { it.marginStart = dp(context, 8) }
                })
            },
        )

        val holder = arrayOfNulls<Dialog>(1)
        box.addView(
            actionRow(themed, context, onCancel = { holder[0]?.dismiss() }, okText = "开始") {
                if (byBoxes) {
                    val n = (boxesField.text.toString().trim().toIntOrNull() ?: 5)
                        .coerceIn(WORK_BOX_MIN, WORK_BOX_MAX)
                    holder[0]?.dismiss()
                    onBoxes(n)
                } else {
                    val m = (mins.text.toString().trim().toIntOrNull() ?: 0).coerceAtLeast(0)
                    val s = (secs.text.toString().trim().toIntOrNull() ?: 0).coerceIn(0, 59)
                    val totalMs = (m * 60 + s) * 1000L
                    if (totalMs < 1000L) {
                        Toast.makeText(context, "至少 1 秒", Toast.LENGTH_SHORT).show()
                        return@actionRow
                    }
                    holder[0]?.dismiss()
                    onTimed(totalMs)
                }
            },
        )
        holder[0] = showOverlayDialog(themed, box)
    }

    private const val WORK_BOX_MIN = 1
    private const val WORK_BOX_MAX = 30

    private fun actionRow(
        themed: Context,
        context: Context,
        onCancel: () -> Unit,
        okText: String = "开始",
        onOk: () -> Unit,
    ): LinearLayout =
        LinearLayout(themed).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.END
            setPadding(0, dp(context, 12), 0, 0)
            addView(Button(themed).apply {
                text = "取消"
                setOnClickListener { onCancel() }
            })
            addView(
                Button(themed).apply {
                    text = okText
                    setOnClickListener { onOk() }
                    layoutParams = LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.WRAP_CONTENT,
                        LinearLayout.LayoutParams.WRAP_CONTENT,
                    ).also { it.marginStart = dp(context, 8) }
                },
            )
        }

    private fun showOverlayDialog(context: Context, content: LinearLayout): Dialog {
        val dialog = Dialog(context)
        dialog.setContentView(content)
        dialog.setCancelable(true)
        dialog.window?.apply {
            setBackgroundDrawableResource(android.R.color.transparent)
            setLayout(
                (context.resources.displayMetrics.widthPixels * 0.82f).toInt(),
                WindowManager.LayoutParams.WRAP_CONTENT,
            )
            try {
                setType(WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY)
            } catch (_: Exception) {
            }
            addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND)
            attributes = attributes?.also {
                it.dimAmount = 0.4f
                it.format = PixelFormat.TRANSLUCENT
            }
        }
        dialog.show()
        return dialog
    }

    private fun header(context: Context, text: String) =
        TextView(context).apply {
            this.text = text
            setTextColor(0xFFFF88CC.toInt())
            textSize = AppDataStore.fontTitleSp(context)
            typeface = android.graphics.Typeface.MONOSPACE
        }

    private fun hint(context: Context, text: String) =
        TextView(context).apply {
            this.text = text
            setTextColor(0xFF8899AA.toInt())
            textSize = AppDataStore.fontHintSp(context)
            typeface = android.graphics.Typeface.MONOSPACE
            setPadding(0, dp(context, 4), 0, dp(context, 8))
        }

    private fun labeledRow(context: Context, title: String, field: EditText): LinearLayout =
        LinearLayout(context).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, dp(context, 8), 0, 0)
            addView(
                TextView(context).apply {
                    text = title
                    setTextColor(0xFFEEF2FF.toInt())
                    textSize = AppDataStore.fontBodySp(context)
                    typeface = android.graphics.Typeface.MONOSPACE
                    layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
                },
            )
            addView(field)
        }

    private fun label(context: Context, text: String): TextView =
        TextView(context).apply {
            this.text = text
            setTextColor(0xFFEEF2FF.toInt())
            textSize = AppDataStore.fontBodySp(context)
            typeface = android.graphics.Typeface.MONOSPACE
            setPadding(0, 0, dp(context, 4), 0)
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT,
            )
        }

    private fun numField(context: Context, default: String): EditText =
        EditText(context).apply {
            setText(default)
            inputType = InputType.TYPE_CLASS_NUMBER
            setSelection(text.length)
            setTextColor(0xFFEEF2FF.toInt())
            setHintTextColor(0xFF667788.toInt())
            setBackgroundColor(0xFF1A2838.toInt())
            setTextSize(TypedValue.COMPLEX_UNIT_SP, AppDataStore.fontBodySp(context))
            setPadding(dp(context, 10), dp(context, 8), dp(context, 10), dp(context, 8))
            layoutParams = LinearLayout.LayoutParams(dp(context, 72), LinearLayout.LayoutParams.WRAP_CONTENT)
        }

    private fun dp(context: Context, v: Int): Int =
        TypedValue.applyDimension(
            TypedValue.COMPLEX_UNIT_DIP,
            v.toFloat(),
            context.resources.displayMetrics,
        ).toInt()
}
