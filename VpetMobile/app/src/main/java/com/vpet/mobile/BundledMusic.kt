package com.vpet.mobile

import android.content.Context
import android.graphics.Color
import kotlin.math.roundToInt

/**
 * 内置曲库（assets/music）。精简包默认仅 RADICAL MAT。
 * 元数据对照桌面 MUSIC_CHAR_DEFS / MUSIC_FOLDER_BASE_COLORS。
 */
object BundledMusic {
    const val DEFAULT_TRACK_ID = "radical_mat"
    const val DEFAULT_FILE = "RADICAL MAT.wav"
    const val DEFAULT_FOLDER = "aoba-blue"

    data class CharDef(
        val id: String,
        val folder: String,
        val label: String,
        val colorKey: String,
    )

    data class Track(
        val folder: String,
        val fileName: String,
        val id: String = idFromFileName(fileName),
        val title: String = titleFromFileName(fileName),
        val charId: String = charIdForFolder(folder),
    ) {
        val assetPath: String get() = "music/$folder/$fileName"
        val label: String get() = "${shortFolder(folder)} · $title"
    }

    val CHAR_DEFS: List<CharDef> = listOf(
        CharDef("aoba", "aoba-blue", "Aoba", "blue"),
        CharDef("clear", "clear-yellow", "Clear", "yellow"),
        CharDef("koujaku", "koujaku-red", "Koujaku", "red"),
        CharDef("mink", "mink-pink", "Mink", "pink"),
        CharDef("mizuki", "mizuki-deep red", "Mizuki", "deep red"),
        CharDef("noiz", "noiz-green", "Noiz", "green"),
        CharDef("ren", "ren-deep blue", "Ren", "deep blue"),
        CharDef("virus_trip", "virus&trip-grey", "Virus&Trip", "grey"),
    )

    private val FOLDER_BASE: Map<String, String> = mapOf(
        "blue" to "#9EC8E8",
        "deep blue" to "#8AA4C8",
        "yellow" to "#E8D6A0",
        "red" to "#E0A0AC",
        "deep red" to "#D0909C",
        "pink" to "#E8B8D0",
        "green" to "#A8D4B4",
        "grey" to "#B0BCC4",
    )

    private val TITLE_TO_ID = mapOf(
        "RADICAL MAT" to "radical_mat",
        "AI CATCH" to "ai_catch",
        "Crystalline" to "crystalline",
        "your reply" to "your_reply",
        "SLIP ON THE PUMPS" to "slip_on_the_pumps",
        "By My Side" to "by_my_side",
        "felt" to "felt",
        "Lullaby Blue" to "lullaby_blue",
        "Soul Grace" to "soul_grace",
    )

    fun folders(ctx: Context): List<String> =
        ctx.assets.list("music")?.filter {
            it.isNotBlank() && !it.endsWith(".txt", true)
        }?.sorted().orEmpty()

    fun tracks(ctx: Context, folder: String? = null): List<Track> {
        val dirs = if (folder.isNullOrBlank()) folders(ctx) else listOf(folder)
        val out = mutableListOf<Track>()
        for (dir in dirs) {
            val files = ctx.assets.list("music/$dir")?.filter {
                val n = it.lowercase()
                n.endsWith(".wav") || n.endsWith(".mp3") || n.endsWith(".ogg")
            }.orEmpty().sorted()
            for (f in files) out += Track(dir, f)
        }
        return out
    }

    /** 默认曲：优先 radical_mat，否则曲库第一首。 */
    fun defaultTrack(ctx: Context): Track? {
        val all = tracks(ctx)
        if (all.isEmpty()) return null
        return all.firstOrNull { it.id == DEFAULT_TRACK_ID }
            ?: all.firstOrNull {
                it.folder == DEFAULT_FOLDER &&
                    it.fileName.equals(DEFAULT_FILE, ignoreCase = true)
            }
            ?: all.first()
    }

    fun waveColorsForFolder(folder: String): IntArray {
        val key = colorKeyOfFolder(folder)
        val baseHex = FOLDER_BASE[key] ?: FOLDER_BASE.getValue("blue")
        val lightHex = lighten(baseHex, 0.48f)
        return intArrayOf(Color.parseColor(baseHex), Color.parseColor(lightHex))
    }

    fun waveColorsForTrack(track: Track?): IntArray =
        waveColorsForFolder(track?.folder ?: DEFAULT_FOLDER)

    /**
     * 跟随外部音乐 App 切歌换色：按签名稳定映射到角色色板。
     * 签名变化（切歌）→ 背景/声波颜色变化。
     */
    fun waveColorsForSignature(signature: String): IntArray {
        val folders = CHAR_DEFS.map { it.folder }
        if (folders.isEmpty() || signature.isBlank()) {
            return waveColorsForFolder(DEFAULT_FOLDER)
        }
        val idx = (signature.hashCode().toLong() and 0x7fffffffL).toInt() % folders.size
        return waveColorsForFolder(folders[idx])
    }

    fun charIdForFolder(folder: String): String =
        CHAR_DEFS.firstOrNull { it.folder.equals(folder, ignoreCase = true) }?.id ?: "aoba"

    fun charLabel(charId: String): String =
        CHAR_DEFS.firstOrNull { it.id == charId }?.label ?: charId

    private fun colorKeyOfFolder(folderName: String): String {
        val name = folderName.trim().lowercase().replace('_', ' ')
        val keys = listOf(
            "deep red", "deep blue", "yellow", "green", "pink", "blue", "red", "grey", "gray",
        )
        val compact = name.replace(Regex("""[\s\-]+"""), " ").trim()
        for (key in keys) {
            if (compact.endsWith(key) || compact.endsWith(key.replace(' ', '-'))) {
                return if (key == "gray") "grey" else key
            }
        }
        val tail = compact.substringAfterLast(' ')
        return when {
            tail in FOLDER_BASE -> tail
            tail == "gray" -> "grey"
            else -> "blue"
        }
    }

    private fun lighten(hex: String, amount: Float): String {
        val t = hex.trim().removePrefix("#")
        if (t.length != 6) return "#D0E8F5"
        val r0 = t.substring(0, 2).toIntOrNull(16) ?: return "#D0E8F5"
        val g0 = t.substring(2, 4).toIntOrNull(16) ?: return "#D0E8F5"
        val b0 = t.substring(4, 6).toIntOrNull(16) ?: return "#D0E8F5"
        val a = amount.coerceIn(0f, 1f)
        val r = (r0 + (255 - r0) * a).roundToInt().coerceIn(0, 255)
        val g = (g0 + (255 - g0) * a).roundToInt().coerceIn(0, 255)
        val b = (b0 + (255 - b0) * a).roundToInt().coerceIn(0, 255)
        return "#%02X%02X%02X".format(r, g, b)
    }

    private fun idFromFileName(fileName: String): String {
        val stem = fileName.substringBeforeLast('.')
        return TITLE_TO_ID[stem]
            ?: stem.lowercase()
                .replace(Regex("""[^a-z0-9]+"""), "_")
                .trim('_')
                .ifBlank { "track" }
    }

    private fun titleFromFileName(fileName: String): String = fileName.substringBeforeLast('.')

    private fun shortFolder(folder: String): String = folder.substringBefore('-').ifBlank { folder }
}
