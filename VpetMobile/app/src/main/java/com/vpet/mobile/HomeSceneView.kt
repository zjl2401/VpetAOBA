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
import kotlin.math.min
import org.json.JSONObject

/**
 * 家园棋盘：从 [HomeLayoutStore] layout 加载/回写 zone 与宠坐标。
 */
class HomeSceneView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : View(context, attrs) {

    companion object {
        val FLOOR_A = Color.parseColor("#6A7080")
        val FLOOR_B = Color.parseColor("#5A6070")
        val FURN = Color.parseColor("#6AA8D8")
        val OUTDOOR_BASE = Color.parseColor("#1A3020")
    }

    enum class Zone { INDOOR, OUTDOOR }

    interface Listener {
        fun onPetCell(cx: Int, cy: Int)
        fun onDoorUsed()
        fun onTapPet()
        /** 经营模式：点目标格（已由 activity 处理走位后也可直接回调）。 */
        fun onFarmTap(cx: Int, cy: Int)
        /** 室内点花瓶等家具交互。 */
        fun onIndoorTap(cx: Int, cy: Int) {}
    }

    var listener: Listener? = null
    var farmMode = false
    var farmGrid: Array<Array<org.json.JSONObject?>>? = null
    var zone = Zone.INDOOR
        private set
    var cols = HomeLayoutStore.COLS_DEFAULT
        private set
    var rows = HomeLayoutStore.ROWS_DEFAULT
        private set
    var petX = 6
    var petY = 5
    private var indoorPetX = 6
    private var indoorPetY = 5
    private var outdoorPetX = 5
    private var outdoorPetY = 4
    private var tile = 32f
    private var ox = 0f
    private var oy = 0f
    private var floorA = FLOOR_A
    private var floorB = FLOOR_B

