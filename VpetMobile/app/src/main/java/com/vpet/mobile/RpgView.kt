package com.vpet.mobile

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.View
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min
import kotlin.random.Random

/**
 * Silent Oath 战役简版：双层、陷阱、宝箱判定、选角精灵、镜头跟随。
 */
class RpgView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : View(context, attrs) {

    interface Listener {
        fun onHud(hp: Int, coins: Int, treasures: Int, layer: String, msg: String?)
        fun onTreasure(tx: Int, ty: Int)
        fun onLevelClear(coins: Int, treasures: Int, levelIdx: Int)
        fun onDead()
    }

    var listener: Listener? = null

    companion object {
        val PLAYER_KINDS = listOf("knight", "vpet", "allmate")
        fun kindLabel(kind: String) = when (kind) {
            "knight" -> "骑士"
            "vpet" -> "苍叶"
            "allmate" -> "伴侣"
            else -> kind
        }
    }

    private var cols = 11
    private var rows = 15
    private var surface = Array(rows) { IntArray(cols) }
    private var underground = Array(rows) { IntArray(cols) }
    private var layer = "surface"
    private var goalLayer = "underground"
    private var levelIdx = 0
    private var princess = false
    private var playerKind = "knight"

    private var px = 1
    private var py = 1
    private var hp = 100
    private var coins = 0
    private var treasures = 0
    private var cleared = false
    private var chestLocked = false
    private var frameToggle = false
    private var facing = SpriteAssets.Dir.FRONT
    private var stickDx = 0f
    private var stickDy = 0f
    private var stickActive = false
    private var stickCx = 0f
    private var stickCy = 0f
    private var moveAcc = 0f
    private var trapCoolUntil = 0L
    private var camX = 0f
    private var camY = 0f
    private var treasureBmp: Bitmap? = null

    private val floorPaint = Paint()
    private val wallPaint = Paint().apply { color = Color.parseColor("#3A5068") }
    private val coinPaint = Paint().apply { color = Color.parseColor("#FFDD66"); isAntiAlias = true }
    private val chestPaint = Paint().apply { color = Color.parseColor("#D4A017"); isAntiAlias = true }
    private val openChestPaint = Paint().apply { color = Color.parseColor("#8B7355"); isAntiAlias = true }
    private val exitPaint = Paint().apply { color = Color.parseColor("#44CC88") }
    private val trapPaint = Paint().apply { color = Color.parseColor("#FF4466"); isAntiAlias = true }
    private val stairsPaint = Paint().apply { color = Color.parseColor("#CCAA66") }
    private val stickBg = Paint().apply { color = Color.parseColor("#66000000"); isAntiAlias = true }
    private val stickKnob = Paint().apply { color = Color.parseColor("#AA88CCFF"); isAntiAlias = true }

    private var standBmp: Bitmap? = null
    private var front1: Bitmap? = null
    private var front2: Bitmap? = null
    private var back1: Bitmap? = null
    private var back2: Bitmap? = null
    private var left1: Bitmap? = null
    private var left2: Bitmap? = null
    private var right1: Bitmap? = null
    private var right2: Bitmap? = null

    private val tick = object : Runnable {
        override fun run() {
            if (cleared) return
            frameToggle = !frameToggle
            stepMove()
            invalidate()
            postDelayed(this, 100L)
        }
    }

    fun setPlayerKind(kind: String) {
        playerKind = if (kind in PLAYER_KINDS) kind else "knight"
        loadSprites()
        invalidate()
    }

    fun playerKind(): String = playerKind

    fun loadLevel(map: RpgMapLoader.CampaignMap) {
        removeCallbacks(tick)
        cols = map.cols
        rows = map.rows
        surface = map.surface.map { it.clone() }.toTypedArray()
        underground = map.underground.map { it.clone() }.toTypedArray()
        goalLayer = map.goalLayer
        levelIdx = map.levelIdx
        princess = map.princess
        layer = "surface"
        px = map.startX
        py = map.startY
        hp = 100
        coins = 0
        treasures = 0
        cleared = false
        chestLocked = false
        trapCoolUntil = 0L
        treasureBmp = loadBmp("rpg/treasure.png", 48)
        loadSprites()
        post(tick)
        emitHud("出发！${map.name} · ${kindLabel(playerKind)}")
        invalidate()
    }

