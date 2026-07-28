package com.vpet.mobile

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.random.Random

/**
 * 家园经营：对照 `home_farm.py`（锄种浇收砍钓采 + 成长/商店/合成最小集）。
 */
object HomeFarmEngine {
    const val MATURITY_MAX = 100.0
    const val MATURITY_PER_HOUR = 5.0
    const val WATER_BOOST_SEC = 3600.0
    const val WATER_MAX_PER_DAY = 2
    const val TREE_REGROW_SEC = 48 * 3600.0
    const val CHOP_DICE_MIN = 2
    const val CHOP_DICE_MAX = 6

    enum class Tool(val id: String, val label: String, val hint: String) {
        TILL("till", "锄地", "先清上面，再锄两下草地→土地"),
        PLANT("plant", "播种", "仅土地可种"),
        WATER("water", "浇水", "每天最多2次；浇后1小时×2"),
        HARVEST("harvest", "收获", "成熟度满100可收"),
        CHOP("chop", "砍树", "点树四周格子"),
        FISH("fish", "钓鱼", "点水面四周；上钩后再点"),
        PICK("pick", "采花", "采小花入背包"),
    }

    data class CropDef(val label: String, val seed: String, val item: String, val colors: List<String>)

    val CROP_DEFS = mapOf(
        "wheat" to CropDef("小麦", "seed_wheat", "crop_wheat", listOf("#c8b070", "#d4c078", "#e8d888", "#f0e090")),
        "berry" to CropDef("莓果", "seed_berry", "crop_berry", listOf("#886688", "#aa6688", "#cc6688", "#ee5588")),
        "corn" to CropDef("玉米", "seed_corn", "crop_corn", listOf("#889944", "#aaba44", "#ccdd55", "#ffe066")),
    )

    val SEED_TO_CROP = mapOf(
        "seed_wheat" to "wheat",
        "seed_berry" to "berry",
        "seed_corn" to "corn",
    )

    val ITEM_LABELS = mapOf(
        "seed_wheat" to "麦种",
        "seed_berry" to "莓种",
        "seed_corn" to "玉米种",
        "crop_wheat" to "小麦",
        "crop_berry" to "莓果",
        "crop_corn" to "玉米穗",
        "wood" to "木材",
        "flower_cut" to "采下的花",
        "fish" to "鲜鱼",
        WalletStore.ITEM_WORK_BOX to "工作宝箱",
    )

    val SHOP_PRICES = mapOf(
        "seed_wheat" to 3,
        "seed_berry" to 4,
        "seed_corn" to 4,
        "wood" to 5,
    )

    val SELL_PRICES = mapOf(
        "crop_wheat" to 4,
        "crop_berry" to 5,
        "crop_corn" to 5,
        "fish" to 6,
        "flower_cut" to 2,
    )

    data class CraftRecipe(
        val id: String,
        val label: String,
        val costs: Map<String, Int>,
        val resultType: String, // food | furniture | item
        val resultId: String,
        val desc: String,
    )

    val CRAFT_RECIPES = listOf(
        CraftRecipe("bread", "烤面包", mapOf("crop_wheat" to 2), "food", "bread", "2小麦→面包"),
        CraftRecipe("berry_snack", "莓果点心", mapOf("crop_berry" to 2), "food", "berry", "2莓果→草莓"),
        CraftRecipe("corn_food", "烤玉米", mapOf("crop_corn" to 2), "food", "corn", "2玉米穗→玉米"),
        CraftRecipe("juice", "果汁", mapOf("crop_berry" to 1, "crop_wheat" to 1), "food", "juice", "莓+麦→果汁"),
        CraftRecipe("sofa", "解锁沙发", mapOf("wood" to 3, "crop_wheat" to 1), "furniture", "sofa", "3木+1麦"),
        CraftRecipe("shelf", "解锁柜子", mapOf("wood" to 2, "crop_berry" to 1), "furniture", "shelf", "2木+1莓"),
    )

    data class ActResult(val ok: Boolean, val msg: String)

