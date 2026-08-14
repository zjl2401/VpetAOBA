package com.vpet.mobile

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.View
import kotlin.math.min

/** DIY 地图画布：双层 surface/underground、起点/出口、公主笔刷。 */
class RpgDiyCanvas @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : View(context, attrs) {

    var cols = 20
    var rows = 14
    var surface = Array(rows) { IntArray(cols) { RpgMapLoader.GRASS } }
    var underground = Array(rows) { IntArray(cols) { RpgMapLoader.BRICK } }
    var editLayer = "surface" // surface | underground
    var brush = RpgMapLoader.GRASS
    var startX = 2
    var startY = 11
    var goalX = 17
    var goalY = 2
    var goalLayer = "surface"
    var princess = false
    var princessBrush = false
    var placeMode = PlaceMode.TILE

    enum class PlaceMode { TILE, START, GOAL, ERASE }

    private var cell = 24f
    private var ox = 0f
    private var oy = 0f
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)

    val tiles: Array<IntArray>
        get() = if (editLayer == "underground") underground else surface

    fun resetBlank(w: Int = 20, h: Int = 14) {
        cols = w; rows = h
        surface = Array(rows) { IntArray(cols) { RpgMapLoader.GRASS } }
        underground = Array(rows) { IntArray(cols) { RpgMapLoader.BRICK } }
        for (x in 0 until cols) {
            surface[0][x] = RpgMapLoader.ROCK
            surface[rows - 1][x] = RpgMapLoader.ROCK
            underground[0][x] = RpgMapLoader.ROCK
            underground[rows - 1][x] = RpgMapLoader.ROCK
        }
        for (y in 0 until rows) {
            surface[y][0] = RpgMapLoader.ROCK
            surface[y][cols - 1] = RpgMapLoader.ROCK
            underground[y][0] = RpgMapLoader.ROCK
            underground[y][cols - 1] = RpgMapLoader.ROCK
        }
        startX = 2; startY = rows - 3
        goalX = cols - 3; goalY = 2
        goalLayer = "surface"
        princess = false
        editLayer = "surface"
        surface[startY][startX] = RpgMapLoader.GRASS
        surface[goalY][goalX] = RpgMapLoader.GATE
        invalidate()
    }

    fun load(
        w: Int,
        h: Int,
        surf: Array<IntArray>,
        under: Array<IntArray>,
        sx: Int,
        sy: Int,
        gx: Int,
        gy: Int,
        gLayer: String = "surface",
        isPrincess: Boolean = false,
    ) {
        cols = w; rows = h
        surface = Array(h) { y -> IntArray(w) { x -> surf.getOrNull(y)?.getOrNull(x) ?: RpgMapLoader.GRASS } }
        underground = Array(h) { y -> IntArray(w) { x -> under.getOrNull(y)?.getOrNull(x) ?: RpgMapLoader.BRICK } }
        startX = sx.coerceIn(0, w - 1)
        startY = sy.coerceIn(0, h - 1)
        goalX = gx.coerceIn(0, w - 1)
        goalY = gy.coerceIn(0, h - 1)
        goalLayer = if (gLayer == "underground") "underground" else "surface"
        princess = isPrincess
        editLayer = "surface"
        invalidate()
    }

    fun toggleLayer() {
        editLayer = if (editLayer == "surface") "underground" else "surface"
        invalidate()
    }

    fun layerLabel(): String = if (editLayer == "underground") "地下层" else "地面层"

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        cell = min(width / cols.toFloat(), height / rows.toFloat())
        ox = (width - cell * cols) / 2f
        oy = (height - cell * rows) / 2f
        val grid = tiles
        for (y in 0 until rows) {
            for (x in 0 until cols) {
                val l = ox + x * cell
                val t = oy + y * cell
                RpgTileAtlas.draw(
                    context = context,
                    c = canvas,
                    tileId = grid[y][x],
                    l = l,
                    t = t,
                    r = l + cell,
                    b = t + cell,
                    underground = editLayer == "underground",
                    floorPaint = p,
                )
            }
        }
        p.color = Color.parseColor("#4488FF")
        canvas.drawCircle(ox + startX * cell + cell / 2, oy + startY * cell + cell / 2, cell * 0.25f, p)
        if (goalLayer == editLayer || (goalLayer == "surface" && editLayer == "surface")) {
            p.color = Color.parseColor("#44FF88")
            canvas.drawCircle(ox + goalX * cell + cell / 2, oy + goalY * cell + cell / 2, cell * 0.25f, p)
        }
        if (princessBrush) {
            p.color = Color.parseColor("#FF88CC")
            canvas.drawCircle(ox + (cols / 2) * cell + cell / 2, oy + cell / 2, cell * 0.18f, p)
        }
    }

    private fun colorOf(t: Int): Int = when (t) {
        RpgMapLoader.LAND -> Color.parseColor("#6B5A3E")
        RpgMapLoader.WATER -> Color.parseColor("#2A6090")
        RpgMapLoader.BRICK, RpgMapLoader.ROCK, RpgMapLoader.OBSTACLE, RpgMapLoader.MOUNTAIN ->
            Color.parseColor("#4A6078")
        RpgMapLoader.TREE -> Color.parseColor("#1A6030")
        RpgMapLoader.HOUSE -> Color.parseColor("#8B5A2B")
        RpgMapLoader.GATE -> Color.parseColor("#44CC88")
        RpgMapLoader.STAIRS, RpgMapLoader.CAVE -> Color.parseColor("#CCAA66")
        RpgMapLoader.TRAP_SPIKE, RpgMapLoader.TRAP_PIT -> Color.parseColor("#FF4466")
        RpgMapLoader.PICKUP_COIN -> Color.parseColor("#FFDD66")
        RpgMapLoader.TREASURE -> Color.parseColor("#D4A017")
        RpgMapLoader.TREASURE_OPEN -> Color.parseColor("#8B7355")
        RpgMapLoader.GRASS -> if (editLayer == "underground") Color.parseColor("#2A2A32") else Color.parseColor("#2A5030")
        0 -> Color.parseColor("#101820")
        else -> Color.parseColor("#1E2A3A")
    }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        if (event.action != MotionEvent.ACTION_DOWN && event.action != MotionEvent.ACTION_MOVE) return true
        val tx = ((event.x - ox) / cell).toInt()
        val ty = ((event.y - oy) / cell).toInt()
        if (tx !in 0 until cols || ty !in 0 until rows) return true
        val grid = tiles
        when (placeMode) {
            PlaceMode.START -> {
                startX = tx; startY = ty
                if (editLayer == "surface") grid[ty][tx] = RpgMapLoader.GRASS
            }
            PlaceMode.GOAL -> {
                for (y in 0 until rows) for (x in 0 until cols) {
                    if (surface[y][x] == RpgMapLoader.GATE) surface[y][x] = RpgMapLoader.GRASS
                    if (underground[y][x] == RpgMapLoader.GATE) underground[y][x] = RpgMapLoader.BRICK
                }
                goalX = tx; goalY = ty
                goalLayer = editLayer
                grid[ty][tx] = RpgMapLoader.GATE
            }
            PlaceMode.ERASE -> {
                grid[ty][tx] = if (editLayer == "underground") RpgMapLoader.BRICK else RpgMapLoader.GRASS
            }
            PlaceMode.TILE -> {
                val b = if (princessBrush && brush == RpgMapLoader.GRASS) {
                    if (RandomPrincess.next()) RpgMapLoader.TREASURE else RpgMapLoader.LAND
                } else {
                    brush
                }
                grid[ty][tx] = b
            }
        }
        invalidate()
        return true
    }

    private object RandomPrincess {
        private var n = 0
        fun next(): Boolean {
            n++
            return n % 7 == 0
        }
    }
}