    /** 宝箱结算：对照 apply_chest_outcome 简版。 */
    fun finishChest(tx: Int, ty: Int, won: Boolean): String {
        chestLocked = false
        val g = grid()
        if (ty !in g.indices || tx !in g[0].indices) return "宝箱消失了"
        if (g[ty][tx] == RpgMapLoader.TREASURE) {
            g[ty][tx] = RpgMapLoader.TREASURE_OPEN
            treasures++
        }
        val msg = if (won) {
            val roll = Random.nextFloat()
            when {
                roll < 0.55f -> {
                    val heal = Random.nextInt(12, 23)
                    hp = (hp + heal).coerceAtMost(100)
                    val coinGain = if (Random.nextFloat() < 0.4f) Random.nextInt(2, 6) else 0
                    if (coinGain > 0) coins += coinGain
                    "判定成功！耐久+$heal" + if (coinGain > 0) " · 金币+$coinGain" else ""
                }
                else -> {
                    val coinGain = Random.nextInt(2, 6)
                    coins += coinGain
                    val heal = Random.nextInt(6, 13)
                    hp = (hp + heal).coerceAtMost(100)
                    "判定成功！金币+$coinGain · 耐久+$heal"
                }
            }
        } else {
            val dmg = Random.nextInt(10, 19)
            hp = (hp - dmg).coerceAtLeast(0)
            "判定失败…耐久-$dmg"
        }
        emitHud(msg)
        checkDead()
        invalidate()
        return msg
    }

    fun cancelChest() {
        chestLocked = false
        emitHud("取消开箱")
    }

    override fun onDetachedFromWindow() {
        removeCallbacks(tick)
        super.onDetachedFromWindow()
    }

    private fun layerLabel() = if (layer == "underground") "地下" else "地面"

    private fun grid(): Array<IntArray> =
        if (layer == "underground") underground else surface

    private fun emitHud(msg: String?) {
        listener?.onHud(hp, coins, treasures, layerLabel(), msg)
    }

    private fun loadBmp(path: String, side: Int = 64): Bitmap? = try {
        context.assets.open(path).use { BitmapFactory.decodeStream(it) }
            ?.let { Bitmap.createScaledBitmap(it, side, side, true) }
    } catch (_: Exception) {
        null
    }

    private fun loadSprites() {
        when (playerKind) {
            "knight" -> {
                standBmp = loadBmp("rpg/knightstand.png") ?: loadBmp("rpg/stand.png")
                front1 = loadBmp("rpg/knightwalk1.png") ?: loadBmp("rpg/walkfront1.png")
                front2 = loadBmp("rpg/knightwalk2.png") ?: loadBmp("rpg/walkfront2.png")
                back1 = loadBmp("rpg/knightwalkback1.png") ?: loadBmp("rpg/walkback1.png")
                back2 = loadBmp("rpg/knightwalkback2.png") ?: loadBmp("rpg/walkback2.png")
                right1 = loadBmp("rpg/knightwalkright1.png")
                right2 = loadBmp("rpg/knightwalkright2.png")
                left1 = right1?.let { flipH(it) } ?: loadBmp("rpg/walkleft1.png")
                left2 = right2?.let { flipH(it) } ?: loadBmp("rpg/walkleft2.png")
            }
            "allmate" -> {
                standBmp = loadBmp("minipet/petstand.png") ?: loadBmp("rpg/stand.png")
                front1 = loadBmp("minipet/petfront1.png") ?: loadBmp("rpg/walkfront1.png")
                front2 = loadBmp("minipet/petfront2.png") ?: loadBmp("rpg/walkfront2.png")
                back1 = loadBmp("minipet/petback1.png") ?: loadBmp("rpg/walkback1.png")
                back2 = loadBmp("minipet/petback2.png") ?: loadBmp("rpg/walkback2.png")
                left1 = loadBmp("minipet/petleft1.png") ?: loadBmp("rpg/walkleft1.png")
                left2 = loadBmp("minipet/petleft2.png") ?: loadBmp("rpg/walkleft2.png")
                right1 = left1?.let { flipH(it) }
                right2 = left2?.let { flipH(it) }
            }
            else -> { // vpet
                standBmp = loadBmp("rpg/stand.png")
                front1 = loadBmp("rpg/walkfront1.png")
                front2 = loadBmp("rpg/walkfront2.png")
                back1 = loadBmp("rpg/walkback1.png")
                back2 = loadBmp("rpg/walkback2.png")
                left1 = loadBmp("rpg/walkleft1.png")
                left2 = loadBmp("rpg/walkleft2.png")
                right1 = left1?.let { flipH(it) }
                right2 = left2?.let { flipH(it) }
            }
        }
    }

    private fun flipH(src: Bitmap): Bitmap {
        val m = android.graphics.Matrix().apply { preScale(-1f, 1f) }
        return Bitmap.createBitmap(src, 0, 0, src.width, src.height, m, true)
    }

