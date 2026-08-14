package com.vpet.mobile

import android.content.Context
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * 钱包：对照 wallet.json（coins + items + 每日登录礼）。
 */
object WalletStore {
    private const val PREF = "vpet_wallet"
    private const val KEY_JSON = "wallet_json"
    const val ITEM_WORK_BOX = "work_reward_box"
    const val ITEM_WOOD = "wood"
    const val DAILY_LOGIN_COINS = 1

    /** 对照 SEED_START：首次钱包含种子。 */
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

    private fun prefs(ctx: Context) = ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE)

    private fun loadObj(ctx: Context): JSONObject {
        PersistVault.bootstrap(ctx)
        val raw = prefs(ctx).getString(KEY_JSON, null)
        if (raw.isNullOrBlank()) {
            val seeded = JSONObject().apply {
                put("coins", 20)
                put("items", JSONObject().apply {
                    SEED_START.forEach { (k, v) -> put(k, v) }
                })
                put("last_daily_coin_ymd", "")
                put("work_boxes_total", 0)
                put("work_reward_boxes_granted", 0)
            }
            // 首装立刻落盘，避免下次被当成「空档」反复重置种子
            saveObj(ctx, seeded)
            return seeded
        }
        return try {
            JSONObject(raw)
        } catch (_: Exception) {
            JSONObject().put("coins", 20).put("items", JSONObject())
        }
    }

    private fun saveObj(ctx: Context, o: JSONObject) {
        prefs(ctx).edit().putString(KEY_JSON, o.toString()).apply()
        PersistVault.snapshot(ctx)
    }

    fun coins(ctx: Context): Int = loadObj(ctx).optInt("coins", 0).coerceAtLeast(0)

    fun itemCount(ctx: Context, id: String): Int =
        loadObj(ctx).optJSONObject("items")?.optInt(id, 0)?.coerceAtLeast(0) ?: 0

    fun grantCoins(ctx: Context, n: Int): Int {
        if (n <= 0) return coins(ctx)
        val o = loadObj(ctx)
        o.put("coins", o.optInt("coins", 0) + n)
        saveObj(ctx, o)
        return o.optInt("coins")
    }

    fun trySpendCoins(ctx: Context, n: Int): Boolean {
        if (n <= 0) return true
        val o = loadObj(ctx)
        val c = o.optInt("coins", 0)
        if (c < n) return false
        o.put("coins", c - n)
        saveObj(ctx, o)
        return true
    }

    /** 补齐经营种子键（不覆盖已有数量）。 */
    fun ensureFarmItems(ctx: Context) {
        val o = loadObj(ctx)
        val items = o.optJSONObject("items") ?: JSONObject().also { o.put("items", it) }
        var changed = false
        for ((k, v) in SEED_START) {
            if (!items.has(k)) {
                items.put(k, v)
                changed = true
            }
        }
        if (changed) saveObj(ctx, o)
    }

    fun grantItem(ctx: Context, id: String, n: Int = 1) {
        if (n <= 0) return
        val o = loadObj(ctx)
        val items = o.optJSONObject("items") ?: JSONObject().also { o.put("items", it) }
        items.put(id, items.optInt(id, 0) + n)
        saveObj(ctx, o)
    }

    fun consumeItem(ctx: Context, id: String, n: Int = 1): Boolean {
        val o = loadObj(ctx)
        val items = o.optJSONObject("items") ?: return false
        val c = items.optInt(id, 0)
        if (c < n) return false
        items.put(id, c - n)
        saveObj(ctx, o)
        return true
    }

    /** 每天首次打开 +1 金币。 */
    fun tryDailyLoginCoin(ctx: Context): Boolean {
        val o = loadObj(ctx)
        val today = SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date())
        if (o.optString("last_daily_coin_ymd") == today) return false
        o.put("last_daily_coin_ymd", today)
        o.put("coins", o.optInt("coins", 0) + DAILY_LOGIN_COINS)
        saveObj(ctx, o)
        return true
    }

    /**
     * 工作送达 1 箱：对照 `_note_work_box_delivered`。
     * @return 新发放的宝箱数（通常 0 或 1）
     */
    fun noteWorkBoxDelivered(ctx: Context): Int {
        val o = loadObj(ctx)
        val total = o.optInt("work_boxes_total", 0) + 1
        o.put("work_boxes_total", total)
        val granted = o.optInt("work_reward_boxes_granted", 0)
        val should = total / 25
        val n = (should - granted).coerceAtLeast(0)
        if (n > 0) {
            o.put("work_reward_boxes_granted", granted + n)
            val items = o.optJSONObject("items") ?: JSONObject().also { o.put("items", it) }
            items.put(ITEM_WORK_BOX, items.optInt(ITEM_WORK_BOX, 0) + n)
        }
        saveObj(ctx, o)
        return n
    }

    fun workBoxesTotal(ctx: Context): Int = loadObj(ctx).optInt("work_boxes_total", 0)

    /** 开启工作宝箱；返回文案。 */
    fun openWorkRewardBox(ctx: Context): String? {
        if (!consumeItem(ctx, ITEM_WORK_BOX, 1)) return null
        val r = kotlin.random.Random.nextFloat()
        return when {
            r < 0.55f -> {
                val n = kotlin.random.Random.nextInt(3, 13)
                grantCoins(ctx, n)
                "开箱！金币 +$n"
            }
            r < 0.72f -> {
                val n = kotlin.random.Random.nextInt(1, 4)
                grantItem(ctx, ITEM_WOOD, n)
                "开箱！木材 ×$n"
            }
            r < 0.86f -> {
                val n = kotlin.random.Random.nextInt(1, 3)
                FoodInventoryStore.add(ctx, listOf("apple", "bread", "candy").random(), n)
                "开箱！零食 ×$n"
            }
            else -> {
                FoodInventoryStore.add(ctx, FoodCatalog.randomCollectId(), 1)
                "开箱！获得一份食材"
            }
        }
    }
}
