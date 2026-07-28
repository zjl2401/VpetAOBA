package com.vpet.mobile

import android.content.Context
import android.net.Uri
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.UUID

/** 用户留声：filesDir/phonograph + phonograph.json（对照桌面）。 */
object UserPhonographStore {
    private const val INDEX = "phonograph.json"

    data class Entry(val id: String, val title: String, val filename: String)

    private fun dir(ctx: Context) = File(ctx.filesDir, "phonograph").also { it.mkdirs() }
    private fun indexFile(ctx: Context) = File(dir(ctx), INDEX)

    fun list(ctx: Context): List<Entry> {
        val f = indexFile(ctx)
        if (!f.isFile) return emptyList()
        return try {
            val arr = JSONArray(f.readText())
            (0 until arr.length()).mapNotNull { i ->
                val o = arr.optJSONObject(i) ?: return@mapNotNull null
                val id = o.optString("id").ifBlank { return@mapNotNull null }
                val fn = o.optString("filename").ifBlank { return@mapNotNull null }
                if (!File(dir(ctx), fn).isFile) return@mapNotNull null
                Entry(id, o.optString("title", fn), fn)
            }
        } catch (_: Exception) {
            emptyList()
        }
    }

    fun fileOf(ctx: Context, entry: Entry): File = File(dir(ctx), entry.filename)

    fun importUri(ctx: Context, uri: Uri, titleHint: String? = null): Entry? {
        return try {
            val id = UUID.randomUUID().toString().take(8)
            val ext = guessExt(ctx, uri)
            val filename = "clip_$id.$ext"
            val dest = File(dir(ctx), filename)
            ctx.contentResolver.openInputStream(uri)?.use { input ->
                dest.outputStream().use { output -> input.copyTo(output) }
            } ?: return null
            if (!dest.isFile || dest.length() <= 0L) return null
            val title = titleHint?.takeIf { it.isNotBlank() } ?: "用户留声 $id"
            val entry = Entry(id, title, filename)
            val all = list(ctx).toMutableList()
            all.add(0, entry)
            save(ctx, all)
            entry
        } catch (_: Exception) {
            null
        }
    }

    fun remove(ctx: Context, id: String) {
        val all = list(ctx).toMutableList()
        val idx = all.indexOfFirst { it.id == id }
        if (idx < 0) return
        val e = all.removeAt(idx)
        File(dir(ctx), e.filename).delete()
        save(ctx, all)
    }

    private fun save(ctx: Context, entries: List<Entry>) {
        val arr = JSONArray()
        for (e in entries) {
            arr.put(JSONObject().put("id", e.id).put("title", e.title).put("filename", e.filename))
        }
        indexFile(ctx).writeText(arr.toString())
    }

    private fun guessExt(ctx: Context, uri: Uri): String {
        val type = ctx.contentResolver.getType(uri)?.lowercase().orEmpty()
        val name = uri.lastPathSegment?.lowercase().orEmpty()
        return when {
            type.contains("mpeg") || type.contains("mp3") || name.endsWith(".mp3") -> "mp3"
            type.contains("ogg") || name.endsWith(".ogg") -> "ogg"
            type.contains("m4a") || name.endsWith(".m4a") -> "m4a"
            else -> "wav"
        }
    }
}
