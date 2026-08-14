package com.vpet.mobile

import android.content.Context
import android.content.Intent

/**
 * 全屏家园/RPG/音游/暴露等打开时收起悬浮桌宠与伴侣；
 * **采集例外**：在屏幕悬浮层直接玩，桌宠与伴侣保持可见且在下落物之上。
 */
object OverlayGate {
    fun pause(context: Context) {
        context.startService(
            Intent(context, PetOverlayService::class.java).setAction(PetOverlayService.ACTION_PAUSE),
        )
    }

    fun resume(context: Context) {
        context.startService(
            Intent(context, PetOverlayService::class.java).setAction(PetOverlayService.ACTION_RESUME),
        )
    }
}
