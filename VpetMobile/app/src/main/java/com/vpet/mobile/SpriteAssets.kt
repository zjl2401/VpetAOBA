package com.vpet.mobile

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Matrix

/**
 * 默认人格立绘（非金目 nc*）：外圈绿幕抠图后的透明 PNG。
 * 四向：front / back / left；right = left 水平翻转（对齐桌面）。
 * 贴纸路径 `sticker/question|angry|like`：对照 pet.py `_add_sticker`。
 */
object SpriteAssets {
    const val STAND = "sprites/stand.png"
    const val HI1 = "sprites/hi1.png"
    const val HI2 = "sprites/hi2.png"
    const val SLEEP1 = "sprites/sleep1.png"
    const val SLEEP2 = "sprites/sleep2.png"
    const val HAPPY = "sprites/happy.png"

    const val WALK_FRONT1 = "sprites/walkfront1.png"
    const val WALK_FRONT2 = "sprites/walkfront2.png"
    const val WALK_BACK1 = "sprites/walkback1.png"
    const val WALK_BACK2 = "sprites/walkback2.png"
    const val WALK_LEFT1 = "sprites/walkleft1.png"
    const val WALK_LEFT2 = "sprites/walkleft2.png"

    const val WALK1 = WALK_FRONT1
    const val WALK2 = WALK_FRONT2

    const val WORK_STAND = "sprites/workstand.png"
    const val WORK_FRONT1 = "sprites/workfront1.png"
    const val WORK_FRONT2 = "sprites/workfront2.png"
    const val WORK_BACK1 = "sprites/workback1.png"
    const val WORK_BACK2 = "sprites/workback2.png"
    const val WORK_LEFT1 = "sprites/workleft1.png"
    const val WORK_LEFT2 = "sprites/workleft2.png"
    const val WORK_WALK1 = WORK_FRONT1
    const val WORK_WALK2 = WORK_FRONT2

    const val BOX = "sprites/box.png"
    const val FLAG = "sprites/flag.png"
    const val MUSIC_STAND = "sprites/musicstand.png"
    const val MUSIC_FRONT1 = "sprites/musicfront1.png"
    const val MUSIC_FRONT2 = "sprites/musicfront2.png"
    const val MUSIC_BACK1 = "sprites/musicback1.png"
    const val MUSIC_BACK2 = "sprites/musicback2.png"
    const val MUSIC_LEFT1 = "sprites/musicleft1.png"
    const val MUSIC_LEFT2 = "sprites/musicleft2.png"
    const val MUSIC_WALK1 = MUSIC_FRONT1
    const val MUSIC_WALK2 = MUSIC_FRONT2

    const val PLAY_GAME1 = "sprites/play_game1.png"
    const val PLAY_GAME2 = "sprites/play_game2.png"
    const val WATCH_VIDEO1 = "sprites/watch_video1.png"
    const val VIDEO = "sprites/video.png"
    const val ALLMATE = "sprites/allmate.png"
    val VIDEO_VARIANTS: Array<String> = arrayOf(
        "sprites/video_v0.png",
        "sprites/video_v1.png",
        "sprites/video_v2.png",
        "sprites/video_v3.png",
        "sprites/video_v4.png",
        "sprites/video_v5.png",
    )

    const val SAD1 = "sprites/sad1.png"
    const val SAD2 = "sprites/sad2.png"
    const val SHY1 = "sprites/shy1.png"
    const val SHY2 = "sprites/shy2.png"
    const val WINK = "sprites/wink.png"
    const val LIKE = "sprites/like.png"
    const val SQUAT = "sprites/squat.png"
    const val KICK = "sprites/kick.png"
    const val YES = "sprites/yes.png"
    const val NO = "sprites/no.png"
    const val CALL1 = "sprites/call1.png"
    const val CALL2 = "sprites/call2.png"
    const val EAT1 = "sprites/eat1.png"
    const val EAT2 = "sprites/eat2.png"
    const val MOVE1 = "sprites/move1.png"
    const val MOVE2 = "sprites/move2.png"
    const val MOVE3 = "sprites/move3.png"

    /** 站立 + 角标（对照 stand_question / stand_angry） */
    const val STAND_QUESTION = "sticker/question"
    const val STAND_ANGRY = "sticker/angry"
    const val STAND_LIKE = "sticker/like"

    enum class Dir(val dx: Int, val dy: Int) {
        FRONT(0, 1),
        BACK(0, -1),
        LEFT(-1, 0),
        RIGHT(1, 0),
        ;

        companion object {
            fun fromDelta(dx: Int, dy: Int): Dir {
                return if (kotlin.math.abs(dx) >= kotlin.math.abs(dy)) {
                    if (dx < 0) LEFT else if (dx > 0) RIGHT else FRONT
                } else {
                    if (dy < 0) BACK else FRONT
                }
            }

            fun random(): Dir = entries.random()
        }
    }

    enum class Outfit { NORMAL, WORK, MUSIC }

    data class Frame(val path: String, val flip: Boolean = false)

