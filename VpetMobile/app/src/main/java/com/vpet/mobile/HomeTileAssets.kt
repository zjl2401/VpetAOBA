package com.vpet.mobile

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt
import kotlin.math.sqrt

/**
 * 家园贴图：对照桌面 `home_cottage._draw_furniture_rgb` / `_load_rpg_rgba`
 * （RPG 素材 + 室内家具像素块）。
 */
object HomeTileAssets {
    private const val FURN = "#6AA8D8"

    private val petal = arrayOf(
        "#FF7799", "#FFCC66", "#FF88CC", "#88DDFF", "#FFAA55", "#EE88FF",
        "#FF6666", "#66EECC", "#FFDD44", "#C080FF", "#FF90A8", "#70D0FF",
    )

    private data class Key(val kind: String, val tile: Int, val filled: Boolean)

    private val cache = mutableMapOf<Key, Bitmap?>()
    private val rawCache = mutableMapOf<String, Bitmap?>()

    fun clearCache() {
        cache.values.forEach { it?.recycle() }
        cache.clear()
    }

    fun bitmap(context: Context, kind: String, tilePx: Int): Bitmap? {
        val t = tilePx.coerceIn(12, 256)
        val filled = kind == "vase_filled"
        val baseKind = when (kind) {
            "vase_filled" -> "vase"
            "gift", "gift_art" -> "gift_art"
            "paint", "user_paint", "art" -> "user_paint"
            "home", "cabin" -> "house"
            else -> kind
        }
        val key = Key(baseKind, t, filled)
        if (cache.containsKey(key)) return cache[key]
        val bmp = build(context, baseKind, t, filled)
        cache[key] = bmp
        return bmp
    }

    private fun build(context: Context, kind: String, tile: Int, vaseFilled: Boolean): Bitmap? {
        when (kind) {
            "grass", "land", "water", "brick", "rock", "path" -> {
                val name = if (kind == "path") "brick.png" else "$kind.png"
                loadRpg(context, name, tile, knock = false, pairTree = false)?.let { return it }
            }
            "tree" -> loadRpg(context, "tree.png", tile, knock = true, pairTree = true)?.let { return it }
            "house" -> loadRpg(context, "house.png", tile, knock = true, pairTree = false)?.let { return it }
            "gift_art" -> loadRpg(context, "gift_art.png", tile, knock = true, pairTree = false)?.let { return it }
            "user_paint" -> loadRpg(context, "user_paint.png", tile, knock = true, pairTree = false)?.let { return it }
        }
        return drawFurniture(kind, tile, vaseFilled)
    }

    private fun loadRaw(context: Context, name: String): Bitmap? {
        rawCache[name]?.let { return it }
        val bmp = try {
            context.assets.open("home/$name").use { BitmapFactory.decodeStream(it) }
                ?: context.assets.open("rpg/tiles/$name").use { BitmapFactory.decodeStream(it) }
        } catch (_: Exception) {
            null
        }
        rawCache[name] = bmp
        return bmp
    }

    private fun loadRpg(
        context: Context,
        name: String,
        tile: Int,
        knock: Boolean,
        pairTree: Boolean,
    ): Bitmap? {
        var img = loadRaw(context, name)?.copy(Bitmap.Config.ARGB_8888, true) ?: return null
        if (knock) {
            img = knockOuterBg(img, if (name.startsWith("tree")) 28f else 46f)
            img = if (pairTree) makePairTree(img, tile) else fitBottom(img, tile, tile)
        } else {
            img = fillTileStripEdge(img, tile)
        }
        return img
    }

