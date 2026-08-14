package com.vpet.mobile

/**
 * 从语音资源文件名解析台词标题（对照桌面 `_parse_stem` / `_strip_title_prefix`）。
 * 手机版：英文资源名 / 文件名碎片不弹文本框。
 */
object VoiceTitle {
    private val PREFIX_RE = Regex("""^((?:\d+)|(?:[a-zA-Z]))(?:[\s._\-]+)(.+)$""")
    private val LEFTOVER_PREFIX = Regex("""^((?:\d+)|(?:[a-zA-Z]))(?:[\s._\-]+)?""")
    private val GENERIC_STEM = Regex("""(?i)^(?:[a-z]+|ij)_\d+$""")
    private val CJK = Regex("""[\u3400-\u9FFF\uF900-\uFAFF]""")

    fun sourceOf(assetPath: String): String =
        if (assetPath.contains("Allmate", ignoreCase = true)) "allmate" else "vpet"

    fun suppressSubtitle(assetPath: String): Boolean {
        val stem = stemOf(assetPath)
        val low = stem.lowercase()
        if (low == "ring" || low.contains("ring")) return true
        if (stem.contains("启动") || low.contains("startup")) return true
        if (stem.contains("碰撞") || low.contains("collision")) return true
        if (assetPath.contains("/interjection/", ignoreCase = true)) return true
        // 无中文可读标题：不弹字幕框（避免 hi_1 / game_1 / watch_video 等文件名）
        val title = displayTitle(assetPath)
        if (title.isBlank() || title == "……") return true
        if (looksLikeAssetName(title) || looksLikeAssetName(stem)) return true
        return false
    }

    fun displayTitle(assetPath: String): String {
        val stem = stemOf(assetPath)
        if (stem.isBlank()) return "……"
        var title = PREFIX_RE.matchEntire(stem)?.groupValues?.getOrNull(2)?.trim() ?: stem.trim()
        title = title.replace(LEFTOVER_PREFIX, "").trim()
        if (title.isBlank() || GENERIC_STEM.matches(title) || GENERIC_STEM.matches(stem)) {
            return "……"
        }
        if (title.equals("ring", ignoreCase = true) || title == "铃响") return "……"
        if (looksLikeAssetName(title) || looksLikeAssetName(stem)) return "……"
        return title
    }

    /** 英文文件名 / 下划线编号等：不当作台词展示。 */
    fun looksLikeAssetName(text: String): Boolean {
        val t = text.trim()
        if (t.isEmpty()) return true
        if (CJK.containsMatchIn(t)) return false
        if (t.contains('_') || t.contains('-') || t.contains('.')) return true
        if (t.any { it.isDigit() } && t.any { it.isLetter() }) return true
        if (t.all { it.isLetterOrDigit() || it.isWhitespace() }) {
            // 纯 ASCII 单词且无中文：多数是资源 stem
            return t.length <= 24
        }
        return false
    }

    private fun stemOf(assetPath: String): String {
        val name = assetPath.substringAfterLast('/').substringAfterLast('\\')
        val dot = name.lastIndexOf('.')
        return if (dot > 0) name.substring(0, dot) else name
    }
}
