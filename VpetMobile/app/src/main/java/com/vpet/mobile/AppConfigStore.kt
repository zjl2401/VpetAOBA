package com.vpet.mobile

import android.content.Context

/** 应用配置：seen_hints 等（对照 app_config.json）。 */
object AppConfigStore {
    private const val PREF = "vpet_app_config"
    private const val KEY_OP_GUIDE = "seen_operation_guide"
    private const val KEY_HINT_PREFIX = "once_hint_"

    private fun prefs(ctx: Context) = ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE)

    fun seenOperationGuide(ctx: Context): Boolean =
        prefs(ctx).getBoolean(KEY_OP_GUIDE, false)

    fun markOperationGuideSeen(ctx: Context) {
        prefs(ctx).edit().putBoolean(KEY_OP_GUIDE, true).apply()
    }

    fun seenOnceHint(ctx: Context, key: String): Boolean =
        prefs(ctx).getBoolean(KEY_HINT_PREFIX + key, false)

    fun markOnceHint(ctx: Context, key: String) {
        prefs(ctx).edit().putBoolean(KEY_HINT_PREFIX + key, true).apply()
    }
}
