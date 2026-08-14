package com.vpet.mobile

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.util.LruCache

/**
 * 采集下落物像素食物：对照桌面 `_pil_draw_pixel_food` / `_render_game_drop_rgb`。
 */
object FoodPixelArt {
    private val cache = object : LruCache<String, Bitmap>(48) {
        override fun sizeOf(key: String, value: Bitmap): Int = 1
    }

    fun bitmapFor(foodId: String, sizePx: Int): Bitmap {
        val key = "$foodId@$sizePx"
        cache.get(key)?.let { if (!it.isRecycled) return it }
        val bmp = render(foodId, sizePx.coerceAtLeast(24))
        cache.put(key, bmp)
        return bmp
    }

    private fun render(foodId: String, size: Int): Bitmap {
        val out = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(out)
        canvas.drawColor(Color.TRANSPARENT)
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.FILL }
        val px = maxOf(8, size / 5)
        val body = px * 4
        val dx = maxOf(1, (size - body) / 2)
        val dy = maxOf(1, (size - body) / 2)
        drawFood(canvas, paint, foodId, dx, dy, px)
        return out
    }

    private fun drawFood(c: Canvas, p: Paint, foodId: String, x: Int, y: Int, px: Int) {
        fun rect(x0: Int, y0: Int, x1: Int, y1: Int, color: String) {
            if (x1 <= x0 || y1 <= y0) return
            p.color = Color.parseColor(color)
            c.drawRect(x0.toFloat(), y0.toFloat(), x1.toFloat(), y1.toFloat(), p)
        }
        fun oval(x0: Int, y0: Int, x1: Int, y1: Int, color: String) {
            if (x1 <= x0 || y1 <= y0) return
            p.color = Color.parseColor(color)
            c.drawOval(RectF(x0.toFloat(), y0.toFloat(), x1.toFloat(), y1.toFloat()), p)
        }
        fun poly(pts: List<Pair<Int, Int>>, color: String) {
            if (pts.size < 3) return
            p.color = Color.parseColor(color)
            val path = Path()
            path.moveTo(pts[0].first.toFloat(), pts[0].second.toFloat())
            for (i in 1 until pts.size) path.lineTo(pts[i].first.toFloat(), pts[i].second.toFloat())
            path.close()
            c.drawPath(path, p)
        }
        when (foodId) {
            "bread" -> {
                rect(x, y + px, x + px * 4, y + px * 3, "#d4a056")
                rect(x + px, y, x + px * 3, y + px, "#e8b870")
            }
            "apple" -> {
                oval(x, y + px, x + px * 3, y + px * 4, "#ee4444")
                rect(x + px, y, x + px * 2, y + px, "#66aa33")
            }
            "cake" -> {
                rect(x, y + px * 2, x + px * 4, y + px * 4, "#ff88cc")
                rect(x + px, y + px, x + px * 3, y + px * 2, "#ffcc66")
                rect(x + px * 2, y, x + px * 3, y + px, "#ff4466")
            }
            "fish" -> {
                poly(
                    listOf(x to y + px * 2, x + px * 4 to y + px, x + px * 4 to y + px * 3),
                    "#88bbee",
                )
                rect(x + px, y + px, x + px * 2, y + px * 2, "#ffffff")
            }
            "onigiri" -> {
                poly(
                    listOf(x + px * 2 to y, x + px * 4 to y + px * 4, x to y + px * 4),
                    "#f5f5ee",
                )
                rect(x + px, y + px * 2, x + px * 3, y + px * 3, "#224422")
            }
            "candy" -> {
                rect(x + px, y + px, x + px * 3, y + px * 3, "#ff6688")
                rect(x + px * 2, y, x + px * 3, y + px * 4, "#ffcc44")
            }
            "tea" -> {
                rect(x, y + px * 2, x + px * 4, y + px * 4, "#cc8844")
                rect(x + px, y + px, x + px * 3, y + px * 2, "#aa6633")
                rect(x + px * 2, y, x + px * 3, y + px, "#cccccc")
            }
            "meat" -> {
                oval(x, y + px, x + px * 4, y + px * 3, "#cc5533")
                rect(x + px, y + px * 2, x + px * 3, y + px * 3, "#aa3322")
            }
            "berry" -> {
                poly(
                    listOf(
                        x + px * 2 to y,
                        x + px * 4 to y + px * 2,
                        x + px * 3 to y + px * 4,
                        x + px to y + px * 4,
                        x to y + px * 2,
                    ),
                    "#ee3355",
                )
                rect(x + px, y, x + px * 2, y + px, "#66aa33")
            }
            "donut" -> {
                oval(x, y + px, x + px * 4, y + px * 4, "#d4a056")
                oval(x + px, y + px * 2, x + px * 3, y + px * 3, "#111122")
                oval(x, y + px, x + px * 4, y + px * 3, "#ff88cc")
            }
            "milk" -> {
                rect(x + px, y + px, x + px * 3, y + px * 4, "#f5f8ff")
                rect(x + px * 2, y, x + px * 3, y + px, "#88aacc")
            }
            "ramen" -> {
                oval(x, y + px * 2, x + px * 4, y + px * 4, "#cc8844")
                rect(x + px, y + px, x + px * 3, y + px * 2, "#ffdd88")
                rect(x + px, y + px * 2, x + px * 3, y + px * 2 + maxOf(1, px / 2), "#dd6633")
            }
            "sushi" -> {
                rect(x, y + px * 2, x + px * 4, y + px * 3, "#ffffff")
                oval(x + px, y + px, x + px * 3, y + px * 2, "#ee5566")
                rect(x + px, y + px * 3, x + px * 3, y + px * 4, "#224422")
            }
            "cookie" -> {
                oval(x + px, y + px, x + px * 3, y + px * 3, "#c98a4a")
                oval(
                    x + px * 2, y + px * 2,
                    x + px * 2 + maxOf(1, px / 2), y + px * 2 + maxOf(1, px / 2),
                    "#6b3f22",
                )
            }
            "juice" -> {
                rect(x + px, y + px, x + px * 3, y + px * 4, "#ffaa44")
                rect(x + px * 2, y, x + px * 3, y + px, "#88cc66")
                rect(x + px, y + px * 3, x + px * 3, y + px * 4, "#ff8844")
            }
            "taco" -> {
                poly(
                    listOf(x + px to y + px * 3, x + px * 4 to y + px * 3, x + px * 3 to y + px),
                    "#e8c060",
                )
                rect(x + px, y + px * 2, x + px * 3, y + px * 3, "#66aa44")
            }
            "icecream" -> {
                poly(
                    listOf(x + px * 2 to y + px * 3, x + px to y + px * 4, x + px * 3 to y + px * 4),
                    "#e8c878",
                )
                oval(x + px, y + px, x + px * 3, y + px * 3, "#ffccdd")
            }
            "corn" -> {
                rect(x + px * 2, y, x + px * 3, y + px * 4, "#88aa44")
                oval(x + px, y + px, x + px * 3, y + px * 4, "#ffdd66")
            }
            else -> rect(x, y + px, x + px * 4, y + px * 3, "#6688aa")
        }
    }
}
