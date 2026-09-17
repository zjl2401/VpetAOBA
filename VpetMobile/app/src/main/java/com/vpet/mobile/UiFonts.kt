package com.vpet.mobile

import android.content.Context
import android.graphics.Typeface
import android.view.View
import android.view.ViewGroup
import android.widget.TextView

/**
 * UI 字体：与电脑设置一致——楷体 / 幼圆 / 像素 / 雅黑 / 默认。
 */
object UiFonts {
    @Volatile
    private var cacheKey: String? = null
    @Volatile
    private var cached: Typeface? = null

    fun cute(context: Context): Typeface = face(context, AppDataStore.fontFamily(context))

    fun face(context: Context, family: String = AppDataStore.fontFamily(context)): Typeface {
        val key = if (family in AppDataStore.FONT_FAMILIES) family else AppDataStore.FONT_FAMILY_DEFAULT
        if (cacheKey == key) {
            cached?.let { return it }
        }
        val loaded = when (key) {
            "幼圆" -> loadAsset(context, "fonts/youyuan.ttf")
                ?: loadRes(context, R.font.youyuan)
                ?: Typeface.create("sans-serif", Typeface.NORMAL)
            "像素" -> loadAsset(context, "fonts/fusion-pixel-12px-proportional-zh_hans.ttf")
                ?: loadAsset(context, "fonts/PressStart2P-Regular.ttf")
                ?: Typeface.MONOSPACE
            "雅黑" -> Typeface.create("sans-serif", Typeface.NORMAL)
                ?: Typeface.SANS_SERIF
            "楷体" -> Typeface.create("serif", Typeface.NORMAL)
                ?: Typeface.SERIF
            "默认" -> Typeface.DEFAULT
            else -> Typeface.create("serif", Typeface.NORMAL)
                ?: Typeface.SERIF
        } ?: Typeface.SANS_SERIF
        cacheKey = key
        cached = loaded
        return loaded
    }

    fun cuteBold(context: Context): Typeface =
        Typeface.create(cute(context), Typeface.BOLD) ?: cute(context)

    fun clearCache() {
        cacheKey = null
        cached = null
    }

    private fun loadAsset(context: Context, path: String): Typeface? = try {
        Typeface.createFromAsset(context.assets, path)
    } catch (_: Exception) {
        null
    }

    private fun loadRes(context: Context, resId: Int): Typeface? = try {
        androidx.core.content.res.ResourcesCompat.getFont(context, resId)
    } catch (_: Exception) {
        null
    }

    /** 递归套用到 Activity/Dialog 根视图下所有 TextView。 */
    fun applyTree(root: View?) {
        root ?: return
        val face = cute(root.context)
        fun walk(v: View) {
            if (v is TextView) {
                val bold = v.typeface?.isBold == true ||
                    (v.paintFlags and android.graphics.Paint.FAKE_BOLD_TEXT_FLAG) != 0
                v.typeface = if (bold) Typeface.create(face, Typeface.BOLD) ?: face else face
            }
            if (v is ViewGroup) {
                for (i in 0 until v.childCount) walk(v.getChildAt(i))
            }
        }
        walk(root)
    }
}
