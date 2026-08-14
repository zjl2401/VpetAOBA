package com.vpet.mobile

import android.app.AppOpsManager
import android.app.usage.UsageEvents
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.Intent
import android.content.pm.ApplicationInfo
import android.media.AudioAttributes
import android.media.AudioManager
import android.media.AudioPlaybackConfiguration
import android.media.MediaMetadata
import android.media.session.MediaSessionManager
import android.os.Build
import android.os.Process
import android.provider.Settings

/** 前台/播音场景：音乐 / 视频 / 游戏。 */
enum class AppScene {
    NONE, MUSIC, VIDEO, GAME
}

/**
 * 包名分类 + 使用情况访问（可选）+ 音频回落。
 * 优先「正在用的 App」，无权限时回落音频白名单（对照 AmbientMusicMonitor）。
 */
object AppSceneClassifier {
    val MUSIC_PACKAGES = setOf(
        "com.netease.cloudmusic", "com.netease.cloudmusic.lite",
        "com.kugou.android", "com.kugou.android.lite",
        "com.tencent.qqmusic", "com.tencent.qqmusiclite",
        "com.spotify.music", "com.google.android.apps.youtube.music",
        "com.apple.android.music", "com.luna.music", "cn.kuwo.player",
        "com.miui.player", "com.android.music", "com.sec.android.app.music",
        "com.huawei.music", "com.oppo.music", "com.oneplus.music",
        "com.realme.music", "com.amazon.mp3", "deezer.android.app",
        "com.aspiro.tidal", "cmccwm.mobilemusic", "com.hiby.music",
        "com.blueocean.musicplayer", "com.rhapsody", "com.soundcloud.android",
        "com.bandcamp.android", "com.ximalaya.ting.android",
        "com.tencent.qqmusicpad", "com.netease.cloudmusic.iot",
        "com.kugou.android.ringtone", "com.tencent.karaoke",
        "cn.toside.music.mobile", "com.all.music.download",
    )

    /** 前缀匹配（对照 AmbientMusicMonitor）：`tv.danmaku.bili` 也能命中 `tv.danmaku.bilibilihd`。 */
    val VIDEO_PREFIXES = listOf(
        "com.google.android.youtube", "com.google.android.apps.youtube.kids",
        "com.google.android.apps.youtube.unplugged",
        "tv.danmaku.bili", "tv.danmaku.bilibilihd", "com.bilibili",
        "com.qiyi.video", "com.tencent.qqlive", "com.youku.phone",
        "com.hunantv.imgo.activity", "com.cmcc.cmvideo",
        "com.ss.android.ugc.aweme", "com.ss.android.ugc.live",
        "com.ss.android.article.video", "com.smile.gifmaker", "com.kuaishou",
        "com.mxtech.videoplayer", "org.videolan.vlc", "tv.acfun.bilibilihd",
        "com.sohu.sohuvideo", "air.tv.douyu.android", "com.douyu.live",
        "com.huya.nemo", "com.tencent.now", "com.lemon.lv",
        "com.dragon.read", "com.baidu.haokan", "com.duowan.kiwi",
        "com.letv.android.client", "com.pptv.android",
        "com.ss.android.ugc.aweme.lite", "com.ss.android.ugc.aweme.mobile",
        "com.kuaishou.nebula", "com.qiyi.video.pad",
    )

    val GAME_PREFIXES = listOf(
        "com.tencent.tmgp", "com.tencent.tmgp.",
        "com.miHoYo", "com.mihoyo", "com.hypergryph", "com.kurogame",
        "com.sunborn", "com.yostar", "com.papegames", "com.nexon",
        "com.netease.cloudgame", "com.netease.dwrg", "com.netease.l22",
        "com.netease.mc", "com.netease.onmyoji", "com.netease.party",
        "com.netease.moba", "com.netease.hyxd", "com.netease.nshm",
        "com.netease.g67", "com.netease.yyslgrl", "com.netease.eve.mobile",
        "com.supercell", "com.activision", "com.riotgames", "com.epicgames",
        "com.valve", "com.nintendo", "com.ea.", "com.gameloft",
        "com.kiloo", "com.mojang", "com.roblox", "com.blizzard",
        "com.mobile.legends", "com.garena", "com.vng.", "com.proximabeta",
        "com.dragonest", "com.happyelements", "com.ourpalm",
        "com.tencent.lolm", "com.tencent.jkchess", "com.tencent.nfsonline",
        "com.tencent.tmgp.sgame", "com.tencent.tmgp.pubgmhd",
        "com.tencent.wegame", "com.tencent.af", "com.tencent.shootgame",
        "com.tencent.mf.uam", "com.tencent.jkchess",
        "com.ShiningNikkiCN", "com.papegames.nn4.cn",
        "com.bilibili.priconne", "com.bilibili.deadcells.mobile",
    )

