package com.vpet.mobile

import android.content.Context

/**
 * 熄屏/锁屏桌宠：开关 + 当前应显示姿势。
 * 姿势优先级：刷视频 > 玩游戏 > 听音乐 > 睡觉（默认）。
 */
object LockScreenPetStore {
    private const val PREF = "vpet_appdata"
    private const val KEY_ENABLED = "lockscreen_pet_enabled"
    private const val KEY_POSE = "lockscreen_pet_pose"

    enum class Pose(val wire: String) {
        SLEEP("sleep"),
        VIDEO("video"),
        GAME("game"),
        MUSIC("music"),
        ;

        companion object {
            fun fromWire(s: String?): Pose = entries.firstOrNull { it.wire == s } ?: SLEEP
        }
    }

    private fun prefs(ctx: Context) =
        ctx.applicationContext.getSharedPreferences(PREF, Context.MODE_PRIVATE)

    fun enabled(ctx: Context): Boolean = prefs(ctx).getBoolean(KEY_ENABLED, true)

    fun setEnabled(ctx: Context, on: Boolean) {
        prefs(ctx).edit().putBoolean(KEY_ENABLED, on).apply()
    }

    fun pose(ctx: Context): Pose = Pose.fromWire(prefs(ctx).getString(KEY_POSE, Pose.SLEEP.wire))

    fun setPose(ctx: Context, pose: Pose) {
        prefs(ctx).edit().putString(KEY_POSE, pose.wire).apply()
    }

    /** 由 [PetModeHub] 同步：仅音乐在听时进 MUSIC，否则空闲也显示睡觉。 */
    fun resolve(
        video: Boolean,
        game: Boolean,
        music: Boolean,
        @Suppress("UNUSED_PARAMETER") quiet: Boolean,
    ): Pose = when {
        video -> Pose.VIDEO
        game -> Pose.GAME
        music -> Pose.MUSIC
        else -> Pose.SLEEP
    }
}
