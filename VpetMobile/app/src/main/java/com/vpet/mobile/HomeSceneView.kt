package com.vpet.mobile

import android.content.Context
import android.graphics.Bitmap
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
        /** 对照桌面 OUTDOOR_BASE_COLOR */
        val OUTDOOR_BASE = Color.parseColor("#000000")
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
    /** 地图编辑：点格子放置 [editBrush]（null=擦除）。 */
    var editMode = false
    var editBrush: String? = null
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
    private val tilePaint = Paint().apply {
        isFilterBitmap = false
        isAntiAlias = false
    }
    private val labelPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#E8F0FF")
        textAlign = Paint.Align.CENTER
        textSize = 11f
    }

    private lateinit var indoor: Array<Array<String?>>
    private lateinit var outdoor: Array<Array<String?>>

    init {
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

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        tile = min(width / cols.toFloat(), height / rows.toFloat())
        ox = (width - tile * cols) / 2f
        oy = (height - tile * rows) / 2f
        val tilePx = tile.toInt().coerceAtLeast(12)
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
                drawCell(canvas, cell, l, t, r, b, tilePx)
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

    private fun drawCell(c: Canvas, kind: String, l: Float, t: Float, r: Float, b: Float, tilePx: Int) {
        // 室外叠放地物：先铺草地（对照桌面 g+k）
        val propKinds = setOf(
            "tree", "flower", "fence", "bush", "plant",
            "gift", "gift_art", "house", "home", "cabin", "door",
            "user_paint", "paint", "art",
        )
        if (zone == Zone.OUTDOOR && kind in propKinds) {
            HomeTileAssets.bitmap(context, "grass", tilePx)?.let {
                c.drawBitmap(it, null, RectF(l, t, r, b), tilePaint)
            }
        }
        val bmp = HomeTileAssets.bitmap(context, kind, tilePx)
        if (bmp != null) {
            c.drawBitmap(bmp, null, RectF(l, t, r, b), tilePaint)
            return
        }
        furnPaint.color = FURN
        c.drawRect(l + 4, t + 4, r - 4, b - 4, furnPaint)
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

    fun tilePx(): Int = tile.toInt().coerceAtLeast(12)

    fun setCellKind(x: Int, y: Int, kind: String?) {
        if (y !in 0 until rows || x !in 0 until cols) return
        val map = if (zone == Zone.INDOOR) indoor else outdoor
        map[y][x] = kind
        invalidate()
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
        if (editMode) {
            setCellKind(tx, ty, editBrush)
            return true
        }
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
