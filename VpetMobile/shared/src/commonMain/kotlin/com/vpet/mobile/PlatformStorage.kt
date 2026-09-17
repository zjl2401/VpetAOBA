package com.vpet.mobile

/**
 * 跨端 KV 存档（Android SharedPreferences / iOS UserDefaults）。
 * [name] 对应原 Android prefs 名，保持双端键兼容。
 */
expect class PlatformStorage(name: String) {
    fun getString(key: String, default: String? = null): String?
    fun putString(key: String, value: String?)
    fun getInt(key: String, default: Int = 0): Int
    fun putInt(key: String, value: Int)
    fun getLong(key: String, default: Long = 0L): Long
    fun putLong(key: String, value: Long)
    fun getBoolean(key: String, default: Boolean = false): Boolean
    fun putBoolean(key: String, value: Boolean)
    fun contains(key: String): Boolean
    fun remove(key: String)
}