    private val IGNORE_FG_PACKAGES = setOf(
        "com.android.systemui",
        "com.android.permissioncontroller",
        "com.google.android.permissioncontroller",
        "com.android.settings",
        "com.miui.securitycenter",
        "com.huawei.systemmanager",
        "com.coloros.safecenter",
        "com.oplus.safecenter",
    )

    fun classifyPackage(pkg: String?): AppScene {
        if (pkg.isNullOrBlank()) return AppScene.NONE
        if (pkg in MUSIC_PACKAGES) return AppScene.MUSIC
        if (isVideoPackage(pkg)) return AppScene.VIDEO
        if (isGamePackage(pkg)) return AppScene.GAME
        return AppScene.NONE
    }

    /** 白名单 + 系统 category 兜底（大量手游不在前缀表里）。 */
    fun classifyPackage(ctx: Context, pkg: String?): AppScene {
        val base = classifyPackage(pkg)
        if (base != AppScene.NONE) return base
        return categoryScene(ctx, pkg)
    }

    fun categoryScene(ctx: Context, pkg: String?): AppScene {
        if (pkg.isNullOrBlank()) return AppScene.NONE
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return AppScene.NONE
        return try {
            val ai = ctx.packageManager.getApplicationInfo(pkg, 0)
            when (ai.category) {
                ApplicationInfo.CATEGORY_GAME -> AppScene.GAME
                ApplicationInfo.CATEGORY_AUDIO -> AppScene.MUSIC
                ApplicationInfo.CATEGORY_VIDEO -> AppScene.VIDEO
                else -> AppScene.NONE
            }
        } catch (_: Exception) {
            AppScene.NONE
        }
    }

    fun isVideoPackage(pkg: String): Boolean {
        if (pkg in MUSIC_PACKAGES) return false
        // 前缀即可：bili → bilibilihd；aweme → aweme.lite
        return VIDEO_PREFIXES.any { pkg == it || pkg.startsWith(it) }
    }

    fun isGamePackage(pkg: String): Boolean {
        if (pkg in MUSIC_PACKAGES || isVideoPackage(pkg)) return false
        return GAME_PREFIXES.any { prefix ->
            pkg == prefix.trimEnd('.') || pkg.startsWith(prefix)
        }
    }

    fun isGameLike(ctx: Context, pkg: String): Boolean =
        isGamePackage(pkg) || categoryScene(ctx, pkg) == AppScene.GAME

