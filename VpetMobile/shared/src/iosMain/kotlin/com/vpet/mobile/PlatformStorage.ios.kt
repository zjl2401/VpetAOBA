package com.vpet.mobile

import platform.Foundation.NSUserDefaults

actual class PlatformStorage actual constructor(name: String) {
    private val prefix = "vpet.$name."
    private val defaults = NSUserDefaults.standardUserDefaults

    private fun k(key: String) = prefix + key

    actual fun getString(key: String, default: String?): String? {
        val v = defaults.stringForKey(k(key))
        return v ?: default
    }

    actual fun putString(key: String, value: String?) {
        if (value == null) defaults.removeObjectForKey(k(key))
        else defaults.setObject(value, forKey = k(key))
    }

    actual fun getInt(key: String, default: Int): Int {
        if (defaults.objectForKey(k(key)) == null) return default
        return defaults.integerForKey(k(key)).toInt()
    }

    actual fun putInt(key: String, value: Int) {
        defaults.setInteger(value.toLong(), forKey = k(key))
    }

    actual fun getLong(key: String, default: Long): Long {
        if (defaults.objectForKey(k(key)) == null) return default
        return defaults.objectForKey(k(key)) as? Long ?: default
    }

    actual fun putLong(key: String, value: Long) {
        defaults.setObject(value, forKey = k(key))
    }

    actual fun getBoolean(key: String, default: Boolean): Boolean {
        if (defaults.objectForKey(k(key)) == null) return default
        return defaults.boolForKey(k(key))
    }

    actual fun putBoolean(key: String, value: Boolean) {
        defaults.setBool(value, forKey = k(key))
    }

    actual fun contains(key: String): Boolean = defaults.objectForKey(k(key)) != null

    actual fun remove(key: String) {
        defaults.removeObjectForKey(k(key))
    }
}
