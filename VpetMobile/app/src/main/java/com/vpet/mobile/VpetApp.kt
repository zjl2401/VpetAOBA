package com.vpet.mobile

import android.app.Application

class VpetApp : Application() {
    override fun onCreate() {
        super.onCreate()
        runCatching { VpetSharedInit.init(this) }
    }
}
