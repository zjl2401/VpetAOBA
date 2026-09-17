package com.vpet.mobile

import android.content.Context

object AndroidContextHolder {
    @Volatile
    var appContext: Context? = null

    fun require(): Context =
        appContext ?: error("Call VpetSharedInit.init(context) first")
}

object VpetSharedInit {
    fun init(context: Context) {
        AndroidContextHolder.appContext = context.applicationContext
    }
}
