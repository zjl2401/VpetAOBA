package com.vpet.mobile

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioManager
import android.media.AudioPlaybackConfiguration
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.Process

/**
 * 检测「音乐 App」是否在播。
 *
 * 严格策略：必须能解析到客户端包名，且命中音乐白名单；
 * 视频/短视频/浏览器等黑名单一律忽略。
 * 不再单凭 CONTENT_TYPE_MUSIC 判断（B站/油管等常误标成 MUSIC）。
 */
class AmbientMusicMonitor(
    context: Context,
    private val onChanged: (active: Boolean, signature: String) -> Unit,
    private val onVideoChanged: ((active: Boolean) -> Unit)? = null,
) {
    private val app = context.applicationContext
    private val am = app.getSystemService(Context.AUDIO_SERVICE) as? AudioManager
    private val handler = Handler(Looper.getMainLooper())
    private var running = false
    private var lastActive: Boolean? = null
    private var lastSignature: String = ""
    private var lastVideo: Boolean? = null
    private var pendingActiveSince = 0L
    private var playbackCb: AudioManager.AudioPlaybackCallback? = null
    private val poll = object : Runnable {
        override fun run() {
            if (!running) return
            emit(probeDetailed())
            emitVideo(isVideoActive(app))
            handler.postDelayed(this, POLL_MS)
        }
    }

    fun start() {
        if (running) return
        running = true
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && am != null) {
            val cb = object : AudioManager.AudioPlaybackCallback() {
                override fun onPlaybackConfigChanged(configs: MutableList<AudioPlaybackConfiguration>?) {
                    handler.post {
                        if (running) {
                            emit(probeDetailed())
                            emitVideo(isVideoActive(app))
                        }
                    }
                }
            }
            playbackCb = cb
            try {
                am.registerAudioPlaybackCallback(cb, handler)
            } catch (_: Exception) {
                playbackCb = null
            }
        }
        emit(probeDetailed())
        emitVideo(isVideoActive(app))
        handler.postDelayed(poll, POLL_MS)
    }

    fun stop() {
        running = false
        handler.removeCallbacks(poll)
        val cb = playbackCb
        if (cb != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            try {
                am?.unregisterAudioPlaybackCallback(cb)
            } catch (_: Exception) {
            }
        }
        playbackCb = null
        lastActive = null
        lastSignature = ""
        lastVideo = null
        pendingActiveSince = 0L
    }

    fun probe(): Boolean = probeDetailed().first

    private fun emitVideo(active: Boolean) {
        if (lastVideo == active) return
        lastVideo = active
        onVideoChanged?.invoke(active)
    }

    private fun emit(result: Pair<Boolean, String>) {
        val (rawActive, signature) = result
        val now = android.os.SystemClock.elapsedRealtime()
        val active = if (rawActive) {
            if (pendingActiveSince <= 0L) pendingActiveSince = now
            now - pendingActiveSince >= DEBOUNCE_ON_MS
        } else {
            pendingActiveSince = 0L
            false
        }
        val changed = lastActive != active || (active && signature != lastSignature)
        if (!changed) return
        lastActive = active
        lastSignature = signature
        onChanged(active, signature)
    }

    companion object {
        private const val POLL_MS = 2000L
        private const val DEBOUNCE_ON_MS = 1800L

        /** 常见音乐客户端（含系统播放器）。 */
        private val MUSIC_PACKAGES = setOf(
            "com.netease.cloudmusic",
            "com.netease.cloudmusic.lite",
            "com.kugou.android",
            "com.kugou.android.lite",
            "com.tencent.qqmusic",
            "com.tencent.qqmusiclite",
            "com.spotify.music",
            "com.google.android.apps.youtube.music",
            "com.apple.android.music",
            "com.luna.music",
            "cn.kuwo.player",
            "com.miui.player",
            "com.android.music",
            "com.sec.android.app.music",
            "com.huawei.music",
            "com.oppo.music",
            "com.oneplus.music",
            "com.realme.music",
            "com.amazon.mp3",
            "deezer.android.app",
            "com.aspiro.tidal",
            "cmccwm.mobilemusic",
            "com.hiby.music",
            "com.blueocean.musicplayer",
            "com.rhapsody",
            "com.soundcloud.android",
            "com.bandcamp.android",
            "com.ximalaya.ting.android",
        )

        /**
         * 视频 / 短视频 / 浏览器：即使标成 CONTENT_TYPE_MUSIC 也不进音乐模式。
         * 用前缀匹配（tv.danmaku.bili / com.bilibili.app.in 等）。
         */
        private val VIDEO_PACKAGE_PREFIXES = listOf(
            "com.google.android.youtube",
            "com.google.android.apps.youtube.kids",
            "com.google.android.apps.youtube.unplugged",
            "tv.danmaku.bili",
            "com.bilibili",
            "com.bilibili.app",
            "com.qiyi.video",
            "com.qiyi.video.pad",
            "com.tencent.qqlive",
            "com.youku.phone",
            "com.hunantv.imgo.activity",
            "com.cmcc.cmvideo",
            "com.ss.android.ugc.aweme",
            "com.ss.android.ugc.live",
            "com.ss.android.article.video",
            "com.smile.gifmaker",
            "com.kuaishou.nebula",
            "com.ss.android.ugc.aweme.lite",
            "com.ss.android.ugc.aweme.mobile",
            "com.dragon.read",
            "com.baidu.haokan",
            "com.mxtech.videoplayer",
            "org.videolan.vlc",
            "com.android.chrome",
            "com.chrome.beta",
            "com.chrome.dev",
            "com.microsoft.emmx",
            "org.mozilla.firefox",
            "com.opera.browser",
            "com.sec.android.app.sbrowser",
            "com.huawei.browser",
            "com.mi.globalbrowser",
            "com.uc.browser",
            "mark.via",
            "com.android.browser",
            "com.tencent.mtt",
            "tv.acfund.bilibilihd",
            "com.sohu.sohuvideo",
            "com.letv.android.client",
            "com.pptv.android",
            "com.duowan.kiwi",
            "air.tv.douyu.android",
            "com.douyu.live",
            "com.huya.nemo",
            "com.tencent.now",
            "com.ss.android.ugc.live",
            "com.phoenix.read",
            "com.lemon.lv",
            "com.ss.android.ugc.aweme",
        )

        fun isMediaActive(context: Context): Boolean = probeDetailed(context).first

        /** 视频/短视频客户端是否在播（桌宠避让屏幕中央用）。 */
        fun isVideoActive(context: Context): Boolean = probeVideoDetailed(context).first

        fun probeVideoDetailed(context: Context): Pair<Boolean, String> {
            val appCtx = context.applicationContext
            val mgr = appCtx.getSystemService(Context.AUDIO_SERVICE) as? AudioManager
                ?: return false to ""
            if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) return false to ""
            val myUid = Process.myUid()
            return try {
                val hits = mutableListOf<String>()
                for (cfg in mgr.activePlaybackConfigurations) {
                    val pkg = videoPackageOf(appCtx, cfg, myUid) ?: continue
                    hits += pkg
                }
                (hits.isNotEmpty()) to hits.distinct().sorted().joinToString("|")
            } catch (_: Exception) {
                false to ""
            }
        }

        fun probeDetailed(context: Context): Pair<Boolean, String> {
            val appCtx = context.applicationContext
            val mgr = appCtx.getSystemService(Context.AUDIO_SERVICE) as? AudioManager
                ?: return false to ""
            if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return false to ""
            // API 29 以下拿不到 clientUid，无法区分视频/音乐 → 不自动进模式
            if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) return false to ""
            val myUid = Process.myUid()
            return try {
                val hits = mutableListOf<String>()
                for (cfg in mgr.activePlaybackConfigurations) {
                    val pkg = musicPackageOf(appCtx, cfg, myUid) ?: continue
                    val uid = clientUidOf(cfg)
                    val pid = playerIdOf(cfg)
                    hits += "$pkg:$uid:$pid"
                }
                (hits.isNotEmpty()) to hits.sorted().joinToString("|")
            } catch (_: Exception) {
                false to ""
            }
        }

        private fun clientUidOf(cfg: AudioPlaybackConfiguration): Int {
            if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) return -1
            return try {
                val m = AudioPlaybackConfiguration::class.java.getMethod("getClientUid")
                m.invoke(cfg) as Int
            } catch (_: Exception) {
                -1
            }
        }

        private fun playerIdOf(cfg: AudioPlaybackConfiguration): Int {
            return try {
                val m = AudioPlaybackConfiguration::class.java.getMethod("getPlayerInterfaceId")
                m.invoke(cfg) as Int
            } catch (_: Exception) {
                0
            }
        }

        /** 命中音乐白名单则返回包名，否则 null。 */
        private fun musicPackageOf(
            context: Context,
            cfg: AudioPlaybackConfiguration,
            myUid: Int,
        ): String? {
            val attrs = cfg.audioAttributes ?: return null
            if (attrs.usage != AudioAttributes.USAGE_MEDIA) return null
            when (attrs.contentType) {
                AudioAttributes.CONTENT_TYPE_MOVIE,
                AudioAttributes.CONTENT_TYPE_SPEECH,
                AudioAttributes.CONTENT_TYPE_SONIFICATION,
                -> return null
            }
            val clientUid = clientUidOf(cfg)
            if (clientUid < 0 || clientUid == myUid) return null
            val pkgs = packagesForUid(context, clientUid)
            if (pkgs.isEmpty()) return null
            if (pkgs.any { isVideoPackage(it) }) return null
            return pkgs.firstOrNull { it in MUSIC_PACKAGES }
        }

        private fun videoPackageOf(
            context: Context,
            cfg: AudioPlaybackConfiguration,
            myUid: Int,
        ): String? {
            val attrs = cfg.audioAttributes ?: return null
            if (attrs.usage != AudioAttributes.USAGE_MEDIA &&
                attrs.usage != AudioAttributes.USAGE_GAME
            ) {
                return null
            }
            val clientUid = clientUidOf(cfg)
            if (clientUid < 0 || clientUid == myUid) return null
            val pkgs = packagesForUid(context, clientUid)
            if (pkgs.isEmpty()) return null
            // 纯音乐白名单客户端不当视频
            if (pkgs.any { it in MUSIC_PACKAGES && !isVideoPackage(it) }) return null
            if (attrs.contentType == AudioAttributes.CONTENT_TYPE_MOVIE) {
                return pkgs.firstOrNull()
            }
            return pkgs.firstOrNull { isVideoPackage(it) }
        }

        private fun packagesForUid(context: Context, uid: Int): List<String> = try {
            context.packageManager.getPackagesForUid(uid)?.toList().orEmpty()
        } catch (_: Exception) {
            emptyList()
        }

        private fun isVideoPackage(pkg: String): Boolean {
            if (pkg in MUSIC_PACKAGES) return false
            return VIDEO_PACKAGE_PREFIXES.any { prefix ->
                pkg == prefix || pkg.startsWith("$prefix.")
            }
        }
    }

    private fun probeDetailed(): Pair<Boolean, String> = probeDetailed(app)
}