    fun dayKey(ts: Long = System.currentTimeMillis()): String =
        SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date(ts))

    fun ensureFarmGrid(layout: JSONObject): Array<Array<JSONObject?>> {
        val cols = layout.optInt("cols", 12)
        val rows = layout.optInt("rows", 10)
        val raw = layout.optJSONArray("farm")
        val out = Array(rows) { arrayOfNulls<JSONObject?>(cols) }
        if (raw != null) {
            for (y in 0 until minOf(rows, raw.length())) {
                val row = raw.optJSONArray(y) ?: continue
                for (x in 0 until minOf(cols, row.length())) {
                    out[y][x] = normalizePlot(row.opt(x))
                }
            }
        }
        return out
    }

    fun writeFarmGrid(layout: JSONObject, farm: Array<Array<JSONObject?>>) {
        val arr = JSONArray()
        for (y in farm.indices) {
            val row = JSONArray()
            for (x in farm[y].indices) {
                val p = farm[y][x]
                if (p == null) row.put(JSONObject.NULL) else row.put(p)
            }
            arr.put(row)
        }
        layout.put("farm", arr)
    }

    fun normalizePlot(v: Any?): JSONObject? {
        if (v == null || v == JSONObject.NULL || v !is JSONObject) return null
        val crop = v.optString("crop").trim()
        if (crop !in CROP_DEFS) return null
        val now = System.currentTimeMillis() / 1000.0
        val planted = v.optLong("planted_at", 0L)
        val maturity = if (v.has("maturity")) {
            v.optDouble("maturity", 0.0).coerceIn(0.0, MATURITY_MAX)
        } else {
            val watered = v.optInt("watered", 0)
            val elapsedH = if (planted > 0) ((now - planted) / 3600.0).coerceAtLeast(0.0) else 0.0
            (elapsedH * MATURITY_PER_HOUR + watered * 8.0).coerceIn(0.0, MATURITY_MAX)
        }
        return JSONObject()
            .put("crop", crop)
            .put("planted_at", planted)
            .put("maturity", maturity)
            .put("last_tick", v.optDouble("last_tick", planted.toDouble().takeIf { it > 0 } ?: now))
            .put("boost_until", v.optDouble("boost_until", 0.0))
            .put("water_day", v.optString("water_day", ""))
            .put("water_count", v.optInt("water_count", 0))
            .put("watered", v.optInt("water_count", v.optInt("watered", 0)))
    }

    fun advancePlot(plot: JSONObject?, nowSec: Double = System.currentTimeMillis() / 1000.0) {
        if (plot == null) return
        var last = plot.optDouble("last_tick", plot.optDouble("planted_at", nowSec))
        if (nowSec <= last) {
            plot.put("last_tick", nowSec)
            return
        }
        var maturity = plot.optDouble("maturity", 0.0)
        val boostUntil = plot.optDouble("boost_until", 0.0)
        val rate = MATURITY_PER_HOUR / 3600.0
        var t0 = last
        while (t0 < nowSec && maturity < MATURITY_MAX) {
            if (t0 < boostUntil) {
                val seg = minOf(nowSec, boostUntil)
                maturity += (seg - t0) * rate * 2.0
                t0 = seg
            } else {
                maturity += (nowSec - t0) * rate
                t0 = nowSec
            }
        }
        plot.put("maturity", maturity.coerceIn(0.0, MATURITY_MAX))
        plot.put("last_tick", nowSec)
    }

    fun advanceFarm(farm: Array<Array<JSONObject?>>) {
        val now = System.currentTimeMillis() / 1000.0
        for (row in farm) for (p in row) advancePlot(p, now)
    }

    fun plotProgress(plot: JSONObject?): Float {
        if (plot == null) return 0f
        advancePlot(plot)
        return (plot.optDouble("maturity", 0.0) / MATURITY_MAX).toFloat().coerceIn(0f, 1f)
    }

    fun plotReady(plot: JSONObject?): Boolean {
        if (plot == null) return false
        advancePlot(plot)
        return plot.optDouble("maturity", 0.0) >= MATURITY_MAX - 1e-6
    }

    fun plotColor(plot: JSONObject?): String {
        if (plot == null) return "#5a4830"
        val crop = plot.optString("crop")
        val colors = CROP_DEFS[crop]?.colors ?: return "#5a4830"
        val prog = plotProgress(plot)
        val st = when {
            prog >= 1f -> 3
            prog >= 0.66f -> 2
            prog >= 0.33f -> 1
            else -> 0
        }
        return colors[st.coerceIn(0, colors.lastIndex)]
    }

    fun plotBoostActive(plot: JSONObject?): Boolean {
        if (plot == null) return false
        val now = System.currentTimeMillis() / 1000.0
        return plot.optDouble("boost_until", 0.0) > now
    }

    fun tileKey(x: Int, y: Int) = "$x,$y"

    fun loadTillHits(layout: JSONObject): MutableMap<String, Int> {
        val o = layout.optJSONObject("till_hits") ?: return mutableMapOf()
        val m = mutableMapOf<String, Int>()
        o.keys().forEach { k -> m[k] = o.optInt(k, 0) }
        return m
    }

    fun saveTillHits(layout: JSONObject, hits: Map<String, Int>) {
        val o = JSONObject()
        hits.forEach { (k, v) -> if (v > 0) o.put(k, v) }
        layout.put("till_hits", o)
    }

    fun loadChopJobs(layout: JSONObject): MutableMap<String, JSONObject> {
        val o = layout.optJSONObject("chop_jobs") ?: return mutableMapOf()
        val m = mutableMapOf<String, JSONObject>()
        o.keys().forEach { k ->
            o.optJSONObject(k)?.let { m[k] = it }
        }
        return m
    }

    fun saveChopJobs(layout: JSONObject, jobs: Map<String, JSONObject>) {
        val o = JSONObject()
        jobs.forEach { (k, v) -> o.put(k, v) }
        layout.put("chop_jobs", o)
    }

    fun loadTreeRegrow(layout: JSONObject): MutableList<JSONObject> {
        val arr = layout.optJSONArray("tree_regrow") ?: return mutableListOf()
        val out = mutableListOf<JSONObject>()
        for (i in 0 until arr.length()) arr.optJSONObject(i)?.let { out.add(it) }
        return out
    }

    fun saveTreeRegrow(layout: JSONObject, list: List<JSONObject>) {
        val arr = JSONArray()
        list.forEach { arr.put(it) }
        layout.put("tree_regrow", arr)
    }

    fun loadCrafted(layout: JSONObject): MutableList<String> {
        val arr = layout.optJSONArray("crafted_furniture") ?: return mutableListOf()
        val out = mutableListOf<String>()
        for (i in 0 until arr.length()) {
            val s = arr.optString(i)
            if (s.isNotBlank() && s !in out) out.add(s)
        }
        return out
    }

    fun saveCrafted(layout: JSONObject, list: List<String>) {
        val arr = JSONArray()
        list.forEach { arr.put(it) }
        layout.put("crafted_furniture", arr)
    }

    /** 场景格子读写接口。 */
    interface TileOps {
        fun kind(x: Int, y: Int): String?
        fun place(kind: String, x: Int, y: Int)
        fun clearToGrass(x: Int, y: Int)
    }

    fun tryTill(
        farm: Array<Array<JSONObject?>>,
        x: Int, y: Int,
        tillHits: MutableMap<String, Int>,
        tiles: TileOps,
    ): ActResult {
        if (y !in farm.indices || x !in farm[0].indices) return ActResult(false, "超出范围")
        farm[y][x] = null
        val kind = tiles.kind(x, y)
        if (kind in setOf("flower", "bush")) {
            tiles.clearToGrass(x, y)
            tillHits.remove(tileKey(x, y))
            return ActResult(true, "已除掉上面的东西")
        }
        if (kind == "land") {
            tillHits.remove(tileKey(x, y))
            return ActResult(true, "土地已整理，可以播种")
        }
        if (kind == "grass" || kind == null) {
            val key = tileKey(x, y)
            val hits = (tillHits[key] ?: 0) + 1
            if (hits >= 2) {
                tiles.place("land", x, y)
                tillHits.remove(key)
                return ActResult(true, "草地已翻成土地，可以播种了")
            }
            tillHits[key] = hits
            return ActResult(true, "再锄一下，草地就会变成土地")
        }
        return ActResult(false, "这里不能锄成田")
    }

    fun tryPlant(
        ctx: Context,
        farm: Array<Array<JSONObject?>>,
        x: Int, y: Int,
        seedId: String,
        tiles: TileOps,
    ): ActResult {
        val crop = SEED_TO_CROP[seedId] ?: return ActResult(false, "请先选择种子")
        if (y !in farm.indices || x !in farm[0].indices) return ActResult(false, "超出范围")
        if (tiles.kind(x, y) != "land") return ActResult(false, "请先把草地锄成土地（锄两下）")
        if (farm[y][x] != null) return ActResult(false, "这里已有作物")
        if (!WalletStore.consumeItem(ctx, seedId, 1)) {
            return ActResult(false, "${ITEM_LABELS[seedId] ?: seedId}不足")
        }
        val now = (System.currentTimeMillis() / 1000L)
        farm[y][x] = JSONObject()
            .put("crop", crop)
            .put("planted_at", now)
            .put("maturity", 0.0)
            .put("last_tick", now.toDouble())
            .put("boost_until", 0.0)
            .put("water_day", "")
            .put("water_count", 0)
            .put("watered", 0)
        return ActResult(true, "已播种")
    }

    fun tryWater(farm: Array<Array<JSONObject?>>, x: Int, y: Int): ActResult {
        if (y !in farm.indices || x !in farm[0].indices) return ActResult(false, "超出范围")
        val plot = farm[y][x] ?: return ActResult(false, "空地无需浇水")
        val now = System.currentTimeMillis() / 1000.0
        advancePlot(plot, now)
        if (plotReady(plot)) return ActResult(false, "已成熟，请收获")
        val day = dayKey()
        if (plot.optString("water_day") != day) {
            plot.put("water_day", day)
            plot.put("water_count", 0)
        }
        val count = plot.optInt("water_count", 0)
        if (count >= WATER_MAX_PER_DAY) return ActResult(false, "今天已经浇过两次了")
        plot.put("water_count", count + 1)
        plot.put("watered", count + 1)
        plot.put("boost_until", now + WATER_BOOST_SEC)
        return ActResult(true, "浇水！一小时内成长速度×2")
    }

    fun tryHarvest(ctx: Context, farm: Array<Array<JSONObject?>>, x: Int, y: Int): ActResult {
        if (y !in farm.indices || x !in farm[0].indices) return ActResult(false, "超出范围")
        val plot = farm[y][x] ?: return ActResult(false, "没有作物")
        if (!plotReady(plot)) return ActResult(false, "还没成熟")
        val crop = plot.optString("crop")
        val meta = CROP_DEFS[crop] ?: run {
            farm[y][x] = null
            return ActResult(false, "未知作物")
        }
        WalletStore.grantItem(ctx, meta.item, 1)
        farm[y][x] = null
        return ActResult(true, "收获了${ITEM_LABELS[meta.item] ?: meta.item}")
    }

    fun findAdjacent(
        tiles: TileOps,
        x: Int, y: Int,
        want: String,
        cols: Int, rows: Int,
    ): Pair<Int, Int>? {
        for ((dx, dy) in listOf(0 to 1, 0 to -1, 1 to 0, -1 to 0)) {
            val nx = x + dx
            val ny = y + dy
            if (nx in 0 until cols && ny in 0 until rows && tiles.kind(nx, ny) == want) {
                return nx to ny
            }
        }
        return null
    }

    fun tryChop(
        ctx: Context,
        tiles: TileOps,
        treeX: Int, treeY: Int,
        chopJobs: MutableMap<String, JSONObject>,
        treeRegrow: MutableList<JSONObject>,
    ): ActResult {
        val key = tileKey(treeX, treeY)
        var job = chopJobs[key]
        val kind = tiles.kind(treeX, treeY)
        if (kind != "tree" && job == null) return ActResult(false, "这里没有可砍的树")
        if (kind == "tree" && job == null) {
            val need = Random.nextInt(CHOP_DICE_MIN, CHOP_DICE_MAX + 1)
            if (need <= 1) {
                tiles.clearToGrass(treeX, treeY)
                WalletStore.grantItem(ctx, "wood", 1)
                treeRegrow.add(
                    JSONObject()
                        .put("x", treeX).put("y", treeY)
                        .put("ready_at", System.currentTimeMillis() / 1000.0 + TREE_REGROW_SEC),
                )
                return ActResult(true, "掷出 $need！一斧砍倒，木材+1")
            }
            chopJobs[key] = JSONObject().put("need", need).put("done", 1).put("x", treeX).put("y", treeY)
            return ActResult(true, "掷出 $need！砍树 1/$need")
        }
        job = job!!
        val done = job.optInt("done", 0) + 1
        val need = job.optInt("need", 1).coerceAtLeast(1)
        job.put("done", done)
        if (done < need) {
            chopJobs[key] = job
            return ActResult(true, "砍树 $done/$need")
        }
        tiles.clearToGrass(treeX, treeY)
        chopJobs.remove(key)
        WalletStore.grantItem(ctx, "wood", 1)
        treeRegrow.add(
            JSONObject()
                .put("x", treeX).put("y", treeY)
                .put("ready_at", System.currentTimeMillis() / 1000.0 + TREE_REGROW_SEC),
        )
        return ActResult(true, "树倒了！木材+1（48小时后可再生）")
    }

    fun processTreeRegrow(
        tiles: TileOps,
        treeRegrow: MutableList<JSONObject>,
        cols: Int, rows: Int,
    ): Int {
        val now = System.currentTimeMillis() / 1000.0
        val remain = mutableListOf<JSONObject>()
        var n = 0
        for (item in treeRegrow) {
            val ready = item.optDouble("ready_at", 0.0)
            val x = item.optInt("x")
            val y = item.optInt("y")
            if (ready > now) {
                remain.add(item)
                continue
            }
            if (x !in 0 until cols || y !in 0 until rows) continue
            val k = tiles.kind(x, y)
            if (k == null || k in setOf("grass", "land", "path", "brick")) {
                tiles.place("tree", x, y)
                n++
            } else {
                item.put("ready_at", now + 3600)
                remain.add(item)
            }
        }
        treeRegrow.clear()
        treeRegrow.addAll(remain)
        return n
    }

    fun tryPick(ctx: Context, tiles: TileOps, x: Int, y: Int): ActResult {
        if (tiles.kind(x, y) != "flower") return ActResult(false, "这里没有小花")
        tiles.clearToGrass(x, y)
        WalletStore.grantItem(ctx, "flower_cut", 1)
        return ActResult(true, "采到花了！可插花瓶，或面板背包戴头顶")
    }

    /** 室内花瓶插花：kind vase → vase_filled。 */
    fun tryPutFlowerInVase(ctx: Context, tiles: TileOps, x: Int, y: Int): ActResult {
        val k = tiles.kind(x, y)
        if (k != "vase" && k != "vase_filled") return ActResult(false, "请点在花瓶上")
        if (k == "vase_filled") return ActResult(false, "花瓶里已有花，先拔出来再插")
        if (WalletStore.itemCount(ctx, "flower_cut") <= 0) return ActResult(false, "还没有采下的花")
        if (!WalletStore.consumeItem(ctx, "flower_cut", 1)) return ActResult(false, "还没有采下的花")
        tiles.place("vase_filled", x, y)
        return ActResult(true, "花已插进花瓶")
    }

    fun tryTakeFlowerFromVase(ctx: Context, tiles: TileOps, x: Int, y: Int): ActResult {
        if (tiles.kind(x, y) != "vase_filled") return ActResult(false, "花瓶里没有花")
        tiles.place("vase", x, y)
        WalletStore.grantItem(ctx, "flower_cut", 1)
        return ActResult(true, "已拔出花，放回背包")
    }

    fun buy(ctx: Context, itemId: String): ActResult {
        val price = SHOP_PRICES[itemId] ?: return ActResult(false, "无法购买")
        if (!WalletStore.trySpendCoins(ctx, price)) return ActResult(false, "金币不足（需 $price）")
        WalletStore.grantItem(ctx, itemId, 1)
        return ActResult(true, "购入 ${ITEM_LABELS[itemId] ?: itemId}")
    }

    fun sell(ctx: Context, itemId: String): ActResult {
        val price = SELL_PRICES[itemId] ?: return ActResult(false, "不可出售")
        if (!WalletStore.consumeItem(ctx, itemId, 1)) return ActResult(false, "数量不足")
        WalletStore.grantCoins(ctx, price)
        return ActResult(true, "售出 +$price 金币")
    }

    fun tryCraft(ctx: Context, crafted: MutableList<String>, recipeId: String): ActResult {
        val recipe = CRAFT_RECIPES.find { it.id == recipeId } ?: return ActResult(false, "未知配方")
        for ((k, n) in recipe.costs) {
            if (WalletStore.itemCount(ctx, k) < n) return ActResult(false, "材料不足")
        }
        if (recipe.resultType == "furniture" && recipe.resultId in crafted) {
            return ActResult(false, "已解锁该家具")
        }
        for ((k, n) in recipe.costs) WalletStore.consumeItem(ctx, k, n)
        when (recipe.resultType) {
            "food" -> FoodInventoryStore.add(ctx, recipe.resultId, 1)
            "furniture" -> crafted.add(recipe.resultId)
            "item" -> WalletStore.grantItem(ctx, recipe.resultId, 1)
        }
        return ActResult(true, "合成成功：${recipe.label}")
    }

    fun applyFishRoll(ctx: Context): ActResult {
        val r = Random.nextFloat()
        return when {
            r < 0.45f -> {
                WalletStore.grantItem(ctx, "fish", 1)
                ActResult(true, "钓到鲜鱼！")
            }
            r < 0.70f -> {
                WalletStore.grantCoins(ctx, 2)
                ActResult(true, "钓到小东西，金币 +2")
            }
            else -> ActResult(false, "鱼跑了……")
        }
    }
}