    fun hasUsageAccess(ctx: Context): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.LOLLIPOP) return false
        return try {
            val appOps = ctx.getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
            val mode = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                appOps.unsafeCheckOpNoThrow(
                    AppOpsManager.OPSTR_GET_USAGE_STATS,
                    Process.myUid(),
                    ctx.packageName,
                )
            } else {
                @Suppress("DEPRECATION")
                appOps.checkOpNoThrow(
                    AppOpsManager.OPSTR_GET_USAGE_STATS,
                    Process.myUid(),
                    ctx.packageName,
                )
            }
            mode == AppOpsManager.MODE_ALLOWED
        } catch (_: Exception) {
            false
        }
    }

    fun openUsageAccessSettings(ctx: Context) {
        try {
            ctx.startActivity(
                Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
            )
        } catch (_: Exception) {
            try {
                ctx.startActivity(
                    Intent(Settings.ACTION_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
                )
            } catch (_: Exception) {
            }
        }
    }

    fun foregroundPackage(ctx: Context): String? {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.LOLLIPOP) return null
        if (!hasUsageAccess(ctx)) return null
        return try {
            val usm = ctx.getSystemService(Context.USAGE_STATS_SERVICE) as? UsageStatsManager
                ?: return null
            val self = ctx.packageName
            val end = System.currentTimeMillis()
            // 拉长事件窗：部分国产 ROM 事件稀疏，15s 统计窗经常空
            val byEvents = foregroundFromEvents(usm, self, end - 5 * 60_000L, end)
            if (!byEvents.isNullOrBlank()) return byEvents
            val begin = end - 120_000L
            val list = usm.queryUsageStats(UsageStatsManager.INTERVAL_BEST, begin, end)
                ?: usm.queryUsageStats(UsageStatsManager.INTERVAL_DAILY, begin, end)
                ?: return null
            list
                .asSequence()
                .filter { pkg ->
                    val p = pkg.packageName
                    !p.isNullOrBlank() && p != self && !shouldIgnoreForeground(p)
                }
                .maxByOrNull { it.lastTimeUsed }
                ?.packageName
        } catch (_: Exception) {
            null
        }
    }

    private fun shouldIgnoreForeground(pkg: String): Boolean {
        if (pkg in IGNORE_FG_PACKAGES) return true
        if (pkg.endsWith(".launcher") || pkg.contains(".launcher.")) return true
        if (pkg.startsWith("com.android.launcher")) return true
        return false
    }

    private fun foregroundFromEvents(
        usm: UsageStatsManager,
        selfPkg: String,
        begin: Long,
        end: Long,
    ): String? {
        return try {
            val events = usm.queryEvents(begin, end) ?: return null
            val ev = UsageEvents.Event()
            var lastFg: String? = null
            while (events.hasNextEvent()) {
                events.getNextEvent(ev)
                val type = ev.eventType
                val resume = type == UsageEvents.Event.MOVE_TO_FOREGROUND ||
                    (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q &&
                        type == UsageEvents.Event.ACTIVITY_RESUMED)
                if (!resume) continue
                val pkg = ev.packageName ?: continue
                if (pkg.isBlank() || pkg == selfPkg || shouldIgnoreForeground(pkg)) continue
                lastFg = pkg
            }
            lastFg
        } catch (_: Exception) {
            null
        }
    }
}

/**
 * 综合前台 App + 音频，回调当前场景。
 * 优先级：前台分类 > 音频视频 > 音频游戏 > 音频音乐。
 */
