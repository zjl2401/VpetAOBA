package com.vpet.mobile

import platform.Foundation.NSDate
import platform.Foundation.NSDateFormatter
import platform.Foundation.NSLocale
import platform.Foundation.NSTimeZone
import platform.Foundation.dateWithTimeIntervalSince1970
import platform.Foundation.timeIntervalSince1970
import platform.Foundation.localTimeZone

actual object PlatformClock {
    private fun formatter(pattern: String, localeId: String): NSDateFormatter {
        val f = NSDateFormatter()
        f.dateFormat = pattern
        f.locale = NSLocale(localeIdentifier = localeId)
        f.timeZone = NSTimeZone.localTimeZone
        return f
    }

    actual fun currentTimeMillis(): Long =
        (NSDate().timeIntervalSince1970 * 1000.0).toLong()

    actual fun elapsedRealtime(): Long = currentTimeMillis()

    actual fun formatDay(ms: Long): String {
        val date = NSDate.dateWithTimeIntervalSince1970(ms / 1000.0)
        return formatter("yyyy-MM-dd", "en_US").stringFromDate(date)
    }

    actual fun formatDateTime(ms: Long): String {
        val date = NSDate.dateWithTimeIntervalSince1970(ms / 1000.0)
        return formatter("yyyy-MM-dd HH:mm", "zh_CN").stringFromDate(date)
    }
}
