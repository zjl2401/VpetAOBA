package com.vpet.mobile

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/** Silent Oath 瓦片与关卡加载（对照 game.py）。 */
object RpgMapLoader {
    const val GRASS = 1
    const val LAND = 2
    const val WATER = 3
    const val BRICK = 4
    const val TREE = 5
    const val ROCK = 6
    const val OBSTACLE = 7
    const val HOUSE = 8
    const val TREASURE = 9
    const val STAIRS = 11
    const val CAVE = 12
    const val GATE = 13
    const val TREASURE_OPEN = 14
    const val MOUNTAIN = 15
    const val TRAP_SPIKE = 18
    const val TRAP_PIT = 19
    const val PICKUP_COIN = 20

    val WALLS = setOf(WATER, BRICK, ROCK, OBSTACLE, HOUSE, MOUNTAIN, 10)
    val TRAPS = setOf(TRAP_SPIKE, TRAP_PIT)

    data class LevelMeta(val idx: Int, val asset: String, val name: String)

    val CAMPAIGN = listOf(
        LevelMeta(0, "rpg/level_01.json", "第一关 · 绿野秘洞"),
        LevelMeta(1, "rpg/level_02.json", "第二关 · 荒原地穴"),
        LevelMeta(2, "rpg/level_03.json", "第三关 · 湖畔洞窟"),
        LevelMeta(3, "rpg/level_04.json", "最终关 · 地下牢笼"),
    )

    data class CampaignMap(
        val name: String,
        val cols: Int,
        val rows: Int,
        val surface: Array<IntArray>,
        val underground: Array<IntArray>,
        val startX: Int,
        val startY: Int,
        val goalX: Int,
        val goalY: Int,
        val goalLayer: String,
        val princess: Boolean,
        val levelIdx: Int,
    )

    fun loadCampaign(context: Context, assetPath: String): CampaignMap? {
        return try {
            val text = context.assets.open(assetPath).bufferedReader().use { it.readText() }
            parseCampaignJson(text)
        } catch (_: Exception) {
            null
        }
    }

    fun loadFromFile(path: String): CampaignMap? {
        return try {
            parseCampaignJson(java.io.File(path).readText())
        } catch (_: Exception) {
            null
        }
    }

    private fun parseCampaignJson(text: String): CampaignMap? {
        return try {
            val o = JSONObject(text)
            val w = o.getInt("width")
            val h = o.getInt("height")
            val surfaceArr = o.optJSONArray("surface") ?: o.getJSONArray("tiles")
            val surface = readGrid(surfaceArr, w, h)
            val under = if (o.has("underground")) {
                readGrid(o.getJSONArray("underground"), w, h)
            } else {
                Array(h) { surface[it].clone() }
            }
            val start = o.getJSONArray("start")
            val goal = o.getJSONArray("goal")
            CampaignMap(
                name = o.optString("name", "map"),
                cols = w,
                rows = h,
                surface = surface,
                underground = under,
                startX = start.getInt(0).coerceIn(0, w - 1),
                startY = start.getInt(1).coerceIn(0, h - 1),
                goalX = goal.getInt(0).coerceIn(0, w - 1),
                goalY = goal.getInt(1).coerceIn(0, h - 1),
                goalLayer = o.optString("goal_layer", "surface"),
                princess = o.optBoolean("princess", false),
                levelIdx = o.optInt("level_idx", -1),
            )
        } catch (_: Exception) {
            null
        }
    }

    fun loadDiy001(context: Context): CampaignMap? {
        return try {
            val text = context.assets.open("rpg/diy_001.json").bufferedReader().use { it.readText() }
            val o = JSONObject(text)
            val w = o.getInt("width")
            val h = o.getInt("height")
            val tiles = o.getJSONArray("tiles")
            val surface = Array(h) { IntArray(w) }
            for (y in 0 until h) {
                val row = tiles.getJSONArray(y)
                for (x in 0 until w) {
                    val t = row.getInt(x)
                    surface[y][x] = when (t) {
                        4, 6, 13 -> ROCK
                        else -> GRASS
                    }
                }
            }
            val start = o.getJSONArray("start")
            val goal = o.getJSONArray("goal")
            val sx = start.getInt(0).coerceIn(0, w - 1)
            val sy = start.getInt(1).coerceIn(0, h - 1)
            val gx = goal.getInt(0).coerceIn(0, w - 1)
            val gy = goal.getInt(1).coerceIn(0, h - 1)
            surface[sy][sx] = GRASS
            surface[gy][gx] = GATE
            var placed = 0
            var guard = 0
            while (placed < 10 && guard < 400) {
                guard++
                val x = (0 until w).random()
                val y = (0 until h).random()
                if (surface[y][x] == GRASS && !(x == sx && y == sy) && !(x == gx && y == gy)) {
                    surface[y][x] = PICKUP_COIN
                    placed++
                }
            }
            CampaignMap(
                name = "DIY · diy_001",
                cols = w,
                rows = h,
                surface = surface,
                underground = Array(h) { surface[it].clone() },
                startX = sx,
                startY = sy,
                goalX = gx,
                goalY = gy,
                goalLayer = "surface",
                princess = false,
                levelIdx = -1,
            )
        } catch (_: Exception) {
            null
        }
    }

    private fun readGrid(arr: JSONArray, w: Int, h: Int): Array<IntArray> {
        val out = Array(h) { IntArray(w) }
        for (y in 0 until minOf(h, arr.length())) {
            val row = arr.getJSONArray(y)
            for (x in 0 until minOf(w, row.length())) {
                out[y][x] = row.getInt(x)
            }
        }
        return out
    }
}
