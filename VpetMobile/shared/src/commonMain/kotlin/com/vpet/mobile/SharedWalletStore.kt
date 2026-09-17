package com.vpet.mobile

import kotlin.random.Random

/** 共享钱包：对照 wallet.json（无 Android Context）。 */
object SharedWalletStore {
    private const val PREF = "vpet_wallet"
    private const val KEY_JSON = "wallet_json"
    const val ITEM_WORK_BOX = "work_reward_box"
    const val ITEM_WOOD = "wood"
    const val DAILY_LOGIN_COINS = 1

    private val SEED_START = mapOf(
        "seed_wheat" to 4,
        "seed_berry" to 2,
        "seed_corn" to 2,
        ITEM_WOOD to 1,
        "flower_cut" to 0,
        "fish" to 0,
        ITEM_WORK_BOX to 0,
        "crop_wheat" to 0,
        "crop_berry" to 0,
        "crop_corn" to 0,
    )

    private fun storage() = PlatformStorage(PREF)

    private fun loadObj(): SimpleJson {
        val raw = storage().getString(KEY_JSON, null)
        if (raw.isNullOrBlank()) {
            return SimpleJson()
                .put("coins", 20)
                .put(
                    "items",
                    SimpleJson().also { items ->
                        SEED_START.forEach { (k, v) -> items.put(k, v) }
                    },
                )
                .put("last_daily_coin_ymd", "")
                .put("work_boxes_total", 0)
                .put("work_reward_boxes_granted", 0)
        }
        return SimpleJson.parse(raw)
    }

    private fun saveObj(o: SimpleJson) {
        storage().putString(KEY_JSON, o.encode())
    }

    fun coins(): Int = loadObj().optInt("coins", 0).coerceAtLeast(0)

    fun itemCount(id: String): Int =
        (loadObj().optObject("items")?.optInt(id, 0) ?: 0).coerceAtLeast(0)

    fun grantCoins(n: Int): Int {
        if (n <= 0) return coins()
        val o = loadObj()
        o.put("coins", o.optInt("coins", 0) + n)
        saveObj(o)
        return o.optInt("coins")
    }

    fun trySpendCoins(n: Int): Boolean {
        if (n <= 0) return true
        val o = loadObj()
        val c = o.optInt("coins", 0)
        if (c < n) return false
        o.put("coins", c - n)
        saveObj(o)
        return true
    }

    fun ensureFarmItems() {
        val o = loadObj()
        val items = o.ensureObject("items")
        var changed = false
        for ((k, v) in SEED_START) {
            if (!items.has(k)) {
                items.put(k, v)
                changed = true
            }
        }
        if (changed) saveObj(o)
    }

    fun grantItem(id: String, n: Int = 1) {
        if (n <= 0) return
        val o = loadObj()
        val items = o.ensureObject("items")
        items.put(id, items.optInt(id, 0) + n)
        saveObj(o)
    }

    fun consumeItem(id: String, n: Int = 1): Boolean {
        val o = loadObj()
        val items = o.optObject("items") ?: return false
        val c = items.optInt(id, 0)
        if (c < n) return false
        items.put(id, c - n)
        saveObj(o)
        return true
    }

    fun tryDailyLoginCoin(): Boolean {
        val o = loadObj()
        val today = PlatformClock.formatDay()
        if (o.optString("last_daily_coin_ymd") == today) return false
        o.put("last_daily_coin_ymd", today)
        o.put("coins", o.optInt("coins", 0) + DAILY_LOGIN_COINS)
        saveObj(o)
        return true
    }

    fun noteWorkBoxDelivered(): Int {
        val o = loadObj()
        val total = o.optInt("work_boxes_total", 0) + 1
        o.put("work_boxes_total", total)
        val granted = o.optInt("work_reward_boxes_granted", 0)
        val should = total / 25
        val n = (should - granted).coerceAtLeast(0)
        if (n > 0) {
            o.put("work_reward_boxes_granted", granted + n)
            val items = o.ensureObject("items")
            items.put(ITEM_WORK_BOX, items.optInt(ITEM_WORK_BOX, 0) + n)
        }
        saveObj(o)
        return n
    }

    fun workBoxesTotal(): Int = loadObj().optInt("work_boxes_total", 0)

    fun openWorkRewardBox(): String? {
        if (!consumeItem(ITEM_WORK_BOX, 1)) return null
        val r = Random.nextFloat()
        return when {
            r < 0.55f -> {
                val n = Random.nextInt(3, 13)
                grantCoins(n)
                "开箱！金币 +$n"
            }
            r < 0.72f -> {
                val n = Random.nextInt(1, 4)
                grantItem(ITEM_WOOD, n)
                "开箱！木材 ×$n"
            }
            r < 0.86f -> {
                val n = Random.nextInt(1, 3)
                SharedFoodInventoryStore.add(listOf("apple", "bread", "candy").random(), n)
                "开箱！零食 ×$n"
            }
            else -> {
                SharedFoodInventoryStore.add(FoodCatalog.randomCollectId(), 1)
                "开箱！获得一份食材"
            }
        }
    }
}
