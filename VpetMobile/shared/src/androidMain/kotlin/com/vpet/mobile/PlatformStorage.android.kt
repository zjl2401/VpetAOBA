package com.vpet.mobile

import android.content.Context

actual class PlatformStorage actual constructor(name: String) {
    private val prefs =
        AndroidContextHolder.require().getSharedPreferences(name, Context.MODE_PRIVATE)

    actual fun getString(key: String, default: String?): String? =
        prefs.getString(key, default)

    actual fun putString(key: String, value: String?) {
        prefs.edit().putString(key, value).apply()
    }

    actual fun getInt(key: String, default: Int): Int = prefs.getInt(key, default)

    actual fun putInt(key: String, value: Int) {
        prefs.edit().putInt(key, value).apply()
    }

    actual fun getLong(key: String, default: Long): Long = prefs.getLong(key, default)

    actual fun putLong(key: String, value: Long) {
        prefs.edit().putLong(key, value).apply()
    }

    actual fun getBoolean(key: String, default: Boolean): Boolean =
        prefs.getBoolean(key, default)

    actual fun putBoolean(key: String, value: Boolean) {
        prefs.edit().putBoolean(key, value).apply()
    }

    actual fun contains(key: String): Boolean = prefs.contains(key)

    actual fun remove(key: String) {
        prefs.edit().remove(key).apply()
    }
}
