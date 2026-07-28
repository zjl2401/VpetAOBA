package com.vpet.mobile

import android.content.Context

/**
 * 游戏失败附加 hurt：对照 `_play_game_fail_voice`。
 * 不挡结算画面；忽略冷却；暴露失败建议无字幕（由调用方控制 UI）。
 */
object GameFailVoice {
    fun playHurt(ctx: Context) {
        if (!AppDataStore.soundOn(ctx)) return
        try {
            val vp = VoicePlayer(ctx)
            vp.playCategory("hurt", force = true) {
                vp.stop()
            }
        } catch (_: Exception) {
        }
    }
}
