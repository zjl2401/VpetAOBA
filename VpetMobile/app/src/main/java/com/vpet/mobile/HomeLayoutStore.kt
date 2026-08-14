package com.vpet.mobile

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/**
 * 家园 layout：对照 `home_cottage.load_layout` / `save_layout`（互导最小集）。
 * 经营字段（farm 等）原样保留；手机侧不玩经营玩法。
 */
object HomeLayoutStore {
    private const val PREF = "vpet_home"
    private const val KEY_JSON = "home_layout_json"
    const val COLS_DEFAULT = 12
    const val ROWS_DEFAULT = 10
    const val FLOOR_A = "#6A7080"
    const val FLOOR_B = "#5A6070"
    const val FURN = "#6AA8D8"

    private fun prefs(ctx: Context) = ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE)

    fun load(ctx: Context): JSONObject {
        val raw = prefs(ctx).getString(KEY_JSON, null)
        if (!raw.isNullOrBlank()) {
            try {
                return normalize(JSONObject(raw))
            } catch (_: Exception) {
            }
        }
        return defaultLayout().also { save(ctx, it) }
    }

    fun save(ctx: Context, layout: JSONObject) {
        prefs(ctx).edit().putString(KEY_JSON, normalize(layout).toString()).apply()
    }

    fun reset(ctx: Context): JSONObject = defaultLayout().also { save(ctx, it) }

    fun exportJson(ctx: Context): String = normalize(load(ctx)).toString(2)

    fun importJson(ctx: Context, text: String): JSONObject {
        val o = normalize(JSONObject(text))
        save(ctx, o)
        return o
    }

    fun defaultLayout(): JSONObject {
        val indoor = defaultIndoorTiles()
        val outdoor = defaultOutdoorTiles()
        val roomTiles = JSONArray()
        for (y in 0 until ROWS_DEFAULT) {
            val row = JSONArray()
            for (x in 0 until COLS_DEFAULT) row.put(indoor.getJSONArray(y).opt(x))
            roomTiles.put(row)
        }
        val farm = JSONArray()
        for (y in 0 until ROWS_DEFAULT) {
            val row = JSONArray()
            for (x in 0 until COLS_DEFAULT) row.put(JSONObject.NULL)
            farm.put(row)
        }
        return JSONObject()
            .put("cols", COLS_DEFAULT)
            .put("rows", ROWS_DEFAULT)
            .put("zone", "indoor")
            .put("move_mode", "free")
            .put("floor_a", FLOOR_A)
            .put("floor_b", FLOOR_B)
            .put("furn_color", FURN)
            .put("bg_colors", JSONObject())
            .put("indoor_tiles", indoor)
            .put("outdoor_tiles", outdoor)
            .put("indoor_pet", JSONArray().put(6).put(5))
            .put("outdoor_pet", JSONArray().put(5).put(4))
            .put("on_desktop", false)
            .put("desktop_x", -1)
            .put("desktop_y", -1)
            .put("house_name", "")
            .put("farm", farm)
            .put("crafted_furniture", JSONArray())
            .put("till_hits", JSONObject())
            .put("chop_jobs", JSONObject())
            .put("tree_regrow", JSONArray())
            .put(
                "rooms",
                JSONArray().put(
                    JSONObject()
                        .put("name", "主屋")
                        .put("tiles", roomTiles)
                        .put("pet", JSONArray().put(6).put(5)),
                ),
            )
            .put("active_room", 0)
    }

    fun normalize(raw: JSONObject): JSONObject {
        val base = defaultLayout()
        val cols = raw.optInt("cols", COLS_DEFAULT).coerceIn(6, 24)
        val rows = raw.optInt("rows", ROWS_DEFAULT).coerceIn(6, 20)
        val zone = raw.optString("zone", "indoor").let {
            if (it == "outdoor") "outdoor" else "indoor"
        }
        val indoor = copyGrid(raw.optJSONArray("indoor_tiles") ?: raw.optJSONArray("tiles"), cols, rows, indoorDefault = true)
        val outdoor = copyGrid(raw.optJSONArray("outdoor_tiles"), cols, rows, indoorDefault = false)
        val out = JSONObject(base.toString())
        out.put("cols", cols)
        out.put("rows", rows)
        out.put("zone", zone)
        out.put("move_mode", if (raw.optString("move_mode") == "control") "control" else "free")
        out.put("floor_a", raw.optString("floor_a", FLOOR_A))
        out.put("floor_b", raw.optString("floor_b", FLOOR_B))
        out.put("furn_color", raw.optString("furn_color", FURN))
        if (raw.has("bg_colors")) out.put("bg_colors", raw.opt("bg_colors"))
        out.put("indoor_tiles", indoor)
        out.put("outdoor_tiles", outdoor)
        out.put("indoor_pet", petPair(raw.optJSONArray("indoor_pet"), 6, 5, cols, rows))
        out.put("outdoor_pet", petPair(raw.optJSONArray("outdoor_pet"), 5, 4, cols, rows))
        if (raw.has("pet_x") && raw.has("pet_y")) {
            val px = raw.optInt("pet_x").coerceIn(0, cols - 1)
            val py = raw.optInt("pet_y").coerceIn(0, rows - 1)
            if (zone == "outdoor") out.put("outdoor_pet", JSONArray().put(px).put(py))
            else out.put("indoor_pet", JSONArray().put(px).put(py))
        }
        out.put("house_name", raw.optString("house_name", "").take(16))
        out.put("on_desktop", raw.optBoolean("on_desktop", false))
        out.put("desktop_x", raw.optInt("desktop_x", -1))
        out.put("desktop_y", raw.optInt("desktop_y", -1))
        // 经营字段透传（可空壳，但不得丢）
        if (raw.has("farm")) out.put("farm", raw.opt("farm"))
        if (raw.has("crafted_furniture")) out.put("crafted_furniture", raw.opt("crafted_furniture"))
        if (raw.has("till_hits")) out.put("till_hits", raw.opt("till_hits"))
        if (raw.has("chop_jobs")) out.put("chop_jobs", raw.opt("chop_jobs"))
        if (raw.has("tree_regrow")) out.put("tree_regrow", raw.opt("tree_regrow"))
        if (raw.has("rooms")) out.put("rooms", raw.opt("rooms"))
        out.put("active_room", raw.optInt("active_room", 0))
        ensureIndoorVase(indoor, cols, rows)
        ensureOutdoorDecor(outdoor, cols, rows)
        out.put("indoor_tiles", indoor)
        out.put("outdoor_tiles", outdoor)
        return out
    }

    /** 旧存档补小屋/礼物像素格（不覆盖已有）。 */
    private fun ensureOutdoorDecor(outdoor: JSONArray, cols: Int, rows: Int) {
        fun hasKind(kind: String): Boolean {
            for (y in 0 until outdoor.length()) {
                val row = outdoor.optJSONArray(y) ?: continue
                for (x in 0 until row.length()) {
                    if (cellKind(row.opt(x)) == kind) return true
                }
            }
            return false
        }
        fun putStack(kind: String, x: Int, y: Int) {
            if (y !in 0 until outdoor.length()) return
            val row = outdoor.getJSONArray(y)
            if (x !in 0 until row.length()) return
            val cur = row.opt(x)
            if (cur != null && cur != JSONObject.NULL && cellKind(cur) !in setOf("grass", "land", "path")) return
            row.put(x, JSONObject().put("g", "grass").put("k", kind))
        }
        if (!hasKind("house")) putStack("house", (cols / 2 + 1).coerceAtMost(cols - 1), 3.coerceAtMost(rows - 1))
        if (!hasKind("gift") && !hasKind("gift_art")) putStack("gift", (cols - 4).coerceAtLeast(0), 5.coerceAtMost(rows - 1))
    }

    /** 旧存档无花瓶时补一个空瓶（不覆盖已有）。 */
    private fun ensureIndoorVase(indoor: JSONArray, cols: Int, rows: Int) {
        var has = false
        for (y in 0 until indoor.length()) {
            val row = indoor.optJSONArray(y) ?: continue
            for (x in 0 until row.length()) {
                val k = cellKind(row.opt(x))
                if (k == "vase" || k == "vase_filled") {
                    has = true
                    break
                }
            }
            if (has) break
        }
        if (has) return
        val vx = 8.coerceAtMost(cols - 1)
        val vy = 3.coerceAtMost(rows - 1)
        while (indoor.length() <= vy) indoor.put(JSONArray())
        val row = indoor.getJSONArray(vy)
        while (row.length() <= vx) row.put(JSONObject.NULL)
        if (row.opt(vx) == null || row.opt(vx) == JSONObject.NULL) {
            row.put(vx, "vase")
        }
    }

    /** 对照 cell_value_kind：取最上层 kind。 */
    fun cellKind(cell: Any?): String? {
        if (cell == null || cell == JSONObject.NULL) return null
        when (cell) {
            is String -> {
                if (cell.isBlank()) return null
                if (cell.startsWith("@")) {
                    val body = cell.substring(1)
                    val kind = body.substringBefore(":")
                    return kind.ifBlank { null }
                }
                return cell
            }
            is JSONObject -> {
                val g = cell.optString("g").trim()
                val k = cell.optString("k").trim()
                if (g.isNotEmpty()) {
                    if (k.startsWith("@")) {
                        val body = k.substring(1)
                        return body.substringBefore(":").ifBlank { g }
                    }
                    return k.ifBlank { g }
                }
                return k.ifBlank { null }
            }
            else -> return cell.toString().ifBlank { null }
        }
    }

    fun tilesToKindGrid(tiles: JSONArray?, cols: Int, rows: Int): Array<Array<String?>> {
        val out = Array(rows) { arrayOfNulls<String?>(cols) }
        if (tiles == null) return out
        for (y in 0 until minOf(rows, tiles.length())) {
            val row = tiles.optJSONArray(y) ?: continue
            for (x in 0 until minOf(cols, row.length())) {
                val cell = row.opt(x)
                out[y][x] = when {
                    cell is String && cell.startsWith("@") -> "@"
                    else -> cellKind(cell)
                }
            }
        }
        return out
    }

    fun kindGridToTiles(grid: Array<Array<String?>>): JSONArray {
        val arr = JSONArray()
        for (y in grid.indices) {
            val row = JSONArray()
            for (x in grid[y].indices) {
                val k = grid[y][x]
                if (k == null) row.put(JSONObject.NULL) else row.put(k)
            }
            arr.put(row)
        }
        return arr
    }

    private fun petPair(arr: JSONArray?, fx: Int, fy: Int, cols: Int, rows: Int): JSONArray {
        val x = (arr?.optInt(0, fx) ?: fx).coerceIn(0, cols - 1)
        val y = (arr?.optInt(1, fy) ?: fy).coerceIn(0, rows - 1)
        return JSONArray().put(x).put(y)
    }

    private fun copyGrid(
        src: JSONArray?,
        cols: Int,
        rows: Int,
        indoorDefault: Boolean,
    ): JSONArray {
        val fallback = if (indoorDefault) defaultIndoorTiles() else defaultOutdoorTiles()
        val out = JSONArray()
        for (y in 0 until rows) {
            val row = JSONArray()
            val srcRow = src?.optJSONArray(y)
            for (x in 0 until cols) {
                val v = srcRow?.opt(x)
                if (v == null || v == JSONObject.NULL) {
                    row.put(fallback.optJSONArray(y)?.opt(x) ?: JSONObject.NULL)
                } else {
                    row.put(v)
                }
            }
            out.put(row)
        }
        return out
    }

    private fun blank(cols: Int = COLS_DEFAULT, rows: Int = ROWS_DEFAULT): JSONArray {
        val a = JSONArray()
        for (y in 0 until rows) {
            val row = JSONArray()
            for (x in 0 until cols) row.put(JSONObject.NULL)
            a.put(row)
        }
        return a
    }

    private fun place(tiles: JSONArray, kind: String, x: Int, y: Int, w: Int = 1, h: Int = 1) {
        for (dy in 0 until h) for (dx in 0 until w) {
            val cx = x + dx
            val cy = y + dy
            if (cy !in 0 until tiles.length()) continue
            val row = tiles.getJSONArray(cy)
            if (cx !in 0 until row.length()) continue
            row.put(cx, if (dx == 0 && dy == 0) kind else "@$kind:$dx,$dy")
        }
    }

    private fun defaultIndoorTiles(): JSONArray {
        val tiles = blank()
        place(tiles, "window", 1, 0, 2, 1)
        place(tiles, "bed", 1, 2, 2, 1)
        place(tiles, "carpet", 4, 4, 2, 2)
        place(tiles, "table", 5, 6)
        place(tiles, "chair", 5, 7)
        place(tiles, "plant", 9, 7)
        place(tiles, "lamp", 3, 2)
        place(tiles, "vase", 8, 3)
        place(tiles, "plant", 10, 1)
        place(tiles, "door", 0, 5)
        return tiles
    }

    private fun defaultOutdoorTiles(): JSONArray {
        val tiles = blank()
        for (y in 0 until ROWS_DEFAULT) {
            val row = tiles.getJSONArray(y)
            for (x in 0 until COLS_DEFAULT) row.put(x, "grass")
        }
        fun stack(kind: String, x: Int, y: Int) {
            tiles.getJSONArray(y).put(x, JSONObject().put("g", "grass").put("k", kind))
        }
        stack("tree", 2, 2)
        stack("tree", 9, 3)
        tiles.getJSONArray(7).put(1, "rock")
        stack("flower", 4, 5)
        stack("flower", 7, 6)
        stack("bush", 10, 7)
        stack("fence", 0, 4)
        stack("fence", 0, 5)
        tiles.getJSONArray(1).put(5, "path")
        tiles.getJSONArray(2).put(5, "path")
        tiles.getJSONArray(3).put(5, "path")
        stack("door", 5, 4)
        stack("house", 6, 3)
        stack("gift", 8, 5)
        tiles.getJSONArray(8).put(8, "water")
        tiles.getJSONArray(8).put(3, "land")
        return tiles
    }
}
