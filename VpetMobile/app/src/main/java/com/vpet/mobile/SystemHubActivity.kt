package com.vpet.mobile

import android.content.Intent
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Bundle
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.SeekBar
import android.widget.Switch
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.vpet.mobile.databinding.ActivitySystemBinding

/**
 * 系统菜单落地页。
 * extra [EXTRA_PAGE]: diary|achievements|gallery|phonograph|settings|about|feedback|guide|submit|reset
 */
class SystemHubActivity : AppCompatActivity() {

    companion object {
        const val EXTRA_PAGE = "page"
        const val EXTRA_AUTO_GUIDE = "auto_guide"
        const val ABOUT_REPO = "https://github.com/zjl2401/VpetAOBA"
        const val FEEDBACK_ISSUE = "$ABOUT_REPO/issues"
        const val XHS = "https://www.xiaohongshu.com/user/profile/444225910"
        const val BILI = "https://space.bilibili.com/696083047"
    }

    private lateinit var binding: ActivitySystemBinding
    private var phonographPlayer: VoicePlayer? = null

    private val pickGalleryImage = registerForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        if (uri == null) return@registerForActivityResult
        val e = UserGalleryStore.importUri(this, uri)
        if (e == null) Toast.makeText(this, "导入失败", Toast.LENGTH_SHORT).show()
        else {
            Toast.makeText(this, "已加入画廊：${e.title}", Toast.LENGTH_SHORT).show()
            pageGallery()
        }
    }

    private val pickPhonographAudio = registerForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        if (uri == null) return@registerForActivityResult
        val e = UserPhonographStore.importUri(this, uri)
        if (e == null) Toast.makeText(this, "导入失败", Toast.LENGTH_SHORT).show()
        else {
            Toast.makeText(this, "已加入留声：${e.title}", Toast.LENGTH_SHORT).show()
            pagePhonograph()
        }
    }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySystemBinding.inflate(layoutInflater)
        setContentView(binding.root)
        UiFonts.applyTree(binding.root)
        when (intent.getStringExtra(EXTRA_PAGE) ?: "about") {
            "diary" -> pageDiary()
            "achievements" -> pageAchievements()
            "gallery" -> pageGallery()
            "phonograph" -> pagePhonograph()
            "settings" -> pageSettings()
            "about" -> pageAbout()
            "feedback" -> pageFeedback()
            "guide" -> pageGuide(auto = intent.getBooleanExtra(EXTRA_AUTO_GUIDE, false))
            "submit" -> pageSubmit()
            "reset" -> pageReset()
            else -> pageAbout()
        }
    }

    override fun onDestroy() {
        phonographPlayer?.stop()
        phonographPlayer = null
        super.onDestroy()
    }

    private fun clearButtons() = binding.sysButtons.removeAllViews()

    private fun dp(v: Int): Int =
        TypedValue.applyDimension(
            TypedValue.COMPLEX_UNIT_DIP,
            v.toFloat(),
            resources.displayMetrics,
        ).toInt()

    private fun addBtn(label: String, onClick: () -> Unit) {
        binding.sysButtons.addView(
            Button(this).apply {
                text = label
                typeface = UiFonts.cute(this@SystemHubActivity)
                setTextColor(MenuDecor.MENU_FG)
                background = MenuDecor.moduleBtnBg(false)
                AppDataStore.applySp(this, AppDataStore.fontBodySp(this@SystemHubActivity))
                minHeight = 0
                minimumHeight = dp(42)
                setPadding(dp(12), dp(8), dp(12), dp(8))
                layoutParams = LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT,
                ).also { it.bottomMargin = dp(6) }
                setOnClickListener { onClick() }
            },
        )
    }

    private fun addSwitchRow(title: String, checked: Boolean, onChanged: (Boolean) -> Unit) {
        val row = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, dp(6), 0, dp(6))
        }
        val label = TextView(this).apply {
            text = title
            typeface = UiFonts.cute(this@SystemHubActivity)
            setTextColor(getColor(R.color.text_main))
            AppDataStore.applySp(this, AppDataStore.fontBodySp(this@SystemHubActivity))
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
        }
        val sw = Switch(this).apply {
            isChecked = checked
            setOnCheckedChangeListener { _, on -> onChanged(on) }
        }
        row.addView(label)
        row.addView(sw)
        binding.sysButtons.addView(row)
    }

    private fun addSliderRow(
        title: String,
        progress: Int,
        max: Int,
        format: (Int) -> String,
        onChange: (Int) -> Unit,
        applyOnStop: Boolean = false,
    ) {
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(0, dp(8), 0, dp(8))
        }
        val head = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        val titleTv = TextView(this).apply {
            text = title
            typeface = UiFonts.cute(this@SystemHubActivity)
            setTextColor(getColor(R.color.text_main))
            AppDataStore.applySp(this, AppDataStore.fontBodySp(this@SystemHubActivity))
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
        }
        val valueTv = TextView(this).apply {
            text = format(progress.coerceIn(0, max))
            typeface = UiFonts.cute(this@SystemHubActivity)
            setTextColor(getColor(R.color.accent_pink))
            AppDataStore.applySp(this, AppDataStore.fontCaptionSp(this@SystemHubActivity))
        }
        head.addView(titleTv)
        head.addView(valueTv)
        val seek = SeekBar(this).apply {
            this.max = max.coerceAtLeast(1)
            this.progress = progress.coerceIn(0, this.max)
            setPadding(dp(4), dp(8), dp(4), dp(4))
            setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(seekBar: SeekBar?, p: Int, fromUser: Boolean) {
                    valueTv.text = format(p)
                    if (fromUser && !applyOnStop) onChange(p)
                }
                override fun onStartTrackingTouch(seekBar: SeekBar?) {}
                override fun onStopTrackingTouch(seekBar: SeekBar?) {
                    if (applyOnStop) onChange(seekBar?.progress ?: return)
                }
            })
        }
        box.addView(head)
        box.addView(seek)
        binding.sysButtons.addView(box)
    }

    private fun pageDiary() {
        binding.sysTitle.text = "日记"
        binding.sysTitle.typeface = UiFonts.cute(this)
        binding.sysBody.typeface = UiFonts.cute(this)
        binding.sysInput.typeface = UiFonts.cute(this)
        binding.sysInput.visibility = View.VISIBLE
        binding.sysInput.hint = "写点今天的事…"

        var moodKey = "stand"
        var weatherKey = "sunny"
        var browseIdx = -1 // -1 = 写新篇；>=0 浏览已有（从新到旧）

        fun refreshBrowse() {
            val arr = AppDataStore.diaries(this)
            clearButtons()
            if (browseIdx < 0) {
                binding.sysInput.visibility = View.VISIBLE
                binding.sysBody.text = buildString {
                    appendLine("心情：${AppDataStore.moodLabel(moodKey)}")
                    appendLine("天气：${AppDataStore.weatherLabel(weatherKey)}")
                    appendLine()
                    val n = arr.length()
                    if (n == 0) append("还没有日记。选心情/天气后写下今天吧。")
                    else append("已有 $n 篇 · 点「浏览」翻看旧日记")
                }
                addBtn("心情 · ${AppDataStore.moodLabel(moodKey)}") {
                    val labels = AppDataStore.DIARY_MOODS.map { it.second }.toTypedArray()
                    AlertDialog.Builder(this)
                        .setTitle("今天的心情")
                        .setItems(labels) { _, which ->
                            moodKey = AppDataStore.DIARY_MOODS[which].first
                            refreshBrowse()
                        }
                        .show()
                }
                addBtn("天气 · ${AppDataStore.weatherLabel(weatherKey)}") {
                    val labels = AppDataStore.DIARY_WEATHER.map { it.second }.toTypedArray()
                    AlertDialog.Builder(this)
                        .setTitle("今天的天气")
                        .setItems(labels) { _, which ->
                            weatherKey = AppDataStore.DIARY_WEATHER[which].first
                            refreshBrowse()
                        }
                        .show()
                }
                addBtn("保存日记") {
                    if (AppDataStore.addDiary(
                            this,
                            binding.sysInput.text.toString(),
                            mood = moodKey,
                            weather = weatherKey,
                        )
                    ) {
                        Toast.makeText(this, "已保存", Toast.LENGTH_SHORT).show()
                        binding.sysInput.setText("")
                        browseIdx = -1
                        refreshBrowse()
                    } else {
                        Toast.makeText(this, "内容不能为空", Toast.LENGTH_SHORT).show()
                    }
                }
                if (arr.length() > 0) {
                    addBtn("浏览旧日记") {
                        browseIdx = arr.length() - 1
                        refreshBrowse()
                    }
                }
            } else {
                binding.sysInput.visibility = View.GONE
                if (arr.length() == 0) {
                    browseIdx = -1
                    refreshBrowse()
                    return
                }
                browseIdx = browseIdx.coerceIn(0, arr.length() - 1)
                val o = arr.getJSONObject(browseIdx)
                binding.sysBody.text = buildString {
                    appendLine("· ${o.optString("ts")}")
                    appendLine("心情 ${AppDataStore.moodLabel(o.optString("mood", "stand"))} · 天气 ${AppDataStore.weatherLabel(o.optString("weather", "sunny"))}")
                    appendLine()
                    append(o.optString("text"))
                    appendLine()
                    appendLine()
                    append("（${browseIdx + 1} / ${arr.length()}）")
                }
                addBtn("上一篇") {
                    if (browseIdx > 0) browseIdx--
                    refreshBrowse()
                }
                addBtn("下一篇") {
                    if (browseIdx < arr.length() - 1) browseIdx++
                    refreshBrowse()
                }
                addBtn("删除这篇") {
                    AlertDialog.Builder(this)
                        .setTitle("删除日记？")
                        .setPositiveButton("删除") { _, _ ->
                            AppDataStore.deleteDiary(this, o.optString("id"))
                            browseIdx = -1
                            refreshBrowse()
                        }
                        .setNegativeButton("取消", null)
                        .show()
                }
                addBtn("写新篇") {
                    browseIdx = -1
                    refreshBrowse()
                }
            }
            addBtn("返回") { finish() }
        }
        refreshBrowse()
    }

    private fun pageAchievements() {
        binding.sysTitle.text = "成就"
        if (PetPrefs.hasOwner(this)) AppDataStore.unlock(this, "owner_named")
        val unlocked = AppDataStore.achievements(this)
        binding.sysBody.text = AppDataStore.achievementCatalog().joinToString("\n\n") { (id, title, desc) ->
            val mark = if (id in unlocked) "✓" else "·"
            "$mark $title\n  $desc"
        }
        clearButtons()
        addBtn("返回") { finish() }
    }

    private fun pageMemory(title: String, body: String) {
        binding.sysTitle.text = title
        binding.sysBody.text = body
        AppDataStore.unlock(this, "memory_open")
        clearButtons()
        addBtn("返回") { finish() }
    }

    private fun pageGallery() {
        binding.sysTitle.text = "画廊"
        AppDataStore.unlock(this, "memory_open")
        val groups = listOf(
            "站立" to listOf("stand.png"),
            "行走" to listOf("walkfront1.png", "walkfront2.png", "walkback1.png", "walkleft1.png"),
            "表情" to listOf("happy.png", "wink.png", "shy1.png", "like.png", "squat.png"),
            "互动" to listOf("hi1.png", "eat1.png", "call1.png", "kick.png", "sleep1.png"),
            "工作" to listOf("workstand.png", "workfront1.png", "box.png", "flag.png"),
        )
        val user = UserGalleryStore.list(this)
        binding.sysBody.text = buildString {
            appendLine("内置精灵组 + 用户图库")
            appendLine()
            for ((name, files) in groups) {
                val ok = files.count { existsAsset("sprites/$it") }
                appendLine("· $name  $ok/${files.size} 帧")
            }
            appendLine()
            appendLine("用户图 ${user.size} 张")
            for (e in user.take(12)) appendLine("· ${e.title}")
            if (user.size > 12) appendLine("…")
        }
        clearButtons()
        addBtn("导入图片") { pickGalleryImage.launch("image/*") }
        for (e in user) {
            addBtn("看·${e.title.take(10)}") {
                val bmp = BitmapFactory.decodeFile(UserGalleryStore.fileOf(this, e).absolutePath)
                if (bmp == null) {
                    Toast.makeText(this, "无法打开", Toast.LENGTH_SHORT).show()
                    return@addBtn
                }
                val iv = ImageView(this).apply {
                    setImageBitmap(bmp)
                    adjustViewBounds = true
                    maxHeight = 720
                }
                AlertDialog.Builder(this)
                    .setTitle(e.title)
                    .setView(iv)
                    .setPositiveButton("好", null)
                    .setNeutralButton("删除") { _, _ ->
                        UserGalleryStore.remove(this, e.id)
                        pageGallery()
                    }
                    .show()
            }
        }
        for ((name, files) in groups) {
            addBtn("预览·$name") {
                val path = files.map { "sprites/$it" }.firstOrNull { existsAsset(it) }
                if (path == null) {
                    Toast.makeText(this, "无素材", Toast.LENGTH_SHORT).show()
                } else {
                    AlertDialog.Builder(this)
                        .setTitle(name)
                        .setMessage("资源：$path")
                        .setPositiveButton("好", null)
                        .show()
                }
            }
        }
        addBtn("返回") { finish() }
    }

    private fun pagePhonograph() {
        binding.sysTitle.text = "留声"
        AppDataStore.unlock(this, "memory_open")
        phonographPlayer = VoicePlayer(this)
        val entries = listOf(
            "问候 hi" to "voice/Vpet/hi",
            "日常 normal" to "voice/Vpet/normal",
            "工作 work" to "voice/Vpet/work",
            "睡眠 sleep" to "voice/Vpet/sleep",
            "游戏 game" to "voice/Vpet/game",
            "吃吃 eat" to "voice/Vpet/eat",
        )
        val user = UserPhonographStore.list(this)
        binding.sysBody.text = buildString {
            appendLine("内置语音 + 用户导入（wav/mp3 等）")
            appendLine("用户条目 ${user.size}")
            for (e in user.take(10)) appendLine("· ${e.title}")
        }
        clearButtons()
        addBtn("导入音频") { pickPhonographAudio.launch("audio/*") }
        for (e in user) {
            addBtn("播·${e.title.take(12)}") {
                val ok = phonographPlayer?.playFile(UserPhonographStore.fileOf(this, e)) == true
                Toast.makeText(this, if (ok) "播放：${e.title}" else "播放失败", Toast.LENGTH_SHORT).show()
            }
            addBtn("删·${e.title.take(8)}") {
                UserPhonographStore.remove(this, e.id)
                pagePhonograph()
            }
        }
        for ((label, dir) in entries) {
            addBtn(label) {
                val path = phonographPlayer?.pickAsset(dir)
                if (path == null) {
                    Toast.makeText(this, "无音频：$dir", Toast.LENGTH_SHORT).show()
                } else {
                    val ok = phonographPlayer?.playAssetPath(path) == true
                    Toast.makeText(
                        this,
                        if (ok) "播放：${path.substringAfterLast('/')}" else "播放失败",
                        Toast.LENGTH_SHORT,
                    ).show()
                }
            }
        }
        addBtn("停止") { phonographPlayer?.stop() }
        addBtn("返回") { finish() }
    }

    private fun existsAsset(path: String): Boolean = try {
        assets.open(path).close()
        true
    } catch (_: Exception) {
        false
    }

    private fun pageSettings() {
        binding.sysTitle.text = "设置"
        binding.sysBody.text = ""
        clearButtons()
        UiFonts.applyTree(binding.root)

        val fontLabels = AppDataStore.FONT_PRESETS.keys.toList()
        val fontFamilies = AppDataStore.FONT_FAMILIES
        val diffLabels = AppDataStore.DIFF_PRESETS
        val sizeSteps = (PetPrefs.SIZE_MAX_PX - PetPrefs.SIZE_MIN_PX) / PetPrefs.SIZE_STEP_PX
        val curPx = PetPrefs.sizePx(this)
        val sizeProgress = ((curPx - PetPrefs.SIZE_MIN_PX) / PetPrefs.SIZE_STEP_PX)
            .coerceIn(0, sizeSteps)

        addSliderRow(
            title = "大小",
            progress = sizeProgress,
            max = sizeSteps,
            format = { i ->
                val px = PetPrefs.SIZE_MIN_PX + i * PetPrefs.SIZE_STEP_PX
                val label = PetPrefs.nearestSizeLabel(px)
                "$label · ${PetPrefs.snapSizePx(px)}px"
            },
            onChange = { i ->
                val px = PetPrefs.SIZE_MIN_PX + i * PetPrefs.SIZE_STEP_PX
                PetPrefs.setSizePx(this, px)
                startService(
                    Intent(this, PetOverlayService::class.java).apply {
                        action = PetOverlayService.ACTION_RESIZE
                    },
                )
            },
            applyOnStop = true,
        )

        addSliderRow(
            title = "字体样式",
            progress = fontFamilies.indexOf(AppDataStore.fontFamily(this)).coerceAtLeast(0),
            max = fontFamilies.lastIndex,
            format = { i -> fontFamilies.getOrElse(i) { AppDataStore.FONT_FAMILY_DEFAULT } },
            onChange = { i ->
                AppDataStore.setFontFamily(
                    this,
                    fontFamilies.getOrElse(i) { AppDataStore.FONT_FAMILY_DEFAULT },
                )
                UiFonts.applyTree(binding.root)
            },
        )

        addSliderRow(
            title = "字体大小",
            progress = fontLabels.indexOf(AppDataStore.fontLabel(this)).coerceAtLeast(0),
            max = fontLabels.lastIndex,
            format = { i -> fontLabels.getOrElse(i) { "中" } },
            onChange = { i ->
                AppDataStore.setFontLabel(this, fontLabels.getOrElse(i) { "中" })
                UiFonts.applyTree(binding.root)
            },
        )

        addSwitchRow("文本框", AppDataStore.speechTextOn(this)) { on ->
            AppDataStore.setSpeechTextOn(this, on)
            Toast.makeText(
                this,
                if (on) "文本框：开" else "文本框：关（语音仍可播）",
                Toast.LENGTH_SHORT,
            ).show()
        }

        addSwitchRow("音效", AppDataStore.soundOn(this)) { on ->
            AppDataStore.setSoundOn(this, on)
        }
        addSwitchRow("语音", AppDataStore.voiceMode(this)) { on ->
            AppDataStore.setVoiceMode(this, on)
        }

        addSliderRow(
            title = "语音音量",
            progress = AppDataStore.voiceVolume(this),
            max = 100,
            format = { "$it%" },
            onChange = { AppDataStore.setVoiceVolume(this, it) },
        )

        addSliderRow(
            title = "难度",
            progress = diffLabels.indexOf(AppDataStore.difficulty(this)).coerceAtLeast(0),
            max = diffLabels.lastIndex,
            format = { diffLabels.getOrElse(it) { "中" } },
            onChange = { i ->
                AppDataStore.setDifficulty(this, diffLabels.getOrElse(i) { "中" })
            },
        )

        addBtn("档案 · 音乐") {
            startActivity(Intent(this, ToolsActivity::class.java))
        }
        addBtn("显示层级说明") {
            Toast.makeText(
                this,
                "手机悬浮已在系统叠加层，无需像电脑那样调窗口层级",
                Toast.LENGTH_LONG,
            ).show()
        }
        addBtn("返回") { finish() }
    }

    private fun pageAbout() {
        binding.sysTitle.text = "关于 Vpet"
        binding.sysBody.text = """
            作者菌：翛然而往
            手机试做版对照电脑 Vpet 1.0 行为复现。
            
            原作世界：《DRAMatical Murder》相关设定问答仅供粉丝向桌宠互动。
            
            GitHub：$ABOUT_REPO
        """.trimIndent()
        clearButtons()
        addBtn("打开 GitHub") { openUrl(ABOUT_REPO) }
        addBtn("小红书") { openUrl(XHS) }
        addBtn("B站") { openUrl(BILI) }
        addBtn("返回") { finish() }
    }

    private fun pageFeedback() {
        binding.sysTitle.text = "问题反馈"
        binding.sysBody.text =
            "Bug 与建议可通过 GitHub Issues / 小红书 / B站 反馈。\n请附：现象、复现步骤、机型系统。"
        clearButtons()
        addBtn("GitHub Issues") { openUrl(FEEDBACK_ISSUE) }
        addBtn("小红书") { openUrl(XHS) }
        addBtn("B站") { openUrl(BILI) }
    }

    private fun pageGuide(auto: Boolean = false) {
        binding.sysTitle.text = "操作说明"
        binding.sysBody.text = """
            【手机版要点】
            · 点立绘打开菜单（模式/面板/互动/系统）
            · 拖动移动；漫步/自由走动；跟随点空白处引路
            · 工作 / 睡眠：点开，再点结束（或 HUD 结束）
            · 音乐：系统 → 设置 → 档案·音乐 导入本地歌曲
            · 所属人与电脑 data/pet_profile.json 可互导
            · 系统：我的 / 设置 / 社区 / 重置 / 退出
            · 设置面板内调大小、字体、音效、文本框、语音、难度
            · 首次开启桌宠需「显示在其他应用上层」权限
        """.trimIndent()
        if (auto) AppConfigStore.markOperationGuideSeen(this)
        clearButtons()
        addBtn("知道了") { finish() }
    }

    private fun pageSubmit() {
        binding.sysTitle.text = "投稿创意"
        binding.sysBody.text = """
            电脑版可打包 DIY 地图/像素画/音频为 zip 投稿。
            手机版暂不支持本地打包；请用电脑版「社区→投稿创意」，或将素材发至反馈渠道。
            一经投稿默认同意无偿公开使用。
        """.trimIndent()
        clearButtons()
        addBtn("去问题反馈渠道") { openUrl(FEEDBACK_ISSUE) }
        addBtn("返回") { finish() }
    }

    private fun pageReset() {
        binding.sysTitle.text = "重置"
        binding.sysBody.text =
            "将清空日记、日程、成就标记、生日礼物、本地音乐与大小等设置。\n所属人昵称与登记时间会保留（对齐电脑版）。"
        clearButtons()
        addBtn("确定重置") {
            AlertDialog.Builder(this)
                .setTitle("确认重置？")
                .setMessage("所属人保留，其余回到初始。")
                .setPositiveButton("重置") { _, _ ->
                    AppDataStore.resetKeepOwner(this)
                    Toast.makeText(this, "已重置（所属人保留）", Toast.LENGTH_LONG).show()
                    finish()
                }
                .setNegativeButton("取消", null)
                .show()
        }
        addBtn("取消") { finish() }
    }

    private fun openUrl(url: String) {
        try {
            startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
        } catch (_: Exception) {
            Toast.makeText(this, "无法打开链接", Toast.LENGTH_SHORT).show()
        }
    }
}