    private fun stepMove() {
        if (!stickActive || cleared || chestLocked) return
        val len = hypot(stickDx.toDouble(), stickDy.toDouble()).toFloat()
        if (len < 18f) return
        moveAcc += len / 36f
        if (moveAcc < 1f) return
        moveAcc = 0f
        val dir = when {
            kotlin.math.abs(stickDx) >= kotlin.math.abs(stickDy) ->
                if (stickDx < 0) SpriteAssets.Dir.LEFT else SpriteAssets.Dir.RIGHT
            else ->
                if (stickDy < 0) SpriteAssets.Dir.BACK else SpriteAssets.Dir.FRONT
        }
        facing = dir
        val nx = (px + dir.dx).coerceIn(0, cols - 1)
        val ny = (py + dir.dy).coerceIn(0, rows - 1)
        val cell = grid()[ny][nx]
        when {
            cell in RpgMapLoader.WALLS || cell == RpgMapLoader.TREE -> {
                hp = (hp - 1).coerceAtLeast(0)
                emitHud("撞墙 -1")
                checkDead()
            }
            else -> {
                px = nx; py = ny
                onEnterCell(cell, nx, ny)
            }
        }
    }

    private fun onEnterCell(cell: Int, x: Int, y: Int) {
        val g = grid()
        when (cell) {
            RpgMapLoader.PICKUP_COIN -> {
                g[y][x] = if (layer == "underground") RpgMapLoader.BRICK else RpgMapLoader.GRASS
                coins++
                if (coins % 10 == 0) {
                    hp = (hp + 15).coerceAtMost(100)
                    emitHud("金币回血 +15")
                } else {
                    emitHud("金币 +1")
                }
            }
            RpgMapLoader.TREASURE -> {
                chestLocked = true
                stickActive = false
                stickDx = 0f; stickDy = 0f
                listener?.onTreasure(x, y)
                emitHud("发现宝箱！")
            }
            RpgMapLoader.TREASURE_OPEN -> emitHud("空宝箱……什么都不剩了")
            RpgMapLoader.TRAP_SPIKE, RpgMapLoader.TRAP_PIT -> {
                val now = android.os.SystemClock.elapsedRealtime()
                if (now >= trapCoolUntil) {
                    trapCoolUntil = now + 800L
                    val dmg = if (cell == RpgMapLoader.TRAP_SPIKE) 12 else 18
                    hp = (hp - dmg).coerceAtLeast(0)
                    emitHud("陷阱 -$dmg")
                    checkDead()
                }
            }
            RpgMapLoader.STAIRS, RpgMapLoader.CAVE -> {
                layer = if (layer == "surface") "underground" else "surface"
                emitHud("切换至${layerLabel()}")
            }
            RpgMapLoader.GATE -> {
                if (layer == goalLayer || goalLayer == "surface") {
                    cleared = true
                    removeCallbacks(tick)
                    listener?.onLevelClear(coins, treasures, levelIdx)
                } else {
                    emitHud("关卡门在${if (goalLayer == "underground") "地下" else "地面"}")
                }
            }
            else -> emitHud(null)
        }
    }

    private fun checkDead() {
        if (hp <= 0) {
            cleared = true
            removeCallbacks(tick)
            listener?.onDead()
        }
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        if (width == 0 || height == 0) return
        val viewH = height * 0.72f
        val cell = min(width / 14f, viewH / 10f)
        val targetCamX = px * cell - width / 2f + cell / 2
        val targetCamY = py * cell - viewH / 2f + cell / 2
        camX += (targetCamX - camX) * 0.25f
        camY += (targetCamY - camY) * 0.25f
        val maxCamX = max(0f, cols * cell - width)
        val maxCamY = max(0f, rows * cell - viewH)
        camX = camX.coerceIn(0f, maxCamX)
        camY = camY.coerceIn(0f, maxCamY)

        val oy = height * 0.06f
        val g = grid()
        val x0 = max(0, (camX / cell).toInt() - 1)
        val y0 = max(0, (camY / cell).toInt() - 1)
        val x1 = min(cols - 1, ((camX + width) / cell).toInt() + 1)
        val y1 = min(rows - 1, ((camY + viewH) / cell).toInt() + 1)
        for (y in y0..y1) {
            for (x in x0..x1) {
                val l = x * cell - camX
                val t = oy + y * cell - camY
                drawTile(canvas, g[y][x], l, t, l + cell, t + cell)
            }
        }
        val pl = px * cell - camX
        val pt = oy + py * cell - camY
        val bmp = currentSprite()
        if (bmp != null) {
            canvas.drawBitmap(bmp, null, RectF(pl, pt, pl + cell, pt + cell), null)
        } else {
            canvas.drawCircle(pl + cell / 2, pt + cell / 2, cell * 0.35f, stickKnob)
        }

        val scx = width * 0.22f
        val scy = height * 0.88f
        val sr = width * 0.12f
        canvas.drawCircle(scx, scy, sr, stickBg)
        val kx = if (stickActive) (scx + stickDx.coerceIn(-sr, sr)) else scx
        val ky = if (stickActive) (scy + stickDy.coerceIn(-sr, sr)) else scy
        canvas.drawCircle(kx, ky, sr * 0.4f, stickKnob)
        stickCx = scx
        stickCy = scy
    }

