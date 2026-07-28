package com.vpet.mobile

import android.content.Context
import android.content.res.AssetFileDescriptor
import android.media.MediaPlayer
import android.os.SystemClock
import org.json.JSONObject
import java.io.IOException

/**
 * 本地语音：对照桌面 voice_system / `_voice_enabled`。
 * 支持数字→伴侣 / 字母→苍叶 链式对答（[chain_index.json]）。
 */
class VoicePlayer(private val context: Context) {
    companion object {
        const val VOICE_GLOBAL_COOLDOWN_MS = 10_000L
        val FORCE_CATEGORIES = setOf(
            "hi", "你好", "call", "kick", "eat", "sleep", "work", "dizzy", "yuqi", "end", "hurt", "hungry",
        )
        private val CHAIN_AMBIENT = setOf(
            "normal", "walk", "work", "game", "hungry", "forget", "error", "email", "ren",
        )
    }

    private var player: MediaPlayer? = null
    private var lastPlayMs = 0L
    var musicBlocked: Boolean = false
    /** 伴侣是否在场（数字链需要）。 */
    var hasCompanion: () -> Boolean = { false }

    private data class ChainIndex(
        val vpet: Map<String, String>,
        val allmate: Map<String, String>,
    )

    private val chainIndex: ChainIndex by lazy { loadChainIndex() }
    private val prefixOfPath: Map<String, Pair<String, String>> by lazy {
        // path -> (source, prefix)
        val m = mutableMapOf<String, Pair<String, String>>()
        for ((p, path) in chainIndex.vpet) m[path] = "vpet" to p
        for ((p, path) in chainIndex.allmate) m[path] = "allmate" to p
        m
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
    }

    fun playing(): Boolean = try {
        player?.isPlaying == true
    } catch (_: Exception) {
        false
    }

    fun voiceEnabled(): Boolean =
        AppDataStore.voiceMode(context) && !musicBlocked

    fun hasCategory(category: String): Boolean =
        pickAsset("voice/Vpet/$category") != null ||
            (category == "hi" && pickAsset("voice/Vpet/你好") != null)

    /** 部位感叹：对照 play_interjection；资源按文件名均分 face/body/legs。 */
    fun playInterjection(part: String, onDone: (() -> Unit)? = null): Boolean {
        if (!voiceEnabled()) return false
        val path = pickInterjection(part) ?: return false
        lastPlayMs = SystemClock.elapsedRealtime()
        return playAsset(path, onDone)
    }

    private fun pickInterjection(part: String): String? {
        val dir = "voice/Vpet/interjection"
        val files = try {
            context.assets.list(dir)?.filter {
                it.endsWith(".wav", true) || it.endsWith(".ogg", true) || it.endsWith(".mp3", true)
            }?.sorted().orEmpty()
        } catch (_: Exception) {
            emptyList()
        }
        if (files.isEmpty()) {
            // 无专用库时回落短 yuqi（仍按部位哈希选）
            return pickAsset("voice/Vpet/yuqi")
        }
        val parts = listOf("face", "body", "legs")
        val idx = parts.indexOf(part).coerceAtLeast(0)
        val n = files.size
        val bucket = files.filterIndexed { i, _ ->
            minOf(i * parts.size / n, parts.size - 1) == idx
        }.ifEmpty { files }
        return bucket.randomOrNull()?.let { "$dir/$it" }
    }

    /** @return 是否开始播放 */
    fun playCategory(
        category: String,
        force: Boolean = false,
        chain: Boolean = true,
        onDone: (() -> Unit)? = null,
    ): Boolean {
        if (!voiceEnabled()) return false
        val now = SystemClock.elapsedRealtime()
        if (!force && now - lastPlayMs < VOICE_GLOBAL_COOLDOWN_MS) return false
        if (!force && playing()) return false
        val allowChain = chain && category !in FORCE_CATEGORIES
        // 伴侣在场时，氛围类有概率直接抽数字链头，便于触发对答
        val path = when {
            category == "hi" -> pickAsset("voice/Vpet/hi") ?: pickAsset("voice/Vpet/你好")
            allowChain && hasCompanion() && category in CHAIN_AMBIENT &&
                kotlin.random.Random.nextFloat() < 0.35f ->
                pickChainStarterDigit() ?: pickCategoryPath(category)
            else -> pickCategoryPath(category)
        } ?: return false
        val ok = playAsset(path) {
            if (allowChain) maybeChain(path) { onDone?.invoke() }
            else onDone?.invoke()
        }
        if (ok) lastPlayMs = now
        return ok
    }

    fun playHi(onDone: (() -> Unit)? = null): Boolean =
        playCategory("hi", force = true, chain = false, onDone = onDone)

    fun playCall(
        onRingStart: (() -> Unit)? = null,
        onLineStart: (() -> Unit)? = null,
        onDone: (() -> Unit)? = null,
    ): Boolean {
        if (!voiceEnabled()) return false
        val ring = pickAsset("voice/Vpet/call") { it.contains("ring", ignoreCase = true) }
            ?: pickAsset("voice/Allmate") { it.contains("ring", ignoreCase = true) }
        val line = pickAsset("voice/Vpet/call") { !it.contains("ring", ignoreCase = true) }
            ?: return false
        lastPlayMs = SystemClock.elapsedRealtime()
        if (ring != null) {
            onRingStart?.invoke()
            return playAsset(ring) {
                onLineStart?.invoke()
                playAsset(line, onDone)
            }
        }
        onLineStart?.invoke()
        return playAsset(line, onDone)
    }

