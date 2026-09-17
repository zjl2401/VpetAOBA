package com.vpet.mobile

/** 跨端时钟：墙钟与单调时钟。 */
expect object PlatformClock {
    fun currentTimeMillis(): Long
    fun elapsedRealtime(): Long
    /** `yyyy-MM-dd` */
    fun formatDay(ms: Long = currentTimeMillis()): String
    /** `yyyy-MM-dd HH:mm` */
    fun formatDateTime(ms: Long = currentTimeMillis()): String
}
