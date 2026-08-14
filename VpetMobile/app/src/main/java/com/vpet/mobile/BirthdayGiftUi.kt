package com.vpet.mobile

import android.content.Context
import android.graphics.BitmapFactory
import android.view.Gravity
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AlertDialog

/** 生日祝福像素画弹窗（gift_art.png）。 */
object BirthdayGiftUi {
    fun showMessages(ctx: Context, messages: List<String>) {
        if (messages.isEmpty()) return
        val bmp = try {
            ctx.assets.open("home/gift_art.png").use { BitmapFactory.decodeStream(it) }
        } catch (_: Exception) {
            null
        }
        val box = LinearLayout(ctx).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 24, 32, 8)
            gravity = Gravity.CENTER_HORIZONTAL
            if (bmp != null) {
                addView(
                    ImageView(ctx).apply {
                        setImageBitmap(bmp)
                        adjustViewBounds = true
                        maxHeight = (ctx.resources.displayMetrics.heightPixels * 0.35f).toInt()
                    },
                )
            }
            addView(
                TextView(ctx).apply {
                    text = messages.joinToString("\n\n")
                    textSize = 15f
                    setPadding(0, 16, 0, 8)
                    gravity = Gravity.CENTER
                },
            )
        }
        AlertDialog.Builder(ctx)
            .setTitle("生日祝福")
            .setView(box)
            .setPositiveButton("好", null)
            .show()
    }
}
