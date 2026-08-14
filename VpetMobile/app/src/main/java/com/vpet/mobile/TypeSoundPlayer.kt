package com.vpet.mobile

import android.content.Context
import android.content.res.AssetFileDescriptor
import android.media.AudioAttributes
import android.media.SoundPool
import android.os.SystemClock

/**
 * 打字滴答音：对照桌面 `_play_type_sound` / `type_cache.wav`。
 */
class TypeSoundPlayer(private val context: Context) {
    companion object {
        const val TYPE_SOUND_MIN_GAP_MS = 28L
    }

    private var pool: SoundPool? = null
    private var soundId = 0
    private var lastPlay = 0L

    fun ensure() {
        if (pool != null) return
        try {
            val sp = SoundPool.Builder()
                .setMaxStreams(4)
                .setAudioAttributes(
                    AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_ASSISTANCE_SONIFICATION)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                        .build(),
                )
                .build()
            val afd: AssetFileDescriptor = context.assets.openFd("audio/type_cache.wav")
            soundId = sp.load(afd, 1)
            afd.close()
            pool = sp
        } catch (_: Exception) {
            pool = null
            soundId = 0
        }
    }

    fun tick() {
        if (!AppDataStore.soundOn(context)) return
        ensure()
        val sp = pool ?: return
        if (soundId == 0) return
        val now = SystemClock.elapsedRealtime()
        if (now - lastPlay < TYPE_SOUND_MIN_GAP_MS) return
        lastPlay = now
        try {
            val vol = AppDataStore.sfxVolumeF(context)
            sp.play(soundId, vol, vol, 1, 0, 1f)
        } catch (_: Exception) {
        }
    }

    fun release() {
        try {
            pool?.release()
        } catch (_: Exception) {
        }
        pool = null
        soundId = 0
    }
}
