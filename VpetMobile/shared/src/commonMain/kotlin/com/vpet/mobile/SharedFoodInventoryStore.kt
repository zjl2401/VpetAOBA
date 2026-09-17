package com.vpet.mobile

/** 共享食物背包。 */
object SharedFoodInventoryStore {
    private const val PREF = "vpet_food_inv"
    private const val KEY_JSON = "inv_json"
    private const val KEY_SEEDED = "seeded_v1"
    private const val KEY_CATALOG_VER = "catalog_ver"
    private const val CATALOG_VER = 2

    private fun prefs() = PlatformStorage(PREF)

    fun ensureSeeded() {
        val p = prefs()
        val first = !p.getBoolean(KEY_SEEDED, false)
        val ver = p.getInt(KEY_CATALOG_VER, 0)
        val m = loadRaw()
        var changed = false
        for (f in FoodCatalog.ALL) {
            if (!m.containsKey(f.id)) {
                m[f.id] = FoodCatalog.NEW_KIND_SEED
                changed = true
            }
        }
        if (first || changed || ver < CATALOG_VER) {
            save(m)
            p.putBoolean(KEY_SEEDED, true)
            p.putInt(KEY_CATALOG_VER, CATALOG_VER)
        }
    }

    private fun loadRaw(): MutableMap<String, Int> {
        val raw = prefs().getString(KEY_JSON, "{}") ?: "{}"
        val out = mutableMapOf<String, Int>()
        val o = SimpleJson.parse(raw)
        for (k in o.keys()) {
            out[k] = o.optInt(k, 0).coerceAtLeast(0)
        }
        return out
    }

    fun load(): MutableMap<String, Int> {
        ensureSeeded()
        val out = mutableMapOf<String, Int>()
        val raw = loadRaw()
        for (f in FoodCatalog.ALL) {
            out[f.id] = raw[f.id] ?: 0
        }
        return out
    }

    private fun save(map: Map<String, Int>) {
        val o = SimpleJson()
        for ((k, v) in map) o.put(k, v.coerceAtLeast(0))
        prefs().putString(KEY_JSON, o.encode())
    }

    fun count(id: String): Int = load()[id] ?: 0

    fun add(id: String, n: Int = 1) {
        if (FoodCatalog.byId(id) == null || n <= 0) return
        val m = load()
        m[id] = (m[id] ?: 0) + n
        save(m)
    }

    fun consumeOne(id: String): Boolean {
        val m = load()
        val c = m[id] ?: 0
        if (c <= 0) return false
        m[id] = c - 1
        save(m)
        return true
    }
}
