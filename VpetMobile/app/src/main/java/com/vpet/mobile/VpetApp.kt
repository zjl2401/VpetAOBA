package com.vpet.mobile

import android.app.Application

class VpetApp : Application() {
    override fun onCreate() {
        super.onCreate()
        // 覆盖安装后先尝试从保险档恢复相伴/装扮/背包，再刷新快照
        PersistVault.bootstrap(this)
    }
}
