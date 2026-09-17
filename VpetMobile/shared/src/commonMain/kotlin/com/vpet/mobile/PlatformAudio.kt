package com.vpet.mobile

/** 跨端语音/音效；首版 Android 包装现有播放器，iOS 用 AVAudioPlayer。 */
interface PlatformAudio {
    fun playVoice(assetKey: String, force: Boolean = false)
    fun stopVoice()
    fun playSfx(assetKey: String)
}

object PlatformAudioHolder {
    var impl: PlatformAudio = object : PlatformAudio {
        override fun playVoice(assetKey: String, force: Boolean) {}
        override fun stopVoice() {}
        override fun playSfx(assetKey: String) {}
    }
}
