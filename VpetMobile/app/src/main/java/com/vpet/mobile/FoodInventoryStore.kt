package com.vpet.mobile

import android.content.Context
import org.json.JSONObject

/** 食物背包：对照 food_inventory.json；展示全部种类（含 ×0）。 */
object FoodInventoryStore {
    private const val PREF = "vpet_food_inv"
    private const val KEY_JSON = "inv_json"
    private const val KEY_SEEDED = "seeded_v1"
    private const val KEY_CATALOG_VER = "catalog_ver"
    private const val CATALOG_VER = 2

    private fun prefs(ctx: Context) = ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE)

    fun ensureSeeded(ctx: Context) {
        PersistVault.bootstrap(ctx)
        val p = prefs(ctx)
        val first = !p.getBoolean(KEY_SEEDED, false)
        val ver = p.getInt(KEY_CATALOG_VER, 0)
        val m = loadRaw(ctx)
        var changed = false
        for (f in FoodCatalog.ALL) {
            if (!m.containsKey(f.id)) {
                // 首装全量种子；升级新增种类也给 NEW_KIND_SEED
                m[f.id] = FoodCatalog.NEW_KIND_SEED
                changed = true
            }
        }
        if (first || changed || ver < CATALOG_VER) {
            save(ctx, m)
            p.edit()
                .putBoolean(KEY_SEEDED, true)
                .putInt(KEY_CATALOG_VER, CATALOG_VER)
                .apply()
        }
    }

    private fun loadRaw(ctx: Context): MutableMap<String, Int> {
        val raw = prefs(ctx).getString(KEY_JSON, "{}") ?: "{}"
        val out = mutableMapOf<String, Int>()
        try {
            val o = JSONObject(raw)
            val keys = o.keys()
            while (keys.hasNext()) {
                val k = keys.next()
                out[k] = o.optInt(k, 0).coerceAtLeast(0)
            }
        } catch (_: Exception) {
        }
        return out
    }

    fun load(ctx: Context): MutableMap<String, Int> {
        ensureSeeded(ctx)
        val out = mutableMapOf<String, Int>()
        val raw = loadRaw(ctx)
        for (f in FoodCatalog.ALL) {
            out[f.id] = raw[f.id] ?: 0
        }
        return out
    }

    private fun save(ctx: Context, map: Map<String, Int>) {
        val o = JSONObject()
        for ((k, v) in map) o.put(k, v.coerceAtLeast(0))
        prefs(ctx).edit().putString(KEY_JSON, o.toString()).apply()
        PersistVault.snapshot(ctx)
    }

    fun count(ctx: Context, id: String): Int = load(ctx)[id] ?: 0

    fun add(ctx: Context, id: String, n: Int = 1) {
        if (FoodCatalog.byId(id) == null || n <= 0) return
        val m = load(ctx)
        m[id] = (m[id] ?: 0) + n
        save(ctx, m)
    }

    /** @return 是否成功扣 1 份 */
    fun consumeOne(ctx: Context, id: String): Boolean {
        val m = load(ctx)
        val c = m[id] ?: 0
        if (c <= 0) return false
        m[id] = c - 1
        save(ctx, m)
        return true
    }
}
