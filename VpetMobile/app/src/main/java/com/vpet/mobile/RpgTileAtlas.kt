package com.vpet.mobile

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF

/** RPG 瓦片图集：对照桌面 Vpetgame/assets 贴图。 */
object RpgTileAtlas {
    private val cache = mutableMapOf<String, Bitmap?>()

    fun clear() {
        cache.clear()
    }

    fun bmp(context: Context, name: String): Bitmap? {
        if (cache.containsKey(name)) return cache[name]
        val path = "rpg/tiles/$name"
        val b = try {
            context.assets.open(path).use { BitmapFactory.decodeStream(it) }
        } catch (_: Exception) {
            null
        }
        cache[name] = b
        return b
    }

    fun draw(
        context: Context,
        c: Canvas,
        tileId: Int,
        l: Float,
        t: Float,
        r: Float,
        b: Float,
        underground: Boolean,
        floorPaint: Paint,
        overlayPaint: Paint = Paint(Paint.ANTI_ALIAS_FLAG),
    ) {
        val floorName = when (tileId) {
            RpgMapLoader.LAND -> "land.png"
            RpgMapLoader.WATER -> "water.png"
            RpgMapLoader.BRICK -> "brick.png"
            RpgMapLoader.GRASS -> if (underground) null else "grass.png"
            RpgMapLoader.CAVE -> "cave.png"
            else -> if (underground) null else "grass.png"
        }
        val floorBmp = floorName?.let { bmp(context, it) }
        if (floorBmp != null) {
            c.drawBitmap(floorBmp, null, RectF(l, t, r, b), null)
        } else {
            floorPaint.color = if (underground) Color.parseColor("#1E1E28") else Color.parseColor("#1E2A3A")
            c.drawRect(l, t, r, b, floorPaint)
        }
        val overlay = when (tileId) {
            RpgMapLoader.TREE -> "tree.png"
            RpgMapLoader.ROCK, RpgMapLoader.MOUNTAIN -> "rock.png"
            RpgMapLoader.OBSTACLE -> "obstacle.png"
            RpgMapLoader.HOUSE -> "house.png"
            RpgMapLoader.STAIRS -> "stairs.png"
            RpgMapLoader.WATER -> null // already floor
            RpgMapLoader.TREASURE, RpgMapLoader.TREASURE_OPEN -> null
            else -> null
        }
        overlay?.let { name ->
            bmp(context, name)?.let { c.drawBitmap(it, null, RectF(l, t, r, b), null) }
        }
        when (tileId) {
            RpgMapLoader.PICKUP_COIN -> {
                overlayPaint.color = Color.parseColor("#FFDD66")
                c.drawCircle((l + r) / 2, (t + b) / 2, (r - l) * 0.18f, overlayPaint)
            }
            RpgMapLoader.TREASURE -> {
                // treasure.png 在 rpg/ 根
                val chest = loadRoot(context, "rpg/treasure.png")
                if (chest != null) c.drawBitmap(chest, null, RectF(l, t, r, b), null)
                else {
                    overlayPaint.color = Color.parseColor("#D4A017")
                    c.drawRect(l + 4, t + 4, r - 4, b - 4, overlayPaint)
                }
            }
            RpgMapLoader.TREASURE_OPEN -> {
                overlayPaint.color = Color.parseColor("#8B7355")
                c.drawRect(l + 4, t + 4, r - 4, b - 4, overlayPaint)
            }
            RpgMapLoader.GATE -> {
                overlayPaint.color = Color.parseColor("#44CC88")
                c.drawRect(l + 2, t + 2, r - 2, b - 2, overlayPaint)
            }
            RpgMapLoader.TRAP_SPIKE, RpgMapLoader.TRAP_PIT -> {
                overlayPaint.color = Color.parseColor("#FF4466")
                c.drawCircle((l + r) / 2, (t + b) / 2, (r - l) * 0.22f, overlayPaint)
            }
            RpgMapLoader.CAVE -> {
                // cave as floor already; darken a bit
            }
        }
    }

    private fun loadRoot(context: Context, path: String): Bitmap? {
        if (cache.containsKey(path)) return cache[path]
        val b = try {
            context.assets.open(path).use { BitmapFactory.decodeStream(it) }
        } catch (_: Exception) {
            null
        }
        cache[path] = b
        return b
    }
}
