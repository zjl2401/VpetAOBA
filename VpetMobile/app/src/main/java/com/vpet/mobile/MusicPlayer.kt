package com.vpet.mobile

import android.content.Context
import android.media.AudioAttributes
import android.media.MediaPlayer
import android.net.Uri
import android.os.Handler
import android.os.Looper

/**
 * 音乐模式播放：仅支持本机 URI（文件选择器 / MediaStore）。
 * 无法直连网易云等云端曲库；若歌曲已下载到手机存储，可用「导入本地歌曲」选中。
 */
class MusicPlayer(private val context: Context) {
    private var player: MediaPlayer? = null
    var playing = false
        private set

    fun playUri(uri: Uri, onError: (String) -> Unit = {}, onComplete: () -> Unit = {}) {
        stop()
        try {
            val mp = MediaPlayer().apply {
                setAudioAttributes(
                    AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_MEDIA)
                        .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                        .build(),
                )
                setDataSource(context, uri)
                setOnCompletionListener {
                    playing = false
                    onComplete()
                }
                setOnErrorListener { _, what, extra ->
                    playing = false
                    onError("播放失败 ($what/$extra)")
                    true
                }
                prepare()
                isLooping = true
                start()
            }
            player = mp
            playing = true
        } catch (e: Exception) {
            playing = false
            onError(e.message ?: "无法播放")
        }
    }

    fun playAsset(assetPath: String, loop: Boolean = true, onError: (String) -> Unit = {}, onComplete: () -> Unit = {}) {
        stop()
        try {
            val afd = context.assets.openFd(assetPath)
            val mp = MediaPlayer().apply {
                setAudioAttributes(
                    AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_MEDIA)
                        .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                        .build(),
                )
                setDataSource(afd.fileDescriptor, afd.startOffset, afd.length)
                setOnCompletionListener {
                    playing = false
                    onComplete()
                }
                setOnErrorListener { _, what, extra ->
                    playing = false
                    onError("播放失败 ($what/$extra)")
                    true
                }
                prepare()
                isLooping = loop
                start()
            }
            try {
                afd.close()
            } catch (_: Exception) {
            }
            player = mp
            playing = true
        } catch (e: Exception) {
            playing = false
            onError(e.message ?: "无法播放")
        }
    }

    fun stop() {
        try {
            player?.stop()
        } catch (_: Exception) {
        }
        try {
            player?.release()
        } catch (_: Exception) {
        }
        player = null
        playing = false
    }
}

/** 日程到点检查（对齐桌面 _reminder_tick 精简版） */
class ScheduleTicker(
    private val context: Context,
    private val onDue: (String) -> Unit,
) {
    private val handler = Handler(Looper.getMainLooper())
    private var lastHm = ""
    private var job: Runnable? = null
    var active = false
        private set

    fun start() {
        if (active) return
        active = true
        schedule()
    }

    fun stop() {
        active = false
        job?.let { handler.removeCallbacks(it) }
        job = null
    }

    private fun schedule() {
        job?.let { handler.removeCallbacks(it) }
        job = Runnable {
            if (!active) return@Runnable
            val cal = java.util.Calendar.getInstance()
            val hm = "%02d:%02d".format(
                cal.get(java.util.Calendar.HOUR_OF_DAY),
                cal.get(java.util.Calendar.MINUTE),
            )
            if (hm != lastHm) {
                lastHm = hm
                PetProfileStore.dueScheduleTexts(context, hm).forEach { onDue(it) }
            }
            schedule()
        }
        handler.postDelayed(job!!, 15_000L)
    }
}