    private fun fillTileStripEdge(src: Bitmap, tile: Int): Bitmap {
        var im = src
        val w = im.width
        val h = im.height
        if (w >= 4 && h >= 4) {
            fun dark(x: Int, y: Int): Boolean {
                val c = im.getPixel(x, y)
                val a = Color.alpha(c)
                return a >= 8 && maxOf(Color.red(c), Color.green(c), Color.blue(c)) <= 48
            }
            var edge = 0
            for (x in 0 until w) {
                if (dark(x, 0)) edge++
                if (dark(x, h - 1)) edge++
            }
            for (y in 0 until h) {
                if (dark(0, y)) edge++
                if (dark(w - 1, y)) edge++
            }
            if (edge >= ((w + h) * 1.5).toInt()) {
                im = Bitmap.createBitmap(im, 1, 1, w - 2, h - 2)
            }
        }
        return scaleNearest(im, tile, tile)
    }

    private fun knockOuterBg(src: Bitmap, tol: Float): Bitmap {
        val im = src.copy(Bitmap.Config.ARGB_8888, true)
        val w = im.width
        val h = im.height
        if (w < 2 || h < 2) return im
        val refs = mutableListOf<IntArray>()
        for ((x, y) in listOf(0 to 0, w - 1 to 0, 0 to h - 1, w - 1 to h - 1)) {
            val c = im.getPixel(x, y)
            if (Color.alpha(c) >= 16) {
                refs += intArrayOf(Color.red(c), Color.green(c), Color.blue(c))
            }
        }
        if (refs.isEmpty()) return im
        fun isKey(c: Int): Boolean {
            val a = Color.alpha(c)
            val r = Color.red(c)
            val g = Color.green(c)
            val b = Color.blue(c)
            if (a < 16) return true
            // 绿幕 / 近白 / 近黑
            if (g > 200 && r < 90 && b < 90) return true
            if (r > 240 && g > 240 && b > 240) return true
            if (r < 20 && g < 20 && b < 20 && a >= 8) return true
            for (ref in refs) {
                val dr = (r - ref[0]).toDouble()
                val dg = (g - ref[1]).toDouble()
                val db = (b - ref[2]).toDouble()
                if (sqrt(dr * dr + dg * dg + db * db) <= tol) return true
            }
            return false
        }
        val visited = BooleanArray(w * h)
        val stack = ArrayDeque<Int>()
        fun push(x: Int, y: Int) {
            if (x !in 0 until w || y !in 0 until h) return
            val i = y * w + x
            if (visited[i]) return
            if (!isKey(im.getPixel(x, y))) return
            visited[i] = true
            stack.add(i)
        }
        for (x in 0 until w) {
            push(x, 0); push(x, h - 1)
        }
        for (y in 0 until h) {
            push(0, y); push(w - 1, y)
        }
        while (stack.isNotEmpty()) {
            val i = stack.removeLast()
            val x = i % w
            val y = i / w
            im.setPixel(x, y, Color.TRANSPARENT)
            push(x + 1, y); push(x - 1, y); push(x, y + 1); push(x, y - 1)
        }
        return im
    }

    private fun fitBottom(src: Bitmap, tw: Int, th: Int): Bitmap {
        val sw = src.width.coerceAtLeast(1)
        val sh = src.height.coerceAtLeast(1)
        val scale = min(tw.toFloat() / sw, th.toFloat() / sh)
        val nw = max(1, (sw * scale).roundToInt())
        val nh = max(1, (sh * scale).roundToInt())
        val scaled = scaleNearest(src, nw, nh)
        val out = Bitmap.createBitmap(tw, th, Bitmap.Config.ARGB_8888)
        Canvas(out).drawBitmap(scaled, (tw - nw) / 2f, (th - nh).toFloat(), nearestPaint())
        if (scaled !== src) scaled.recycle()
        return out
    }

    private fun makePairTree(src: Bitmap, tile: Int): Bitmap {
        val slot = tile / 2
        val sw = src.width.coerceAtLeast(1)
        val sh = src.height.coerceAtLeast(1)
        val scale = min(slot.toFloat() / sw, tile.toFloat() / sh)
        val nw = max(1, (sw * scale).roundToInt())
        val nh = max(1, (sh * scale).roundToInt())
        val one = scaleNearest(src, nw, nh)
        val out = Bitmap.createBitmap(tile, tile, Bitmap.Config.ARGB_8888)
        val c = Canvas(out)
        val p = nearestPaint()
        val y = (tile - nh).toFloat()
        for (i in 0..1) {
            val x = i * slot + (slot - nw) / 2f
            c.drawBitmap(one, x, y, p)
        }
        if (one !== src) one.recycle()
        return out
    }

