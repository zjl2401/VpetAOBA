package com.vpet.mobile

/** 应用设置子集（字体/声音/难度），对照 AppDataStore。 */
object SharedAppSettings {
    private const val PREF = "vpet_appdata"
    private const val KEY_FONT = "font_label"
    private const val KEY_SOUND = "sound_on"
    private const val KEY_VOICE_MODE = "voice_mode"
    private const val KEY_VOICE_VOL = "voice_volume"
    private const val KEY_DIFF = "difficulty"
    private const val KEY_SPEECH_TEXT = "show_speech_text"

    val FONT_PRESETS = linkedMapOf("小" to 11f, "中" to 13f, "大" to 15f, "特大" to 17f)
    val DIFF_PRESETS = listOf("低", "中", "高")

    private fun prefs() = PlatformStorage(PREF)

    fun fontLabel(): String {
        val v = prefs().getString(KEY_FONT, "中") ?: "中"
        return if (v in FONT_PRESETS) v else "中"
    }

    fun setFontLabel(label: String) {
        prefs().putString(KEY_FONT, if (label in FONT_PRESETS) label else "中")
    }

    fun soundOn(): Boolean = prefs().getBoolean(KEY_SOUND, true)
    fun setSoundOn(on: Boolean) = prefs().putBoolean(KEY_SOUND, on)

    fun speechTextOn(): Boolean = prefs().getBoolean(KEY_SPEECH_TEXT, true)
    fun setSpeechTextOn(on: Boolean) = prefs().putBoolean(KEY_SPEECH_TEXT, on)

    fun voiceMode(): String = prefs().getString(KEY_VOICE_MODE, "开") ?: "开"
    fun setVoiceMode(mode: String) = prefs().putString(KEY_VOICE_MODE, mode)

    fun voiceVolume(): Int = prefs().getInt(KEY_VOICE_VOL, 80).coerceIn(0, 100)
    fun setVoiceVolume(v: Int) = prefs().putInt(KEY_VOICE_VOL, v.coerceIn(0, 100))

    fun difficulty(): String {
        val v = prefs().getString(KEY_DIFF, "中") ?: "中"
        return if (v in DIFF_PRESETS) v else "中"
    }

    fun setDifficulty(label: String) {
        prefs().putString(KEY_DIFF, if (label in DIFF_PRESETS) label else "中")
    }
}
