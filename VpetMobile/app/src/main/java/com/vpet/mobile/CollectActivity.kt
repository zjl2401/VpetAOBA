package com.vpet.mobile

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity

/** 旧全屏采集页；现由 [CollectOverlayUi] 在屏幕上直接玩。保留避免清单引用断裂。 */
class CollectActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        finish()
    }
}
