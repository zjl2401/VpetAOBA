package com.vpet.mobile

import android.app.Application

/** 手机版应用入口。 */
class VpetApp : Application() {
    override fun onCreate() {
        super.onCreate()
        // 保险档会在首次访问存档时恢复；此处不执行磁盘 I/O，保证进程可尽快进入首屏。
    }
}
