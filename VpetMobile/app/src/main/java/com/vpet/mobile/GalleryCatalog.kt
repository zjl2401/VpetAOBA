package com.vpet.mobile

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import org.json.JSONArray

/** 回忆画廊：gallery.json + gallery/ 与 sprites/ 回落。 */
object GalleryCatalog {
    data class Group(val title: String, val paths: List<String>, val sticker: String? = null)

    fun loadGroups(ctx: Context): List<Group> {
        val fromJson = runCatching {
            ctx.assets.open("gallery/gallery.json").bufferedReader().use { it.readText() }
        }.getOrNull()?.let { parseJson(ctx, it) }.orEmpty()
        if (fromJson.isNotEmpty()) return fromJson
        return fallbackGroups(ctx)
    }

    private fun parseJson(ctx: Context, raw: String): List<Group> {
        val arr = JSONArray(raw)
        val out = mutableListOf<Group>()
        for (i in 0 until arr.length()) {
            val o = arr.getJSONObject(i)
            val title = o.optString("title", "图组")
            val sticker = o.optString("sticker", "").ifBlank { null }
            val files = o.optJSONArray("files") ?: continue
            val paths = mutableListOf<String>()
            for (j in 0 until files.length()) {
                resolve(ctx, files.getString(j))?.let { paths += it }
            }
            if (paths.isNotEmpty()) out += Group(title, paths, sticker)
        }
        return out
    }

    private fun fallbackGroups(ctx: Context): List<Group> {
        val names = listOf(
            "站立" to listOf("stand.png"),
            "开心" to listOf("happy.png"),
            "打招呼" to listOf("hi1.png", "hi2.png"),
            "Wink" to listOf("wink.png"),
            "点赞" to listOf("like.png"),
            "下蹲" to listOf("squat.png"),
            "侧踢" to listOf("kick.png"),
            "伤心" to listOf("sad1.png", "sad2.png"),
            "吃东西" to listOf("eat1.png", "eat2.png"),
            "睡眠" to listOf("sleep1.png", "sleep2.png"),
        )
        return names.mapNotNull { (title, files) ->
            val paths = files.mapNotNull { resolve(ctx, it) }
            if (paths.isEmpty()) null else Group(title, paths)
        }
    }

    /** jpg 名回落到 png；优先 gallery/，再 sprites/。 */
    fun resolve(ctx: Context, fileName: String): String? {
        val base = fileName.substringBeforeLast('.').ifBlank { fileName }
        val candidates = listOf(
            "gallery/$fileName",
            "gallery/$base.png",
            "gallery/$base.jpg",
            "sprites/$base.png",
            "sprites/$fileName",
        )
        return candidates.firstOrNull { exists(ctx, it) }
    }

    fun decode(ctx: Context, assetPath: String): Bitmap? = try {
        ctx.assets.open(assetPath).use { BitmapFactory.decodeStream(it) }
    } catch (_: Exception) {
        null
    }

    private fun exists(ctx: Context, path: String): Boolean = try {
        ctx.assets.open(path).close()
        true
    } catch (_: Exception) {
        false
    }
}