    fun playCompanionStart(): Boolean {
        if (!voiceEnabled()) return false
        val path = pickAsset("voice/Allmate") {
            it.contains("start", ignoreCase = true) || it.contains("启动")
        } ?: pickAsset("voice/Allmate") { !it.contains("ring", ignoreCase = true) }
            ?: return false
        lastPlayMs = SystemClock.elapsedRealtime()
        return playAsset(path)
    }

    fun pickAsset(dir: String, predicate: ((String) -> Boolean)? = null): String? {
        return try {
            val files = context.assets.list(dir)?.filter {
                it.endsWith(".wav", true) || it.endsWith(".ogg", true) || it.endsWith(".mp3", true)
            }.orEmpty()
            val filtered = if (predicate != null) files.filter(predicate) else files
            filtered.randomOrNull()?.let { "$dir/$it" }
        } catch (_: Exception) {
            null
        }
    }

    fun playAssetPath(assetPath: String, onDone: (() -> Unit)? = null): Boolean {
        // 留声页可直接播，不强制 voice_mode
        lastPlayMs = SystemClock.elapsedRealtime()
        return playAsset(assetPath, onDone)
    }

    /** 播放本地文件（用户留声）。 */
    fun playFile(file: java.io.File, onDone: (() -> Unit)? = null): Boolean {
        if (!file.isFile) return false
        stop()
        return try {
            val mp = MediaPlayer()
            mp.setDataSource(file.absolutePath)
            val vol = AppDataStore.voiceVolumeF(context)
            mp.setVolume(vol, vol)
            mp.setOnCompletionListener {
                if (player === mp) stop()
                onDone?.invoke()
            }
            mp.setOnErrorListener { _, _, _ ->
                if (player === mp) stop()
                onDone?.invoke()
                true
            }
            mp.prepare()
            mp.start()
            player = mp
            true
        } catch (_: Exception) {
            stop()
            false
        }
    }

    private fun pickCategoryPath(category: String): String? =
        pickAsset("voice/Vpet/$category")

    private fun pickChainStarterDigit(): String? {
        val digits = chainIndex.vpet.filterKeys { it.all(Char::isDigit) }.values.toList()
        return digits.randomOrNull()
    }

    private fun maybeChain(finishedPath: String, onDone: (() -> Unit)?) {
        val meta = prefixOfPath[finishedPath]
        if (meta == null) {
            onDone?.invoke()
            return
        }
        val (source, prefix) = meta
        val next = when {
            source == "vpet" && prefix.all(Char::isDigit) && hasCompanion() ->
                chainIndex.allmate[prefix]
            source == "allmate" && prefix.length == 1 && prefix[0].isLetter() ->
                chainIndex.vpet[prefix.lowercase()]
            else -> null
        }
        if (next == null) {
            onDone?.invoke()
            return
        }
        // 链式续播：字幕由上层可选；此处只播音
        if (!playAsset(next) {
                // 字母链：伴侣 → 苍叶后结束；数字链伴侣答完即结束（不再二次链）
                onDone?.invoke()
            }
        ) {
            onDone?.invoke()
        }
    }

    private fun loadChainIndex(): ChainIndex {
        return try {
            val text = context.assets.open("voice/chain_index.json").bufferedReader().use { it.readText() }
            val o = JSONObject(text)
            fun mapOf(key: String): Map<String, String> {
                val child = o.optJSONObject(key) ?: return emptyMap()
                val out = mutableMapOf<String, String>()
                val it = child.keys()
                while (it.hasNext()) {
                    val k = it.next()
                    out[k] = child.getString(k)
                }
                return out
            }
            ChainIndex(mapOf("vpet"), mapOf("allmate"))
        } catch (_: Exception) {
            ChainIndex(emptyMap(), emptyMap())
        }
    }

    private fun playAsset(assetPath: String, onDone: (() -> Unit)? = null): Boolean {
        stop()
        return try {
            val afd: AssetFileDescriptor = context.assets.openFd(assetPath)
            val mp = MediaPlayer()
            player = mp
            mp.setDataSource(afd.fileDescriptor, afd.startOffset, afd.length)
            afd.close()
            mp.setOnCompletionListener {
                onDone?.invoke()
                // 若 onDone 又启动了新 play，不要 stop 掉新实例
                if (player === mp) stop()
            }
            mp.setOnErrorListener { _, _, _ ->
                if (player === mp) stop()
                onDone?.invoke()
                true
            }
            mp.prepare()
            val vol = AppDataStore.voiceVolumeF(context)
            mp.setVolume(vol, vol)
            mp.start()
            true
        } catch (_: IOException) {
            stop()
            false
        } catch (_: Exception) {
            stop()
            false
        }
    }
}
