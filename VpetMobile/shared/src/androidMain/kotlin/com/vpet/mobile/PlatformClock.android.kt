package com.vpet.mobile

import android.os.SystemClock
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

actual object PlatformClock {
    private val dayFmt = SimpleDateFormat("yyyy-MM-dd", Locale.US)
    private val dateTimeFmt = SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.CHINA)

    actual fun currentTimeMillis(): Long = System.currentTimeMillis()

    actual fun elapsedRealtime(): Long = SystemClock.elapsedRealtime()

    actual fun formatDay(ms: Long): String = synchronized(dayFmt) { dayFmt.format(Date(ms)) }

    actual fun formatDateTime(ms: Long): String =
        synchronized(dateTimeFmt) { dateTimeFmt.format(Date(ms)) }
}
