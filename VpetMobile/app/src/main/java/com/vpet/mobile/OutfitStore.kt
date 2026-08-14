package com.vpet.mobile

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID
import kotlin.math.max
import kotlin.math.roundToInt

/**
 * 装扮数据与像素素材（对齐桌面 pet_outfit.py）。
 * kind: builtin | user_paint | gift_art
 */
object OutfitStore {
    const val MAX = 8
    const val SCALE_MIN = 0.12f
    const val SCALE_MAX = 0.55f
    const val DEFAULT_NX = 0f
    const val DEFAULT_NY = -0.38f
    const val DEFAULT_SCALE = 0.28f

    const val KIND_BUILTIN = "builtin"
    const val KIND_USER_PAINT = "user_paint"
    const val KIND_GIFT_ART = "gift_art"

    data class Decor(
        val id: String,
        var kind: String,
        var ref: String,
        var nx: Float,
        var ny: Float,
        var scale: Float,
    )

    data class Choice(val kind: String, val ref: String, val name: String, val group: String)

    private val builtinPalette = intArrayOf(
        Color.TRANSPARENT,
        Color.parseColor("#FF6688"),
        Color.parseColor("#FFCC66"),
        Color.parseColor("#66CCFF"),
        Color.parseColor("#88EEAA"),
        Color.parseColor("#FFFFFF"),
        Color.parseColor("#CC88FF"),
        Color.parseColor("#442233"),
    )

    private fun cellsOf(draw: (put: (Int, Int, Int) -> Unit) -> Unit): IntArray {
        val cells = IntArray(144)
        draw { x, y, c ->
            if (x in 0 until 12 && y in 0 until 12) cells[y * 12 + x] = c
        }
        return cells
    }

    private val builtinCatalog: List<Triple<String, String, IntArray>> = listOf(
        Triple(
            "star", "星星",
            cellsOf { put ->
                listOf(
                    5 to 1, 5 to 2, 4 to 3, 5 to 3, 6 to 3, 3 to 4, 4 to 4, 5 to 4, 6 to 4, 7 to 4,
                    5 to 5, 4 to 6, 6 to 6, 3 to 7, 7 to 7,
                ).forEach { (x, y) -> put(x, y, 2) }
            },
        ),
        Triple(
            "heart", "爱心",
            cellsOf { put ->
                listOf(
                    3 to 2, 4 to 2, 7 to 2, 8 to 2,
                    2 to 3, 3 to 3, 4 to 3, 5 to 3, 6 to 3, 7 to 3, 8 to 3, 9 to 3,
                    2 to 4, 3 to 4, 4 to 4, 5 to 4, 6 to 4, 7 to 4, 8 to 4, 9 to 4,
                    3 to 5, 4 to 5, 5 to 5, 6 to 5, 7 to 5, 8 to 5,
                    4 to 6, 5 to 6, 6 to 6, 7 to 6, 5 to 7, 6 to 7,
                ).forEach { (x, y) -> put(x, y, 1) }
            },
        ),
        Triple(
            "bow", "蝴蝶结",
            cellsOf { put ->
                listOf(
                    2 to 4, 3 to 4, 4 to 4, 7 to 4, 8 to 4, 9 to 4,
                    1 to 5, 2 to 5, 3 to 5, 4 to 5, 5 to 5, 6 to 5, 7 to 5, 8 to 5, 9 to 5, 10 to 5,
                    2 to 6, 3 to 6, 4 to 6, 7 to 6, 8 to 6, 9 to 6, 5 to 4, 5 to 6,
                ).forEach { (x, y) -> put(x, y, 6) }
                put(5, 5, 5)
            },
        ),
        Triple(
            "leaf", "小叶",
            cellsOf { put ->
                listOf(
                    6 to 1, 5 to 2, 6 to 2, 7 to 2, 4 to 3, 5 to 3, 6 to 3, 7 to 3,
                    3 to 4, 4 to 4, 5 to 4, 6 to 4, 4 to 5, 5 to 5, 6 to 5, 5 to 6, 6 to 6, 6 to 7, 7 to 8,
                ).forEach { (x, y) -> put(x, y, 4) }
            },
        ),
    )

    fun clampNorm(v: Float): Float = v.coerceIn(-0.55f, 0.55f)
    fun clampScale(v: Float): Float = v.coerceIn(SCALE_MIN, SCALE_MAX)

    fun load(ctx: Context): List<Decor> {
        val arr = PetProfileStore.profile(ctx).optJSONArray("outfit_decors") ?: return emptyList()
        val out = ArrayList<Decor>()
        for (i in 0 until arr.length()) {
            val o = arr.optJSONObject(i) ?: continue
            val kind = o.optString("kind")
            if (kind !in setOf(KIND_BUILTIN, KIND_USER_PAINT, KIND_GIFT_ART)) continue
            val ref = o.optString("ref")
            if (kind == KIND_BUILTIN && ref.isBlank()) continue
            out += Decor(
                id = o.optString("id").ifBlank { UUID.randomUUID().toString().take(10) },
                kind = kind,
                ref = ref,
                nx = clampNorm(o.optDouble("nx", DEFAULT_NX.toDouble()).toFloat()),
                ny = clampNorm(o.optDouble("ny", DEFAULT_NY.toDouble()).toFloat()),
                scale = clampScale(o.optDouble("scale", DEFAULT_SCALE.toDouble()).toFloat()),
            )
            if (out.size >= MAX) break
        }
        return out
    }