    fun walkFrame(outfit: Outfit, dir: Dir, frame2: Boolean): Frame {
        val i = if (frame2) 2 else 1
        return when (outfit) {
            Outfit.NORMAL -> when (dir) {
                Dir.FRONT -> Frame(if (i == 1) WALK_FRONT1 else WALK_FRONT2)
                Dir.BACK -> Frame(if (i == 1) WALK_BACK1 else WALK_BACK2)
                Dir.LEFT -> Frame(if (i == 1) WALK_LEFT1 else WALK_LEFT2)
                Dir.RIGHT -> Frame(if (i == 1) WALK_LEFT1 else WALK_LEFT2, flip = true)
            }
            Outfit.WORK -> when (dir) {
                Dir.FRONT -> Frame(if (i == 1) WORK_FRONT1 else WORK_FRONT2)
                Dir.BACK -> Frame(if (i == 1) WORK_BACK1 else WORK_BACK2)
                Dir.LEFT -> Frame(if (i == 1) WORK_LEFT1 else WORK_LEFT2)
                Dir.RIGHT -> Frame(if (i == 1) WORK_LEFT1 else WORK_LEFT2, flip = true)
            }
            Outfit.MUSIC -> when (dir) {
                Dir.FRONT -> Frame(if (i == 1) MUSIC_FRONT1 else MUSIC_FRONT2)
                Dir.BACK -> Frame(if (i == 1) MUSIC_BACK1 else MUSIC_BACK2)
                Dir.LEFT -> Frame(if (i == 1) MUSIC_LEFT1 else MUSIC_LEFT2)
                Dir.RIGHT -> Frame(if (i == 1) MUSIC_LEFT1 else MUSIC_LEFT2, flip = true)
            }
        }
    }

    fun resolve(context: Context, defaultPath: String): String {
        if (!AppDataStore.isJinmu(context)) return defaultPath
        val name = defaultPath.substringAfterLast('/')
        val nc = "sprites/nc$name"
        return try {
            context.assets.open(nc).close()
            nc
        } catch (_: Exception) {
            defaultPath
        }
    }

    fun load(
        context: Context,
        path: String,
        maxSide: Int = 360,
        flip: Boolean = false,
    ): Bitmap? {
        if (path.startsWith("sticker/")) {
            val kind = path.removePrefix("sticker/")
            return loadStickerStand(context, kind, maxSide, flip)
        }
        val resolved = if (path.startsWith("sprites/") && !path.contains("/nc")) {
            resolve(context, path)
        } else {
            path
        }
        return try {
            val bounds = android.graphics.BitmapFactory.Options().apply { inJustDecodeBounds = true }
            context.assets.open(resolved).use {
                android.graphics.BitmapFactory.decodeStream(it, null, bounds)
            }
            val sample = calcSample(bounds.outWidth, bounds.outHeight, maxSide)
            val opts = android.graphics.BitmapFactory.Options().apply { inSampleSize = sample }
            val bmp = context.assets.open(resolved).use {
                android.graphics.BitmapFactory.decodeStream(it, null, opts)
            } ?: return null
            if (!flip) bmp
            else {
                val m = Matrix().apply { preScale(-1f, 1f) }
                Bitmap.createBitmap(bmp, 0, 0, bmp.width, bmp.height, m, true).also {
                    if (it != bmp) bmp.recycle()
                }
            }
        } catch (_: Exception) {
            null
        }
    }

    /** 对照 `_add_sticker`：站立立绘右上角像素角标。 */
    private fun loadStickerStand(context: Context, kind: String, maxSide: Int, flip: Boolean): Bitmap? {
        val base = load(context, STAND, maxSide, flip) ?: return null
        val out = base.copy(Bitmap.Config.ARGB_8888, true) ?: base
        if (out != base) base.recycle()
        val canvas = Canvas(out)
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.FILL }
        val px = maxOf(3, out.width / 32).toFloat()
        val x = out.width - px * 5
        val y = px * 2
        when (kind) {
            "angry" -> {
                paint.color = Color.parseColor("#FF3333")
                val cx = x + px * 2
                val cy = y + px * 2
                canvas.drawRect(cx - px * 2, cy - px / 2, cx + px * 2, cy + px / 2, paint)
                canvas.drawRect(cx - px / 2, cy - px * 2, cx + px / 2, cy + px * 2, paint)
                for ((ox, oy) in listOf(-2 to -2, 2 to -2, -2 to 2, 2 to 2)) {
                    canvas.drawRect(
                        cx + ox * px, cy + oy * px,
                        cx + ox * px + px, cy + oy * px + px, paint,
                    )
                }
            }
            "question" -> {
                paint.color = Color.parseColor("#FFCC33")
                // ? 形像素块
                canvas.drawRect(x + px, y, x + px * 3, y + px, paint)
                canvas.drawRect(x + px * 2, y + px, x + px * 3, y + px * 2, paint)
                canvas.drawRect(x + px, y + px * 2, x + px * 2, y + px * 3, paint)
                canvas.drawRect(x + px, y + px * 3, x + px * 2, y + px * 4, paint)
            }
            "like" -> {
                paint.color = Color.parseColor("#FF6688")
                for ((ox, oy) in listOf(0f to 0f, px * 3 to px)) {
                    canvas.drawRect(x + ox, y + oy + px, x + ox + px * 2, y + oy + px * 3, paint)
                    canvas.drawRect(x + ox + px, y + oy, x + ox + px * 3, y + oy + px * 2, paint)
                }
            }
        }
        return out
    }

    private fun calcSample(w: Int, h: Int, maxSide: Int): Int {
        var sample = 1
        val side = maxOf(w.coerceAtLeast(1), h.coerceAtLeast(1))
        while (side / sample > maxSide) {
            sample *= 2
        }
        return sample.coerceAtLeast(1)
    }
}