    private fun drawTile(c: Canvas, t: Int, l: Float, t0: Float, r: Float, b: Float) {
        floorPaint.color = when (t) {
            RpgMapLoader.LAND -> Color.parseColor("#6B5A3E")
            RpgMapLoader.WATER -> Color.parseColor("#2A6090")
            RpgMapLoader.BRICK -> Color.parseColor("#5A4A4A")
            RpgMapLoader.GRASS -> if (layer == "underground") Color.parseColor("#2A2A32") else Color.parseColor("#2A5030")
            else -> if (layer == "underground") Color.parseColor("#1E1E28") else Color.parseColor("#1E2A3A")
        }
        c.drawRect(l, t0, r, b, floorPaint)
        when (t) {
            in RpgMapLoader.WALLS, RpgMapLoader.TREE -> {
                wallPaint.color = when (t) {
                    RpgMapLoader.WATER -> Color.parseColor("#2266AA")
                    RpgMapLoader.TREE -> Color.parseColor("#1A6030")
                    RpgMapLoader.HOUSE -> Color.parseColor("#8B5A2B")
                    else -> Color.parseColor("#4A6078")
                }
                c.drawRect(l + 1, t0 + 1, r - 1, b - 1, wallPaint)
            }
            RpgMapLoader.PICKUP_COIN ->
                c.drawCircle((l + r) / 2, (t0 + b) / 2, (r - l) * 0.18f, coinPaint)
            RpgMapLoader.TREASURE -> {
                val bmp = treasureBmp
                if (bmp != null) {
                    c.drawBitmap(bmp, null, RectF(l + 2, t0 + 2, r - 2, b - 2), null)
                } else {
                    c.drawRoundRect(RectF(l + 4, t0 + 6, r - 4, b - 4), 4f, 4f, chestPaint)
                }
            }
            RpgMapLoader.TREASURE_OPEN ->
                c.drawRoundRect(RectF(l + 4, t0 + 8, r - 4, b - 4), 4f, 4f, openChestPaint)
            RpgMapLoader.GATE ->
                c.drawRoundRect(RectF(l + 3, t0 + 3, r - 3, b - 3), 6f, 6f, exitPaint)
            RpgMapLoader.STAIRS, RpgMapLoader.CAVE ->
                c.drawRoundRect(RectF(l + 4, t0 + 4, r - 4, b - 4), 4f, 4f, stairsPaint)
            in RpgMapLoader.TRAPS ->
                c.drawCircle((l + r) / 2, (t0 + b) / 2, (r - l) * 0.2f, trapPaint)
        }
    }

    private fun currentSprite(): Bitmap? {
        if (!stickActive || hypot(stickDx.toDouble(), stickDy.toDouble()) < 18) {
            return standBmp ?: front1
        }
        val a = if (frameToggle) 1 else 2
        return when (facing) {
            SpriteAssets.Dir.FRONT -> if (a == 1) front1 else front2
            SpriteAssets.Dir.BACK -> if (a == 1) back1 else back2
            SpriteAssets.Dir.LEFT -> if (a == 1) left1 else left2
            SpriteAssets.Dir.RIGHT -> if (a == 1) right1 else right2
        } ?: standBmp
    }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        if (cleared || chestLocked) return true
        val scx = stickCx
        val scy = stickCy
        val sr = width * 0.12f
        when (event.actionMasked) {
            MotionEvent.ACTION_DOWN, MotionEvent.ACTION_MOVE -> {
                val dx = event.x - scx
                val dy = event.y - scy
                if (hypot(dx.toDouble(), dy.toDouble()) <= sr * 1.6f || stickActive) {
                    stickActive = true
                    stickDx = dx.coerceIn(-sr, sr)
                    stickDy = dy.coerceIn(-sr, sr)
                }
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                stickActive = false
                stickDx = 0f
                stickDy = 0f
            }
        }
        return true
    }
}