class AppSceneMonitor(
    context: Context,
    private val onScene: (scene: AppScene, signature: String) -> Unit,
) {
    private val app = context.applicationContext
    private val am = app.getSystemService(Context.AUDIO_SERVICE) as? AudioManager
    private val handler = android.os.Handler(android.os.Looper.getMainLooper())
    private var running = false
    private var lastScene: AppScene? = null
    private var lastSig = ""
    private var pendingMusicSince = 0L
    /** 粘住：同包名仍在前台/仍在播，或短暂失焦，都不立刻 NONE。 */
    private var stickyScene: AppScene = AppScene.NONE
    private var stickyPkg: String = ""
    private var missCount = 0
    private var playbackCb: AudioManager.AudioPlaybackCallback? = null
    private val poll = object : Runnable {
        override fun run() {
            if (!running) return
            emit(probe())
            handler.postDelayed(this, POLL_MS)
        }
    }

    fun start() {
        if (running) return
        running = true
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && am != null) {
            val cb = object : AudioManager.AudioPlaybackCallback() {
                override fun onPlaybackConfigChanged(configs: MutableList<AudioPlaybackConfiguration>?) {
                    handler.post { if (running) emit(probe()) }
                }
            }
            playbackCb = cb
            try {
                am.registerAudioPlaybackCallback(cb, handler)
            } catch (_: Exception) {
                playbackCb = null
            }
        }
        emit(probe())
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
        lastScene = null
        lastSig = ""
        pendingMusicSince = 0L
        stickyScene = AppScene.NONE
        stickyPkg = ""
        missCount = 0
    }

    private fun emit(result: Pair<AppScene, String>) {
        val stabilized = stabilize(result)
        val (scene, sig) = stabilized
        val now = android.os.SystemClock.elapsedRealtime()
        if (scene == AppScene.MUSIC) {
            if (pendingMusicSince <= 0L) pendingMusicSince = now
            // 防抖：短暂波动不回调；切勿改成 NONE，否则会永远进不了音乐
            if (now - pendingMusicSince < DEBOUNCE_MUSIC_MS) {
                return
            }
        } else {
            pendingMusicSince = 0L
        }
        if (scene == lastScene && sig == lastSig) return
        lastScene = scene
        lastSig = sig
        onScene(scene, sig)
    }

    /**
     * 页面/App 不关就保持场景：
     * - 同包名前台（含桌宠自己抢前台）
     * - 或该包仍在播音
     * - 切走后连续 miss 才发 NONE
     */
    private fun stabilize(raw: Pair<AppScene, String>): Pair<AppScene, String> {
        var (scene, sig) = raw
        val self = app.packageName
        val fg = AppSceneClassifier.foregroundPackage(app)
        val pkg = scenePkg(scene, sig, fg)

        if (scene != AppScene.NONE) {
            missCount = 0
            stickyScene = scene
            if (pkg.isNotBlank()) stickyPkg = pkg
            return scene to sig
        }

        // 已无活动场景
        if (stickyScene == AppScene.NONE || stickyPkg.isBlank()) {
            missCount = 0
            return AppScene.NONE to ""
        }

        // 仅当「确实」检测到前台是桌宠自己时才粘住（打开菜单不退姿势）。
        // 切勿把 fg==null（未授权使用情况访问）当成 self，否则视频/音乐姿势永远退不掉。
        val fgSelf = !fg.isNullOrBlank() && fg == self
        val fgSticky = !fg.isNullOrBlank() && fg == stickyPkg
        val audioSticky = packageStillAudible(stickyPkg)
        if (fgSticky || fgSelf || audioSticky) {
            missCount = 0
            // 仍粘住：刷新签名（切歌换色），不发 NONE
            val keepSig = when (stickyScene) {
                AppScene.MUSIC -> musicTrackSignature(preferPkg = stickyPkg).ifBlank { stickyPkg }
                else -> stickyPkg
            }
            return stickyScene to keepSig
        }

        missCount += 1
        if (missCount < MISS_EXIT) {
            val keepSig = when (stickyScene) {
                AppScene.MUSIC -> musicTrackSignature(preferPkg = stickyPkg).ifBlank { lastSig.ifBlank { stickyPkg } }
                else -> lastSig.ifBlank { stickyPkg }
            }
            return stickyScene to keepSig
        }
        stickyScene = AppScene.NONE
        stickyPkg = ""
        missCount = 0
        return AppScene.NONE to ""
    }

    private fun scenePkg(scene: AppScene, sig: String, fg: String?): String {
        if (scene == AppScene.NONE) return ""
        val fromSig = sig.substringBefore('|').trim()
        if (fromSig.isNotBlank() && '.' in fromSig) return fromSig
        if (!fg.isNullOrBlank() && fg != app.packageName) return fg
        return fromSig
    }

    private fun packageStillAudible(pkg: String): Boolean {
        if (pkg.isBlank() || Build.VERSION.SDK_INT < Build.VERSION_CODES.Q || am == null) return false
        val myUid = Process.myUid()
        return try {
            am.activePlaybackConfigurations.any { cfg ->
                val uid = clientUid(cfg)
                if (uid < 0 || uid == myUid) return@any false
                packagesForUid(uid).any { it == pkg }
            }
        } catch (_: Exception) {
            false
        }
    }

    private fun probe(): Pair<AppScene, String> {
        val self = app.packageName
        val fg = AppSceneClassifier.foregroundPackage(app)
        if (!fg.isNullOrBlank() && fg != self) {
            when (val byFg = AppSceneClassifier.classifyPackage(app, fg)) {
                AppScene.MUSIC ->
                    // 前台已是音乐 App：与视频/游戏一致，打开即可切姿势（不必等解码回调）
                    return AppScene.MUSIC to musicTrackSignature(preferPkg = fg)
                AppScene.VIDEO, AppScene.GAME ->
                    return byFg to fg
                AppScene.NONE -> Unit
            }
        }
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q || am == null) {
            // API29 以下无 clientUid：只能靠使用情况访问认前台包
            return AppScene.NONE to ""
        }
        // 无使用情况访问时：只要视频/音乐 App 在播也能进（打开未播仍需授权）
        if (fg.isNullOrBlank()) {
            val videoHit = AmbientMusicMonitor.probeVideoDetailed(app)
            if (videoHit.first) {
                val pkg = videoHit.second.substringBefore('|').ifBlank { videoHit.second }
                return AppScene.VIDEO to pkg.ifBlank { "video" }
            }
            val musicHit = AmbientMusicMonitor.probeDetailed(app)
            if (musicHit.first) {
                val pkg = musicHit.second.substringBefore(':').ifBlank { "music" }
                return AppScene.MUSIC to musicTrackSignature(preferPkg = pkg)
            }
        }
        val myUid = Process.myUid()
        var video: String? = null
        var game: String? = null
        var music: String? = null
        try {
            for (cfg in am.activePlaybackConfigurations) {
                val uid = clientUid(cfg)
                if (uid < 0 || uid == myUid) continue
                val pkgs = packagesForUid(uid)
                if (pkgs.isEmpty()) continue
                val attrs = cfg.audioAttributes ?: continue
                val pkg = pkgs.firstOrNull() ?: continue
                when {
                    // 短视频/B 站常标 MUSIC 而非 MOVIE：包名命中即视频
                    pkgs.any { AppSceneClassifier.isVideoPackage(it) } ||
                        attrs.contentType == AudioAttributes.CONTENT_TYPE_MOVIE ->
                        if (video == null) {
                            video = pkgs.firstOrNull { AppSceneClassifier.isVideoPackage(it) } ?: pkg
                        }
                    // 手游多为 USAGE_MEDIA：白名单或系统 CATEGORY_GAME 都算游戏
                    pkgs.any { AppSceneClassifier.isGameLike(app, it) } ||
                        attrs.usage == AudioAttributes.USAGE_GAME ->
                        if (game == null) {
                            game = pkgs.firstOrNull { AppSceneClassifier.isGameLike(app, it) } ?: pkg
                        }
                    attrs.usage == AudioAttributes.USAGE_MEDIA &&
                        attrs.contentType != AudioAttributes.CONTENT_TYPE_SPEECH &&
                        attrs.contentType != AudioAttributes.CONTENT_TYPE_SONIFICATION &&
                        (
                            pkgs.any { it in AppSceneClassifier.MUSIC_PACKAGES } ||
                                pkgs.any {
                                    AppSceneClassifier.categoryScene(app, it) == AppScene.MUSIC
                                }
                            ) &&
                        pkgs.none { AppSceneClassifier.isVideoPackage(it) } ->
                        if (music == null) {
                            music = pkgs.firstOrNull { it in AppSceneClassifier.MUSIC_PACKAGES }
                                ?: pkgs.firstOrNull {
                                    AppSceneClassifier.categoryScene(app, it) == AppScene.MUSIC
                                }
                        }
                }
            }
        } catch (_: Exception) {
            return AppScene.NONE to ""
        }
        // 前台是游戏/音乐时，不被后台残留视频音频盖住
        if (!fg.isNullOrBlank() && fg != self) {
            when (AppSceneClassifier.classifyPackage(app, fg)) {
                AppScene.GAME -> if (game != null || video == null) return AppScene.GAME to fg
                AppScene.MUSIC -> if (music != null || video == null) {
                    return AppScene.MUSIC to musicTrackSignature(preferPkg = fg)
                }
                else -> Unit
            }
        }
        return when {
            video != null -> AppScene.VIDEO to video
            game != null -> AppScene.GAME to game
            music != null -> AppScene.MUSIC to musicTrackSignature(preferPkg = music)
            else -> AppScene.NONE to ""
        }
    }

    /**
     * 用于「切歌换色」的签名。
     * 有通知使用权时可读 MediaSession 曲名；否则用播放器实例 id（部分 App 切歌会变）。
     */
    private fun musicTrackSignature(preferPkg: String?): String {
        val meta = mediaSessionTrackSig(preferPkg)
        if (!meta.isNullOrBlank()) return meta
        val players = musicPlayerHits(preferPkg)
        if (players.isNotBlank()) {
            return if (preferPkg.isNullOrBlank()) players else "$preferPkg|$players"
        }
        return preferPkg.orEmpty()
    }

    private fun mediaSessionTrackSig(preferPkg: String?): String? {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.LOLLIPOP) return null
        return try {
            val msm = app.getSystemService(Context.MEDIA_SESSION_SERVICE) as? MediaSessionManager
                ?: return null
            @Suppress("DEPRECATION")
            val controllers = msm.getActiveSessions(null)
            for (c in controllers) {
                val pkg = c.packageName ?: continue
                val musicLike = pkg in AppSceneClassifier.MUSIC_PACKAGES ||
                    AppSceneClassifier.categoryScene(app, pkg) == AppScene.MUSIC
                if (!musicLike) continue
                if (!preferPkg.isNullOrBlank() && pkg != preferPkg) continue
                val md = c.metadata ?: continue
                val title = md.getString(MediaMetadata.METADATA_KEY_TITLE).orEmpty()
                val artist = md.getString(MediaMetadata.METADATA_KEY_ARTIST).orEmpty()
                val id = md.getString(MediaMetadata.METADATA_KEY_MEDIA_ID).orEmpty()
                if (title.isBlank() && id.isBlank()) continue
                return listOf(pkg, title, artist, id).joinToString("|")
            }
            null
        } catch (_: SecurityException) {
            null
        } catch (_: Exception) {
            null
        }
    }

    private fun musicPlayerHits(preferPkg: String?): String {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q || am == null) return ""
        val myUid = Process.myUid()
        val hits = mutableListOf<String>()
        try {
            for (cfg in am.activePlaybackConfigurations) {
                val uid = clientUid(cfg)
                if (uid < 0 || uid == myUid) continue
                val pkgs = packagesForUid(uid)
                val pkg = pkgs.firstOrNull {
                    it in AppSceneClassifier.MUSIC_PACKAGES ||
                        AppSceneClassifier.categoryScene(app, it) == AppScene.MUSIC
                } ?: continue
                if (!preferPkg.isNullOrBlank() && pkg != preferPkg) continue
                val attrs = cfg.audioAttributes ?: continue
                if (attrs.usage != AudioAttributes.USAGE_MEDIA) continue
                if (attrs.contentType == AudioAttributes.CONTENT_TYPE_SPEECH ||
                    attrs.contentType == AudioAttributes.CONTENT_TYPE_SONIFICATION ||
                    attrs.contentType == AudioAttributes.CONTENT_TYPE_MOVIE
                ) {
                    continue
                }
                hits += "$pkg:$uid:${playerInterfaceId(cfg)}"
            }
        } catch (_: Exception) {
            return ""
        }
        return hits.distinct().sorted().joinToString("|")
    }

    private fun playerInterfaceId(cfg: AudioPlaybackConfiguration): Int = try {
        AudioPlaybackConfiguration::class.java.getMethod("getPlayerInterfaceId").invoke(cfg) as Int
    } catch (_: Exception) {
        0
    }

    private fun clientUid(cfg: AudioPlaybackConfiguration): Int {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) return -1
        return try {
            AudioPlaybackConfiguration::class.java.getMethod("getClientUid").invoke(cfg) as Int
        } catch (_: Exception) {
            -1
        }
    }

    private fun packagesForUid(uid: Int): List<String> = try {
        app.packageManager.getPackagesForUid(uid)?.toList().orEmpty()
    } catch (_: Exception) {
        emptyList()
    }

    companion object {
        private const val POLL_MS = 1200L
        private const val DEBOUNCE_MUSIC_MS = 400L
        /** 约 5×1.2s：切走其它 App 后仍稳住一段时间，关页/停播后才结束 */
        private const val MISS_EXIT = 5
    }
}