    fun save(ctx: Context, list: List<Decor>) {
        val p = PetProfileStore.profile(ctx)
        val arr = JSONArray()
        for (d in list.take(MAX)) {
            arr.put(
                JSONObject()
                    .put("id", d.id)
                    .put("kind", d.kind)
                    .put("ref", d.ref)
                    .put("nx", d.nx.toDouble())
                    .put("ny", d.ny.toDouble())
                    .put("scale", d.scale.toDouble()),
            )
        }
        p.put("outfit_decors", arr)
        PetProfileStore.saveProfile(ctx, p)
    }

    fun newDecor(kind: String, ref: String, nx: Float = DEFAULT_NX, ny: Float = DEFAULT_NY, scale: Float = DEFAULT_SCALE) =
        Decor(UUID.randomUUID().toString().take(10), kind, ref, clampNorm(nx), clampNorm(ny), clampScale(scale))

    fun choices(ctx: Context): List<Choice> {
        val list = mutableListOf<Choice>()
        for ((id, name, _) in builtinCatalog) {
            list += Choice(KIND_BUILTIN, id, "公开·$name", "公开")
        }
        if (assetExists(ctx, "home/user_paint.png")) {
            list += Choice(KIND_USER_PAINT, "", "自创画", "我的")
        }
        if (assetExists(ctx, "home/gift_art.png")) {
            list += Choice(KIND_GIFT_ART, "", "礼物画", "我的")
        }
        return list
    }

    private fun assetExists(ctx: Context, path: String): Boolean =
        try {
            ctx.assets.open(path).close()
            true
        } catch (_: Exception) {
            false
        }

    fun bitmapFor(ctx: Context, decor: Decor, sizePx: Int): Bitmap? {
        val side = sizePx.coerceAtLeast(8)
        return when (decor.kind) {
            KIND_BUILTIN -> builtinBitmap(decor.ref, side)
            KIND_USER_PAINT -> decodeAsset(ctx, "home/user_paint.png", side)
            KIND_GIFT_ART -> decodeAsset(ctx, "home/gift_art.png", side)
            else -> null
        }
    }

    fun thumbFor(ctx: Context, choice: Choice, sizePx: Int = 36): Bitmap? =
        bitmapFor(ctx, Decor("t", choice.kind, choice.ref, 0f, 0f, DEFAULT_SCALE), sizePx)

    private fun decodeAsset(ctx: Context, path: String, sizePx: Int): Bitmap? =
        try {
            ctx.assets.open(path).use { stream ->
                val raw = BitmapFactory.decodeStream(stream) ?: return null
                // 等比贴进透明方框（对照桌面家园 `_fit_bottom`），不拉扁成正方形
                fitIntoSquare(raw, sizePx)
            }
        } catch (_: Exception) {
            null
        }

    private fun fitIntoSquare(src: Bitmap, side: Int): Bitmap {
        val sw = src.width.coerceAtLeast(1)
        val sh = src.height.coerceAtLeast(1)
        if (sw == side && sh == side) return src
        val scale = minOf(side.toFloat() / sw, side.toFloat() / sh)
        val nw = max(1, (sw * scale).roundToInt())
        val nh = max(1, (sh * scale).roundToInt())
        val scaled = if (nw == sw && nh == sh) src else Bitmap.createScaledBitmap(src, nw, nh, false)
        val out = Bitmap.createBitmap(side, side, Bitmap.Config.ARGB_8888)
        Canvas(out).drawBitmap(scaled, (side - nw) / 2f, (side - nh).toFloat(), null)
        if (scaled !== src && scaled !== out) {
            try { scaled.recycle() } catch (_: Exception) {}
        }
        if (src !== out && src !== scaled) {
            try { src.recycle() } catch (_: Exception) {}
        }
        return out
    }

    private fun builtinBitmap(ref: String, sizePx: Int): Bitmap? {
        val cells = builtinCatalog.firstOrNull { it.first == ref }?.third ?: return null
        val scale = 4
        val base = 12 * scale
        val bmp = Bitmap.createBitmap(base, base, Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp)
        val p = Paint().apply { style = Paint.Style.FILL; isAntiAlias = false }
        for (y in 0 until 12) {
            for (x in 0 until 12) {
                val idx = cells[y * 12 + x]
                if (idx <= 0 || idx >= builtinPalette.size) continue
                p.color = builtinPalette[idx]
                c.drawRect(
                    (x * scale).toFloat(),
                    (y * scale).toFloat(),
                    ((x + 1) * scale).toFloat(),
                    ((y + 1) * scale).toFloat(),
                    p,
                )
            }
        }
        return if (sizePx == base) bmp else fitIntoSquare(bmp, sizePx)
    }

    /** 在宠框坐标系绘制（PAD 已由调用方处理时，传 pet 边长与左上）。 */
    fun drawOnPet(
        canvas: Canvas,
        ctx: Context,
        petLeft: Float,
        petTop: Float,
        petSize: Float,
        list: List<Decor>,
    ) {
        if (list.isEmpty()) return
        val cx = petLeft + petSize / 2f
        val cy = petTop + petSize / 2f
        for (d in list) {
            val side = max(8, (petSize * d.scale).roundToInt())
            val bmp = bitmapFor(ctx, d, side) ?: continue
            val x = cx + d.nx * petSize - bmp.width / 2f
            val y = cy + d.ny * petSize - bmp.height / 2f
            canvas.drawBitmap(bmp, x, y, null)
        }
    }
}
