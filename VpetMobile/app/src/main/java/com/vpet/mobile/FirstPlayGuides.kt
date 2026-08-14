package com.vpet.mobile

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.view.ContextThemeWrapper

/** 首次进入玩法弹电脑版 FIRST_PLAY_GUIDES 原文。 */
object FirstPlayGuides {
    fun maybeShow(context: Context, key: String) {
        val topic = DesktopGuideCopy.FIRST_PLAY[key] ?: return
        if (AppConfigStore.seenOnceHint(context, key)) return
        AppConfigStore.markOnceHint(context, key)
        val themed = ContextThemeWrapper(context, R.style.Theme_VpetMobile)
        val b = AlertDialog.Builder(themed)
            .setTitle(topic.title)
            .setMessage(topic.body)
            .setPositiveButton("知道了", null)
        val link = topic.links.firstOrNull()
        if (link != null) {
            b.setNeutralButton(link.first) { _, _ ->
                try {
                    context.startActivity(
                        Intent(Intent.ACTION_VIEW, Uri.parse(link.second))
                            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
                    )
                } catch (_: Exception) {
                }
            }
        }
        try {
            b.show()
        } catch (_: Exception) {
        }
    }
}
