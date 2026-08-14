package com.vpet.mobile

import android.app.Dialog
import android.content.Context
import android.graphics.PixelFormat
import android.util.TypedValue
import android.view.Gravity
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.view.ContextThemeWrapper

/**
 * 吃东西选食物：对照桌面 `_open_eat_food_menu`（像素图标 + 背包库存）。
 */
object FeedFoodPicker {
    fun show(context: Context, onFeed: (foodId: String) -> Unit) {
        FoodInventoryStore.ensureSeeded(context)
        val total = FoodCatalog.ALL.sumOf { FoodInventoryStore.count(context, it.id) }
        if (total <= 0) {
            Toast.makeText(context, "暂无食物。请先进行采集。", Toast.LENGTH_LONG).show()
            return
        }
        val themed = ContextThemeWrapper(context, R.style.Theme_VpetMobile)
        val pad = dp(context, 10)
        val bodySp = AppDataStore.fontBodySp(context)
        val box = LinearLayout(themed).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(pad, pad, pad, pad)
            setBackgroundColor(0xE0141824.toInt())
        }
        box.addView(
            TextView(themed).apply {
                text = "吃东西 · 背包（$total）"
                setTextColor(0xFFFF88CC.toInt())
                textSize = AppDataStore.fontTitleSp(context)
            },
        )
        box.addView(
            TextView(themed).apply {
                text = "点选有库存的食物"
                setTextColor(0xFF8899AA.toInt())
                textSize = AppDataStore.fontHintSp(context)
                setPadding(0, dp(context, 2), 0, dp(context, 6))
            },
        )
        val list = LinearLayout(themed).apply { orientation = LinearLayout.VERTICAL }
        val holder = arrayOfNulls<Dialog>(1)
        val iconPx = dp(context, 28)
        for (food in FoodCatalog.ALL.sortedByDescending { it.mood + it.stamina }) {
            val n = FoodInventoryStore.count(context, food.id)
            val enabled = n > 0
            val row = LinearLayout(themed).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                setPadding(dp(context, 8), dp(context, 6), dp(context, 8), dp(context, 6))
                setBackgroundColor(if (enabled) 0xFF1E2838.toInt() else 0xFF12161E.toInt())
                alpha = if (enabled) 1f else 0.45f
                layoutParams = LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT,
                ).also { it.bottomMargin = dp(context, 3) }
                if (enabled) {
                    setOnClickListener {
                        holder[0]?.dismiss()
                        onFeed(food.id)
                    }
                }
            }
            row.addView(
                ImageView(themed).apply {
                    setImageBitmap(FoodPixelArt.bitmapFor(food.id, iconPx))
                    layoutParams = LinearLayout.LayoutParams(iconPx, iconPx).also {
                        it.marginEnd = dp(context, 8)
                    }
                    scaleType = ImageView.ScaleType.FIT_CENTER
                },
            )
            row.addView(
                TextView(themed).apply {
                    text = "${food.label} ×$n  体+${food.stamina} 心+${food.mood}"
                    setTextColor(if (enabled) 0xFFEEF2FF.toInt() else 0xFF666666.toInt())
                    textSize = bodySp
                    layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
                },
            )
            list.addView(row)
        }
        val scroll = ScrollView(themed).apply {
            addView(list)
            layoutParams = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                dp(context, 280),
            )
        }
        box.addView(scroll)
        box.addView(
            TextView(themed).apply {
                text = "取消"
                gravity = Gravity.CENTER
                setTextColor(0xFFAAB8C8.toInt())
                textSize = bodySp
                setPadding(0, dp(context, 10), 0, dp(context, 4))
                setOnClickListener { holder[0]?.dismiss() }
            },
        )
        val dialog = Dialog(themed)
        holder[0] = dialog
        dialog.setContentView(box)
        dialog.setCancelable(true)
        dialog.window?.apply {
            setBackgroundDrawableResource(android.R.color.transparent)
            setLayout(
                (themed.resources.displayMetrics.widthPixels * 0.88f).toInt(),
                WindowManager.LayoutParams.WRAP_CONTENT,
            )
            setGravity(Gravity.BOTTOM)
            // 悬浮桌宠从 Service 上下文弹出：必须用 overlay 窗，否则 BadToken 闪退
            try {
                setType(WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY)
            } catch (_: Exception) {
            }
            addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND)
            attributes = attributes?.also {
                it.y = dp(context, 24)
                it.dimAmount = 0.4f
                it.format = PixelFormat.TRANSLUCENT
            }
        }
        try {
            dialog.show()
        } catch (e: Exception) {
            Toast.makeText(context, "无法打开吃东西菜单", Toast.LENGTH_SHORT).show()
        }
    }

    private fun dp(context: Context, v: Int): Int =
        TypedValue.applyDimension(
            TypedValue.COMPLEX_UNIT_DIP,
            v.toFloat(),
            context.resources.displayMetrics,
        ).toInt()
}