    private fun scaleNearest(src: Bitmap, w: Int, h: Int): Bitmap {
        if (src.width == w && src.height == h) return src
        val out = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        Canvas(out).drawBitmap(src, Rect(0, 0, src.width, src.height), Rect(0, 0, w, h), nearestPaint())
        return out
    }

    private fun nearestPaint() = Paint().apply {
        isFilterBitmap = false
        isAntiAlias = false
    }

    private fun drawFurniture(kind: String, tile: Int, vaseFilled: Boolean): Bitmap {
        val tw = tile
        val th = tile
        val img = Bitmap.createBitmap(tw, th, Bitmap.Config.ARGB_8888)
        val d = Canvas(img)
        val wood = FURN
        val woodD = shade(wood, 0.65f)
        val accent = blend(wood, "#88AACC", 0.45f)
        val fabric = blend(wood, "#DDEEFF", 0.55f)
        fun box(x0: Int, y0: Int, x1: Int, y1: Int, fill: String, outline: String? = null) {
            val p = Paint().apply { color = Color.parseColor(fill); style = Paint.Style.FILL }
            d.drawRect(x0.toFloat(), y0.toFloat(), x1.toFloat(), y1.toFloat(), p)
            if (outline != null) {
                p.style = Paint.Style.STROKE
                p.strokeWidth = 1f
                p.color = Color.parseColor(outline)
                d.drawRect(x0 + 0.5f, y0 + 0.5f, x1 - 0.5f, y1 - 0.5f, p)
            }
        }
        when (kind) {
            "bed" -> {
                box(2, 6, tw - 2, th - 2, wood, woodD)
                box(4, 4, tw - 4, th / 2 + 2, fabric, shade(fabric, 0.75f))
                box(tw - tile / 2 - 2, 2, tw - 4, th / 2, "#DDEEFF")
            }
            "table" -> {
                box(4, th / 3, tw - 4, th - 6, wood, woodD)
                box(6, th - 6, 10, th - 2, woodD)
                box(tw - 10, th - 6, tw - 6, th - 2, woodD)
            }
            "chair" -> {
                box(6, 4, tw - 6, 10, woodD)
                box(5, 10, tw - 5, th - 4, wood, woodD)
            }
            "sofa" -> {
                box(2, 8, tw - 2, th - 2, accent, shade(accent, 0.7f))
                box(2, 4, 10, th - 4, blend(accent, "#FFFFFF", 0.2f))
                box(tw - 10, 4, tw - 2, th - 4, blend(accent, "#FFFFFF", 0.2f))
                box(10, 6, tw - 10, th / 2 + 2, fabric)
            }
            "plant" -> {
                box(tile / 2 - 5, th - 10, tile / 2 + 5, th - 2, wood)
                box(tile / 2 - 8, 4, tile / 2 + 8, th - 10, "#44AA66", "#228844")
                box(tile / 2 - 3, 2, tile / 2 + 3, 8, "#66CC88")
            }
            "carpet" -> {
                val c1 = blend(wood, "#AA5566", 0.7f)
                box(1, 1, tw - 1, th - 1, c1, shade(c1, 0.7f))
                box(4, 4, tw - 4, th - 4, blend(c1, "#FFFFFF", 0.25f))
            }
            "shelf" -> {
                box(3, 2, tw - 3, th - 2, wood, woodD)
                box(5, th / 3, tw - 5, th / 3 + 3, blend(wood, "#FFFFFF", 0.15f))
                box(5, 2 * th / 3, tw - 5, 2 * th / 3 + 3, blend(wood, "#FFFFFF", 0.15f))
                box(7, 6, 14, 14, "#88CCFF")
                box(tw - 16, th / 2, tw - 7, th / 2 + 10, "#FFCC66")
            }
            "lamp" -> {
                box(tile / 2 - 3, th / 2, tile / 2 + 3, th - 2, "#555566")
                box(tile / 2 - 8, 4, tile / 2 + 8, th / 2, "#FFEE88", "#CCAA44")
            }
            "window" -> {
                box(2, 4, tw - 2, th - 4, "#88CCEE", "#446688")
                val mid = tw / 2
                box(mid - 1, 4, mid + 1, th - 4, "#446688")
                box(2, th / 2 - 1, tw - 2, th / 2 + 1, "#446688")
                box(0, 2, tw, 6, wood)
            }
            "door" -> {
                box(2, 1, tw - 2, th - 1, woodD, shade(woodD, 0.7f))
                box(5, 3, tw - 5, th - 2, wood, woodD)
                box(tw - 10, th / 2 - 1, tw - 7, th / 2 + 3, blend(wood, "#FFEE88", 0.35f))
                box(4, 2, tw - 4, 5, shade(wood, 0.55f))
            }
            "vase" -> {
                val body = "#B8C4CC"
                val rim = "#8A98A4"
                box(tile / 2 - 6, th / 2 + 2, tile / 2 + 6, th - 2, body, rim)
                box(tile / 2 - 8, th / 2 - 2, tile / 2 + 8, th / 2 + 4, "#D0D8E0", rim)
                box(tile / 2 - 4, th / 2 + 4, tile / 2 + 4, th - 4, "#A8B4BC")
                if (vaseFilled) {
                    for ((ox, oy, col) in listOf(
                        Triple(-4, -6, "#FF7799"), Triple(4, -6, "#FFCC66"),
                        Triple(0, -10, "#FF88CC"), Triple(0, -4, "#88DDFF"),
                    )) {
                        box(tile / 2 + ox - 2, th / 2 + oy - 2, tile / 2 + ox + 2, th / 2 + oy + 2, col)
                    }
                    box(tile / 2 - 1, th / 2 - 8, tile / 2 + 1, th / 2 + 2, "#44AA55")
                }
            }
            "flower" -> {
                box(tile / 2 - 2, th / 2, tile / 2 + 2, th - 2, "#44AA55")
                val cols = listOf(petal[0], petal[1], petal[2], petal[3])
                for ((ox, oy, col) in listOf(
                    Triple(-5, -2, cols[0]), Triple(5, -2, cols[1]),
                    Triple(0, -6, cols[2]), Triple(0, 2, cols[3]),
                )) {
                    box(tile / 2 + ox - 2, th / 2 + oy - 2, tile / 2 + ox + 2, th / 2 + oy + 2, col)
                }
            }
            "fence" -> {
                box(2, 8, tw - 2, 12, wood, woodD)
                box(4, 4, 8, th - 2, woodD)
                box(tw - 8, 4, tw - 4, th - 2, woodD)
            }
            "bush" -> {
                box(3, th / 3, tw - 3, th - 2, "#3A8844", "#226633")
                box(6, 4, tw - 6, th / 2, "#55AA66")
            }
            else -> {
                box(4, 4, tw - 4, th - 4, wood)
            }
        }
        return img
    }

    private fun shade(hex: String, factor: Float): String {
        val c = Color.parseColor(hex)
        fun ch(v: Int) = (v * factor).roundToInt().coerceIn(0, 255)
        return String.format("#%02X%02X%02X", ch(Color.red(c)), ch(Color.green(c)), ch(Color.blue(c)))
    }

    private fun blend(a: String, b: String, t: Float): String {
        val ca = Color.parseColor(a)
        val cb = Color.parseColor(b)
        fun ch(x: Int, y: Int) = (x + (y - x) * t).roundToInt().coerceIn(0, 255)
        return String.format(
            "#%02X%02X%02X",
            ch(Color.red(ca), Color.red(cb)),
            ch(Color.green(ca), Color.green(cb)),
            ch(Color.blue(ca), Color.blue(cb)),
        )
    }
}
