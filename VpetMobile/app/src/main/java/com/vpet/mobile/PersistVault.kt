package com.vpet.mobile

import android.content.Context
import org.json.JSONObject
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * 覆盖安装/异常清空后的本地保险档。
 * 保留：所属人与相伴起点、装扮、模式相伴时长、食物背包、家园钱包。
 * SharedPreferences 仍是主存；本文件在 filesDir，随应用数据一起在更新时保留。
 */
object PersistVault {
    private const val FILE = "vpet_persist_vault.json"
    private val fmt = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.CHINA)

    @Volatile
    private var bootstrapped = false

    fun bootstrap(ctx: Context) {
        if (bootstrapped) return
        synchronized(this) {
            if (bootstrapped) return
            try {
                restoreIfNeeded(ctx.applicationContext)
                snapshot(ctx.applicationContext)
            } catch (_: Exception) {
            }
            bootstrapped = true
        }
    }

    /** 关键存档写入保险档（各 Store 保存后调用）。 */
    fun snapshot(ctx: Context) {
        val app = ctx.applicationContext
        try {
            val profilePrefs = app.getSharedPreferences("vpet_profile", Context.MODE_PRIVATE)
            val profileRaw = profilePrefs.getString("pet_profile_json", null)
            val modePrefs = app.getSharedPreferences("vpet_mode_time", Context.MODE_PRIVATE)
            val modeRaw = modePrefs.getString("mode_seconds_json", null)
            val foodPrefs = app.getSharedPreferences("vpet_food_inv", Context.MODE_PRIVATE)
            val foodRaw = foodPrefs.getString("inv_json", null)
            val walletPrefs = app.getSharedPreferences("vpet_wallet", Context.MODE_PRIVATE)
            val walletRaw = walletPrefs.getString("wallet_json", null)

            val o = JSONObject()
                .put("v", 1)
                .put("saved_at", fmt.format(Date()))
            if (!profileRaw.isNullOrBlank()) o.put("profile", JSONObject(profileRaw))
            if (!modeRaw.isNullOrBlank()) o.put("mode_seconds", JSONObject(modeRaw))
            if (!foodRaw.isNullOrBlank()) o.put("food_inv", JSONObject(foodRaw))
            if (!walletRaw.isNullOrBlank()) o.put("wallet", JSONObject(walletRaw))
            // 至少有所属人或任一进度才落盘
            val hasOwner = o.optJSONObject("profile")?.optString("owner_name").orEmpty().isNotBlank()
            val hasProgress = o.has("mode_seconds") || o.has("food_inv") || o.has("wallet") ||
                (o.optJSONObject("profile")?.optJSONArray("outfit_decors")?.length() ?: 0) > 0
            if (!hasOwner && !hasProgress) return
            vaultFile(app).writeText(o.toString())
        } catch (_: Exception) {
        }
    }

    private fun restoreIfNeeded(ctx: Context) {
        val file = vaultFile(ctx)
        if (!file.isFile || file.length() < 8) return
        val vault = try {
            JSONObject(file.readText())
        } catch (_: Exception) {
            return
        }

        // —— 档案（含所属人 / 相伴起点 / 装扮）——
        val profilePrefs = ctx.getSharedPreferences("vpet_profile", Context.MODE_PRIVATE)
        val curProfileRaw = profilePrefs.getString("pet_profile_json", null)
        val vaultProfile = vault.optJSONObject("profile")
        if (vaultProfile != null) {
            val vaultOwner = vaultProfile.optString("owner_name", "").trim()
            val curOwner = try {
                if (curProfileRaw.isNullOrBlank()) ""
                else JSONObject(curProfileRaw).optString("owner_name", "").trim()
            } catch (_: Exception) {
                ""
            }
            val curOutfitLen = try {
                if (curProfileRaw.isNullOrBlank()) 0
                else JSONObject(curProfileRaw).optJSONArray("outfit_decors")?.length() ?: 0
            } catch (_: Exception) {
                0
            }
            val vaultOutfitLen = vaultProfile.optJSONArray("outfit_decors")?.length() ?: 0
            val needProfile = when {
                curProfileRaw.isNullOrBlank() && vaultOwner.isNotEmpty() -> true
                curOwner.isEmpty() && vaultOwner.isNotEmpty() -> true
                // 装扮丢了但保险档有
                curOutfitLen == 0 && vaultOutfitLen > 0 -> true
                // 相伴起点丢了
                ownerSetAtBlank(curProfileRaw) && !ownerSetAtBlank(vaultProfile.toString()) -> true
                else -> false
            }
            if (needProfile) {
                val merged = try {
                    if (curProfileRaw.isNullOrBlank()) vaultProfile
                    else mergeProfile(JSONObject(curProfileRaw), vaultProfile)
                } catch (_: Exception) {
                    vaultProfile
                }
                profilePrefs.edit().putString("pet_profile_json", merged.toString()).apply()
            }
        }

        // —— 模式相伴时长 ——
        val modePrefs = ctx.getSharedPreferences("vpet_mode_time", Context.MODE_PRIVATE)
        val modeRaw = modePrefs.getString("mode_seconds_json", null)
        val vaultMode = vault.optJSONObject("mode_seconds")
        if (vaultMode != null && (modeRaw.isNullOrBlank() || modeSecondsTotal(modeRaw) < 1.0) &&
            modeSecondsTotal(vaultMode.toString()) >= 1.0
        ) {
            modePrefs.edit().putString("mode_seconds_json", vaultMode.toString()).apply()
        }

        // —— 食物背包 ——
        val foodPrefs = ctx.getSharedPreferences("vpet_food_inv", Context.MODE_PRIVATE)
        val foodRaw = foodPrefs.getString("inv_json", null)
        val vaultFood = vault.optJSONObject("food_inv")
        if (vaultFood != null && (foodRaw.isNullOrBlank() || foodTotal(foodRaw) <= 0) &&
            foodTotal(vaultFood.toString()) > 0
        ) {
            foodPrefs.edit()
                .putString("inv_json", vaultFood.toString())
                .putBoolean("seeded_v1", true)
                .apply()
        }

        // —— 钱包/家园背包 ——
        val walletPrefs = ctx.getSharedPreferences("vpet_wallet", Context.MODE_PRIVATE)
        val walletRaw = walletPrefs.getString("wallet_json", null)
        val vaultWallet = vault.optJSONObject("wallet")
        if (vaultWallet != null && walletRaw.isNullOrBlank()) {
            walletPrefs.edit().putString("wallet_json", vaultWallet.toString()).apply()
        }
    }

    private fun mergeProfile(cur: JSONObject, vault: JSONObject): JSONObject {
        // 以当前为主；补回保险档里有而当前空的关键字段
        if (cur.optString("owner_name").isBlank() && vault.optString("owner_name").isNotBlank()) {
            cur.put("owner_name", vault.optString("owner_name"))
            cur.put("owner_set_at", vault.optString("owner_set_at"))
            cur.put("owner_welcome_done", vault.optBoolean("owner_welcome_done", true))
        } else if (cur.optString("owner_set_at").isBlank() &&
            vault.optString("owner_set_at").isNotBlank() &&
            cur.optString("owner_name") == vault.optString("owner_name")
        ) {
            cur.put("owner_set_at", vault.optString("owner_set_at"))
        }
        val curOutfit = cur.optJSONArray("outfit_decors")
        val vaultOutfit = vault.optJSONArray("outfit_decors")
        if ((curOutfit == null || curOutfit.length() == 0) &&
            vaultOutfit != null && vaultOutfit.length() > 0
        ) {
            cur.put("outfit_decors", vaultOutfit)
        }
        if (!cur.has("created") && vault.has("created")) cur.put("created", vault.get("created"))
        return cur
    }

    private fun ownerSetAtBlank(profileRaw: String?): Boolean {
        if (profileRaw.isNullOrBlank()) return true
        return try {
            JSONObject(profileRaw).optString("owner_set_at").isBlank()
        } catch (_: Exception) {
            true
        }
    }

    private fun modeSecondsTotal(raw: String?): Double {
        if (raw.isNullOrBlank()) return 0.0
        return try {
            val o = JSONObject(raw)
            var s = 0.0
            val it = o.keys()
            while (it.hasNext()) s += o.optDouble(it.next(), 0.0)
            s
        } catch (_: Exception) {
            0.0
        }
    }

    private fun foodTotal(raw: String?): Int {
        if (raw.isNullOrBlank()) return 0
        return try {
            val o = JSONObject(raw)
            var n = 0
            val it = o.keys()
            while (it.hasNext()) n += o.optInt(it.next(), 0)
            n
        } catch (_: Exception) {
            0
        }
    }

    private fun vaultFile(ctx: Context): File = File(ctx.filesDir, FILE)
}
