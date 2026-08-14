package com.vpet.mobile

import android.app.Dialog
import android.content.Context
import android.graphics.PixelFormat
import android.text.InputType
import android.util.TypedValue
import android.view.Gravity
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.view.ContextThemeWrapper

/** 日程 / 生日：悬浮小窗编辑（不跳回 ToolsActivity）。 */
object ScheduleBirthdayDialogs {

    fun showSchedule(context: Context) {
        val themed = ContextThemeWrapper(context, R.style.Theme_VpetMobile)
        val pad = dp(context, 12)
        val box = LinearLayout(themed).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(pad, pad, pad, pad)
            setBackgroundColor(0xE0141824.toInt())
        }
        box.addView(header(themed, "日程提醒"))
        box.addView(hint(themed, "到点会 Toast 提示；点条目可删除"))

        val listHost = LinearLayout(themed).apply {
            orientation = LinearLayout.VERTICAL
        }
        fun refreshList() {
            listHost.removeAllViews()
            val arr = PetProfileStore.schedules(context)
            if (arr.length() == 0) {
                listHost.addView(hint(themed, "暂无日程"))
                return
            }
            for (i in 0 until arr.length()) {
                val o = arr.getJSONObject(i)
                val id = o.optString("id")
                val line = "${o.optString("time")}  ${o.optString("text")}"
                listHost.addView(
                    TextView(themed).apply {
                        text = line
                        setTextColor(0xFFEEF2FF.toInt())
                        textSize = 13f
                        setPadding(0, dp(context, 6), 0, dp(context, 6))
                        setOnClickListener {
                            PetProfileStore.removeSchedule(context, id)
                            Toast.makeText(context, "已删除", Toast.LENGTH_SHORT).show()
                            refreshList()
                        }
                    },
                )
            }
        }
        refreshList()
        box.addView(
            ScrollView(themed).apply {
                layoutParams = LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    (context.resources.displayMetrics.heightPixels * 0.22f).toInt(),
                )
                addView(listHost)
            },
        )

        val time = textField(themed, "08:30", InputType.TYPE_CLASS_DATETIME or InputType.TYPE_DATETIME_VARIATION_TIME)
        val content = textField(themed, "提醒内容", InputType.TYPE_CLASS_TEXT)
        content.hint = "提醒内容"
        content.setText("")
        box.addView(labeledField(themed, "时间 HH:MM", time))
        box.addView(labeledField(themed, "内容", content))

        val holder = arrayOfNulls<Dialog>(1)
        box.addView(
            LinearLayout(themed).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.END
                setPadding(0, dp(context, 12), 0, 0)
                addView(Button(themed).apply {
                    text = "关闭"
                    setOnClickListener { holder[0]?.dismiss() }
                })
                addView(
                    Button(themed).apply {
                        text = "添加"
                        setOnClickListener {
                            val ok = PetProfileStore.addSchedule(
                                context,
                                time.text.toString(),
                                content.text.toString(),
                            )
                            if (!ok) {
                                Toast.makeText(context, "时间用 HH:MM，内容不能空", Toast.LENGTH_SHORT).show()
                                return@setOnClickListener
                            }
                            content.setText("")
                            Toast.makeText(context, "已添加", Toast.LENGTH_SHORT).show()
                            refreshList()
                        }
                        layoutParams = LinearLayout.LayoutParams(
                            LinearLayout.LayoutParams.WRAP_CONTENT,
                            LinearLayout.LayoutParams.WRAP_CONTENT,
                        ).also { it.marginStart = dp(context, 8) }
                    },
                )
            },
        )
        holder[0] = showOverlayDialog(themed, box)
    }

    fun showBirthday(context: Context) {
        val themed = ContextThemeWrapper(context, R.style.Theme_VpetMobile)
        val pad = dp(context, 12)
        val box = LinearLayout(themed).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(pad, pad, pad, pad)
            setBackgroundColor(0xE0141824.toInt())
        }
        box.addView(header(themed, "生日祝福"))
        box.addView(hint(themed, "所属人生日 + 苍叶 4/22 礼物文案"))

        val p = PetProfileStore.profile(context)
        val month = numField(themed, p.optInt("bless_month").takeIf { it > 0 }?.toString() ?: "1")
        val day = numField(themed, p.optInt("bless_day").takeIf { it > 0 }?.toString() ?: "1")
        val msg = textField(themed, "祝福语", InputType.TYPE_CLASS_TEXT)
        msg.setText(p.optString("bless_message"))
        val gift = textField(themed, "礼物名", InputType.TYPE_CLASS_TEXT)
        gift.setText(p.optString("gift_text"))

        box.addView(
            LinearLayout(themed).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                setPadding(0, dp(context, 8), 0, 0)
                addView(label(themed, "月"))
                addView(month)
                addView(label(themed, "日").also { v ->
                    (v.layoutParams as LinearLayout.LayoutParams).marginStart = dp(context, 12)
                })
                addView(day)
            },
        )
        box.addView(labeledField(themed, "祝福语", msg))
        box.addView(labeledField(themed, "礼物（苍叶）", gift))

        val holder = arrayOfNulls<Dialog>(1)
        box.addView(
            LinearLayout(themed).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.END
                setPadding(0, dp(context, 12), 0, 0)
                addView(Button(themed).apply {
                    text = "取消"
                    setOnClickListener { holder[0]?.dismiss() }
                })
                addView(
                    Button(themed).apply {
                        text = "保存"
                        setOnClickListener {
                            val m = month.text.toString().trim().toIntOrNull() ?: 0
                            val d = day.text.toString().trim().toIntOrNull() ?: 0
                            if (m !in 1..12 || d !in 1..31) {
                                Toast.makeText(context, "请填写有效月/日", Toast.LENGTH_SHORT).show()
                                return@setOnClickListener
                            }
                            PetProfileStore.setBless(context, m, d, msg.text.toString())
                            PetProfileStore.setGiftText(context, gift.text.toString())
                            Toast.makeText(context, "已保存生日与礼物", Toast.LENGTH_SHORT).show()
                            holder[0]?.dismiss()
                        }
                        layoutParams = LinearLayout.LayoutParams(
                            LinearLayout.LayoutParams.WRAP_CONTENT,
                            LinearLayout.LayoutParams.WRAP_CONTENT,
                        ).also { it.marginStart = dp(context, 8) }
                    },
                )
            },
        )
        holder[0] = showOverlayDialog(themed, box)
    }

    private fun showOverlayDialog(context: Context, content: LinearLayout): Dialog {
        val dialog = Dialog(context)
        dialog.setContentView(content)
        dialog.setCancelable(true)
        dialog.window?.apply {
            setBackgroundDrawableResource(android.R.color.transparent)
            setLayout(
                (context.resources.displayMetrics.widthPixels * 0.86f).toInt(),
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
            textSize = 16f
        }

    private fun hint(context: Context, text: String) =
        TextView(context).apply {
            this.text = text
            setTextColor(0xFF8899AA.toInt())
            textSize = 12f
            setPadding(0, dp(context, 4), 0, dp(context, 8))
        }

    private fun label(context: Context, text: String): TextView =
        TextView(context).apply {
            this.text = text
            setTextColor(0xFFEEF2FF.toInt())
            textSize = 14f
            setPadding(0, 0, dp(context, 4), 0)
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT,
            )
        }

    private fun labeledField(context: Context, title: String, field: EditText): LinearLayout =
        LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(0, dp(context, 6), 0, 0)
            addView(
                TextView(context).apply {
                    text = title
                    setTextColor(0xFFEEF2FF.toInt())
                    textSize = 13f
                    setPadding(0, 0, 0, dp(context, 4))
                },
            )
            addView(field)
        }

    private fun numField(context: Context, default: String): EditText =
        EditText(context).apply {
            setText(default)
            inputType = InputType.TYPE_CLASS_NUMBER
            setSelection(text.length)
            styleField(this, context)
            layoutParams = LinearLayout.LayoutParams(dp(context, 64), LinearLayout.LayoutParams.WRAP_CONTENT)
        }

    private fun textField(context: Context, hintOrDefault: String, type: Int): EditText =
        EditText(context).apply {
            hint = hintOrDefault
            inputType = type
            styleField(this, context)
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT,
            )
        }

    private fun styleField(field: EditText, context: Context) {
        field.setTextColor(0xFFEEF2FF.toInt())
        field.setHintTextColor(0xFF667788.toInt())
        field.setBackgroundColor(0xFF1A2838.toInt())
        field.setPadding(dp(context, 10), dp(context, 8), dp(context, 10), dp(context, 8))
    }

    private fun dp(context: Context, v: Int): Int =
        TypedValue.applyDimension(
            TypedValue.COMPLEX_UNIT_DIP,
            v.toFloat(),
            context.resources.displayMetrics,
        ).toInt()
}