    private val floorPaint = Paint()
    private val furnPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = FURN }
    private val labelPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#E8F0FF")
        textAlign = Paint.Align.CENTER
        textSize = 11f
    }

    private var bmpGrass: Bitmap? = null
    private var bmpLand: Bitmap? = null
    private var bmpWater: Bitmap? = null
    private var bmpTree: Bitmap? = null
    private var bmpRock: Bitmap? = null
    private var bmpBrick: Bitmap? = null

    private lateinit var indoor: Array<Array<String?>>
    private lateinit var outdoor: Array<Array<String?>>

    init {
        loadTiles()
        applyLayout(HomeLayoutStore.defaultLayout())
    }

    fun maxRoomsHint(days: Int): String {
        val rooms = when {
            days >= 45 -> 4
            days >= 21 -> 3
            days >= 7 -> 2
            else -> 1
        }
        return "相伴第 ${days} 天 · 可开 $rooms 间房"
    }

    fun cellKindAt(x: Int, y: Int): String? {
        if (y !in 0 until rows || x !in 0 until cols) return null
        val map = if (zone == Zone.INDOOR) indoor else outdoor
        val c = map[y][x] ?: return null
        if (c == "@" || c.startsWith("@")) return null
        return c
    }

    fun setOutdoorKind(x: Int, y: Int, kind: String?) {
        if (y !in 0 until rows || x !in 0 until cols) return
        outdoor[y][x] = kind
        invalidate()
    }

    fun outdoorTileOps(): HomeFarmEngine.TileOps = object : HomeFarmEngine.TileOps {
        override fun kind(x: Int, y: Int): String? {
            if (y !in 0 until rows || x !in 0 until cols) return null
            val c = outdoor[y][x] ?: return null
            if (c == "@" || c.startsWith("@")) return null
            return c
        }

        override fun place(kind: String, x: Int, y: Int) {
            if (y in 0 until rows && x in 0 until cols) {
                outdoor[y][x] = kind
                invalidate()
            }
        }

        override fun clearToGrass(x: Int, y: Int) {
            place("grass", x, y)
        }
    }

    fun indoorTileOps(): HomeFarmEngine.TileOps = object : HomeFarmEngine.TileOps {
        override fun kind(x: Int, y: Int): String? {
            if (y !in 0 until rows || x !in 0 until cols) return null
            val c = indoor[y][x] ?: return null
            if (c == "@" || c.startsWith("@")) return null
            return c
        }

        override fun place(kind: String, x: Int, y: Int) {
            if (y in 0 until rows && x in 0 until cols) {
                indoor[y][x] = kind
                invalidate()
            }
        }

        override fun clearToGrass(x: Int, y: Int) {
            // 室内无草地，清空为 null
            if (y in 0 until rows && x in 0 until cols) {
                indoor[y][x] = null
                invalidate()
            }
        }
    }

    fun applyLayout(layout: JSONObject) {
        cols = layout.optInt("cols", HomeLayoutStore.COLS_DEFAULT).coerceIn(6, 24)
        rows = layout.optInt("rows", HomeLayoutStore.ROWS_DEFAULT).coerceIn(6, 20)
        floorA = parseColor(layout.optString("floor_a"), FLOOR_A)
        floorB = parseColor(layout.optString("floor_b"), FLOOR_B)
        indoor = HomeLayoutStore.tilesToKindGrid(layout.optJSONArray("indoor_tiles"), cols, rows)
        outdoor = HomeLayoutStore.tilesToKindGrid(layout.optJSONArray("outdoor_tiles"), cols, rows)
        val ip = layout.optJSONArray("indoor_pet")
        indoorPetX = (ip?.optInt(0, 6) ?: 6).coerceIn(0, cols - 1)
        indoorPetY = (ip?.optInt(1, 5) ?: 5).coerceIn(0, rows - 1)
        val op = layout.optJSONArray("outdoor_pet")
        outdoorPetX = (op?.optInt(0, 5) ?: 5).coerceIn(0, cols - 1)
        outdoorPetY = (op?.optInt(1, 4) ?: 4).coerceIn(0, rows - 1)
        zone = if (layout.optString("zone") == "outdoor") Zone.OUTDOOR else Zone.INDOOR
        if (zone == Zone.INDOOR) {
            petX = indoorPetX; petY = indoorPetY
        } else {
            petX = outdoorPetX; petY = outdoorPetY
        }
        invalidate()
    }

    /** 把当前场景写回 layout（保留 farm 等原字段）。 */
    fun writeInto(layout: JSONObject) {
        rememberPet()
        layout.put("cols", cols)
        layout.put("rows", rows)
        layout.put("zone", if (zone == Zone.OUTDOOR) "outdoor" else "indoor")
        layout.put("indoor_tiles", HomeLayoutStore.kindGridToTiles(indoor))
        layout.put("outdoor_tiles", HomeLayoutStore.kindGridToTiles(outdoor))
        layout.put("indoor_pet", org.json.JSONArray().put(indoorPetX).put(indoorPetY))
        layout.put("outdoor_pet", org.json.JSONArray().put(outdoorPetX).put(outdoorPetY))
        // 同步活动房间宠坐标
        val rooms = layout.optJSONArray("rooms")
        if (rooms != null && rooms.length() > 0) {
            val active = layout.optInt("active_room", 0).coerceIn(0, rooms.length() - 1)
            val room = rooms.optJSONObject(active)
            room?.put("pet", org.json.JSONArray().put(indoorPetX).put(indoorPetY))
            room?.put("tiles", HomeLayoutStore.kindGridToTiles(indoor))
        }
    }

    fun setZone(z: Zone) {
        rememberPet()
        zone = z
        if (z == Zone.INDOOR) {
            petX = indoorPetX; petY = indoorPetY
        } else {
            petX = outdoorPetX; petY = outdoorPetY
        }
        invalidate()
    }

    fun toggleZone() {
        setZone(if (zone == Zone.INDOOR) Zone.OUTDOOR else Zone.INDOOR)
        listener?.onDoorUsed()
    }

    private fun rememberPet() {
        if (zone == Zone.INDOOR) {
            indoorPetX = petX; indoorPetY = petY
        } else {
            outdoorPetX = petX; outdoorPetY = petY
        }
    }

    private fun parseColor(hex: String, fallback: Int): Int = try {
        Color.parseColor(if (hex.startsWith("#")) hex else "#$hex")
    } catch (_: Exception) {
        fallback
    }

    private fun loadTiles() {
        fun load(name: String): Bitmap? = try {
            context.assets.open("home/$name").use { BitmapFactory.decodeStream(it) }
        } catch (_: Exception) {
            null
        }
        bmpGrass = load("grass.png")
        bmpLand = load("land.png")
        bmpWater = load("water.png")
        bmpTree = load("tree.png")
        bmpRock = load("rock.png")
        bmpBrick = load("brick.png")
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        tile = min(width / cols.toFloat(), height / rows.toFloat())
        ox = (width - tile * cols) / 2f
        oy = (height - tile * rows) / 2f
        val map = if (zone == Zone.INDOOR) indoor else outdoor
        for (y in 0 until rows) {
            for (x in 0 until cols) {
                val l = ox + x * tile
                val t = oy + y * tile
                val r = l + tile
                val b = t + tile
                if (zone == Zone.INDOOR) {
                    floorPaint.color = if ((x + y) % 2 == 0) floorA else floorB
                    canvas.drawRect(l, t, r, b, floorPaint)
                } else {
                    floorPaint.color = OUTDOOR_BASE
                    canvas.drawRect(l, t, r, b, floorPaint)
                }
                val cell = map[y][x] ?: continue
                if (cell == "@" || cell.startsWith("@")) continue
                drawCell(canvas, cell, l, t, r, b)
                // 经营作物叠层（仅室外）
                if (zone == Zone.OUTDOOR) {
                    val plot = farmGrid?.getOrNull(y)?.getOrNull(x)
                    if (plot != null) drawCrop(canvas, plot, l, t, r, b)
                }
            }
        }
        val pl = ox + petX * tile
        val pt = oy + petY * tile
        floorPaint.color = Color.parseColor("#44FF88AA")
        canvas.drawRoundRect(RectF(pl + 4, pt + 4, pl + tile - 4, pt + tile - 4), 8f, 8f, floorPaint)
    }

    private fun drawCrop(c: Canvas, plot: org.json.JSONObject, l: Float, t: Float, r: Float, b: Float) {
        val col = try {
            Color.parseColor(HomeFarmEngine.plotColor(plot))
        } catch (_: Exception) {
            Color.parseColor("#88AA44")
        }
        furnPaint.color = col
        val cx = (l + r) / 2
        val cy = (t + b) / 2
        c.drawCircle(cx, cy, tile * 0.22f, furnPaint)
        val prog = HomeFarmEngine.plotProgress(plot)
        floorPaint.color = Color.parseColor("#44000000")
        c.drawRect(l + 4, b - 8, r - 4, b - 3, floorPaint)
        floorPaint.color = if (HomeFarmEngine.plotBoostActive(plot)) {
            Color.parseColor("#44AAFF")
        } else {
            Color.parseColor("#88FF88")
        }
        c.drawRect(l + 4, b - 8, l + 4 + (r - l - 8) * prog, b - 3, floorPaint)
        if (HomeFarmEngine.plotReady(plot)) {
            labelPaint.textSize = tile * 0.28f
            c.drawText("★", cx, cy + 4, labelPaint)
        }
    }

    private fun drawCell(c: Canvas, kind: String, l: Float, t: Float, r: Float, b: Float) {
        val bmp = when (kind) {
            "grass" -> bmpGrass
            "land" -> bmpLand
            "water" -> bmpWater
            "tree" -> bmpTree
            "rock" -> bmpRock
            "brick", "path" -> bmpBrick
            else -> null
        }
        if (bmp != null) {
            c.drawBitmap(bmp, null, RectF(l, t, r, b), null)
            if (kind in setOf("grass", "land", "water", "brick", "path", "rock")) return
        }
        when (kind) {
            "door" -> {
                furnPaint.color = Color.parseColor("#8B5A2B")
                c.drawRect(l + 6, t + 2, r - 6, b - 2, furnPaint)
                labelPaint.textSize = tile * 0.28f
                c.drawText("门", (l + r) / 2, (t + b) / 2 + 4, labelPaint)
            }
            "bed" -> {
                furnPaint.color = FURN
                c.drawRoundRect(RectF(l + 2, t + 4, r - 2, b - 4), 4f, 4f, furnPaint)
                c.drawText("床", (l + r) / 2, (t + b) / 2 + 4, labelPaint)
            }
            "table" -> {
                furnPaint.color = FURN
                c.drawRect(l + 4, t + 4, r - 4, b - 4, furnPaint)
            }
            "chair" -> {
                furnPaint.color = Color.parseColor("#88B8E8")
                c.drawRect(l + 8, t + 8, r - 8, b - 8, furnPaint)
            }
            "carpet" -> {
                furnPaint.color = Color.parseColor("#AA6688")
                c.drawRect(l, t, r, b, furnPaint)
            }
            "plant", "flower", "bush" -> {
                furnPaint.color = Color.parseColor("#44AA66")
                c.drawCircle((l + r) / 2, (t + b) / 2, tile * 0.28f, furnPaint)
                if (kind == "flower") {
                    furnPaint.color = Color.parseColor("#FF7799")
                    c.drawCircle((l + r) / 2, (t + b) / 2 - tile * 0.08f, tile * 0.12f, furnPaint)
                }
            }
            "vase", "vase_filled" -> {
                furnPaint.color = Color.parseColor("#88AACC")
                c.drawRoundRect(RectF(l + 10, t + tile * 0.35f, r - 10, b - 4), 4f, 4f, furnPaint)
                if (kind == "vase_filled") {
                    furnPaint.color = Color.parseColor("#FF88AA")
                    c.drawCircle((l + r) / 2, t + tile * 0.28f, tile * 0.16f, furnPaint)
                    furnPaint.color = Color.parseColor("#FFEE88")
                    c.drawCircle((l + r) / 2, t + tile * 0.28f, tile * 0.06f, furnPaint)
                } else {
                    labelPaint.textSize = tile * 0.22f
                    c.drawText("瓶", (l + r) / 2, (t + b) / 2 + 6, labelPaint)
                }
            }
            "lamp" -> {
                furnPaint.color = Color.parseColor("#FFEE88")
                c.drawCircle((l + r) / 2, t + tile * 0.35f, tile * 0.18f, furnPaint)
            }
            "window" -> {
                furnPaint.color = Color.parseColor("#88CCFF")
                c.drawRect(l + 2, t + 6, r - 2, b - 6, furnPaint)
            }
            "fence" -> {
                furnPaint.color = Color.parseColor("#8B6A3A")
                c.drawRect(l + 2, t + 4, r - 2, b - 4, furnPaint)
            }
            "tree" -> {
                if (bmpTree != null) c.drawBitmap(bmpTree!!, null, RectF(l, t, r, b), null)
                else {
                    furnPaint.color = Color.parseColor("#2A6A38")
                    c.drawCircle((l + r) / 2, (t + b) / 2, tile * 0.35f, furnPaint)
                }
            }
            else -> Unit
        }
    }

    fun petPixelCenter(): Pair<Float, Float> {
        val cx = ox + petX * tile + tile / 2
        val cy = oy + petY * tile + tile / 2
        return cx to cy
    }

    fun petPixelTopLeft(petSizePx: Int): Pair<Float, Float> {
        val (cx, cy) = petPixelCenter()
        return cx - petSizePx / 2f to cy - petSizePx / 2f
    }

    fun tryMove(dx: Int, dy: Int): Boolean {
        val nx = (petX + dx).coerceIn(0, cols - 1)
        val ny = (petY + dy).coerceIn(0, rows - 1)
        if (nx == petX && ny == petY) return false
        val map = if (zone == Zone.INDOOR) indoor else outdoor
        val cell = map[ny][nx]
        if (cell == "door") {
            petX = nx; petY = ny
            rememberPet()
            invalidate()
            toggleZone()
            return true
        }
        if (cell in setOf("tree", "fence", "water", "rock", "shelf")) return false
        petX = nx
        petY = ny
        rememberPet()
        listener?.onPetCell(petX, petY)
        invalidate()
        return true
    }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        if (event.action != MotionEvent.ACTION_DOWN) return true
        val tx = ((event.x - ox) / tile).toInt()
        val ty = ((event.y - oy) / tile).toInt()
        if (tx !in 0 until cols || ty !in 0 until rows) return true
        if (tx == petX && ty == petY) {
            listener?.onTapPet()
            return true
        }
        if (farmMode && zone == Zone.OUTDOOR) {
            listener?.onFarmTap(tx, ty)
            return true
        }
        val map = if (zone == Zone.INDOOR) indoor else outdoor
        val cellKind = map[ty][tx]
        if (zone == Zone.INDOOR && (cellKind == "vase" || cellKind == "vase_filled")) {
            listener?.onIndoorTap(tx, ty)
            return true
        }
        if (cellKind == "door") {
            toggleZone()
            return true
        }
        val dx = (tx - petX).coerceIn(-1, 1)
        val dy = (ty - petY).coerceIn(-1, 1)
        if (dx != 0 || dy != 0) tryMove(dx, dy)
        return true
    }
}
