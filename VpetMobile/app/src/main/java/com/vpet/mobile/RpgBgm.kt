package com.vpet.mobile

import android.content.Context
import android.content.res.AssetFileDescriptor
import android.media.MediaPlayer

/**
 * Silent Oath BGM：先播 startmusic，结束后循环 music（对照 game.py）。
 */
class RpgBgm(private val context: Context) {
    private var player: MediaPlayer? = null
    private var looping = false

    /** 开场/标题页只播 startmusic（循环）。 */
    fun playIntroOnly() {
        stop()
        playAsset("rpg/startmusic.mp3", loop = true)
    }

    fun startAdventure() {
        stop()
        playAsset("rpg/startmusic.mp3", loop = false) {
            playAsset("rpg/music.mp3", loop = true)
        }
    }

    fun stop() {
        looping = false
        try {
            player?.stop()
        } catch (_: Exception) {
        }
        try {
            player?.release()
        } catch (_: Exception) {
        }
        player = null
    }

    private fun playAsset(path: String, loop: Boolean, onComplete: (() -> Unit)? = null) {
        stop()
        looping = loop
        try {
            val afd: AssetFileDescriptor = context.assets.openFd(path)
            val mp = MediaPlayer()
            mp.setDataSource(afd.fileDescriptor, afd.startOffset, afd.length)
            afd.close()
            mp.isLooping = loop
            mp.setOnCompletionListener {
                if (!loop) {
                    onComplete?.invoke()
                }
            }
            mp.setOnErrorListener { _, _, _ ->
                if (!loop) onComplete?.invoke()
                true
            }
            mp.prepare()
            mp.start()
            player = mp
        } catch (_: Exception) {
            if (!loop) onComplete?.invoke()
        }
    }
}
