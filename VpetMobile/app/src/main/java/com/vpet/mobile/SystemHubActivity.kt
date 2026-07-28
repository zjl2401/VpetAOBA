package com.vpet.mobile

import android.content.Intent
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.ImageView
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

    private fun addBtn(label: String, onClick: () -> Unit) {
        binding.sysButtons.addView(
            Button(this).apply {
                text = label
                setOnClickListener { onClick() }
            },
        )
    }

    private fun pageDiary() {
        binding.sysTitle.text = "日记"
        binding.sysInput.visibility = View.VISIBLE
        binding.sysInput.hint = "写点今天的事…"
        refreshDiaryBody()
        clearButtons()
        addBtn("保存日记") {
            if (AppDataStore.addDiary(this, binding.sysInput.text.toString())) {
                Toast.makeText(this, "已保存", Toast.LENGTH_SHORT).show()
                binding.sysInput.setText("")
                refreshDiaryBody()
            } else {
                Toast.makeText(this, "内容不能为空", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun refreshDiaryBody() {
        val arr = AppDataStore.diaries(this)
        binding.sysBody.text = if (arr.length() == 0) {
            "还没有日记。"
        } else {
            buildString {
                for (i in arr.length() - 1 downTo 0) {
                    val o = arr.getJSONObject(i)
                    appendLine("· ${o.optString("ts")}")
                    appendLine(o.optString("text"))
                    appendLine()
                }
            }
        }
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
        fun refresh() {
            binding.sysBody.text = buildString {
                appendLine("桌宠大小：${PetPrefs.sizeLabel(this@SystemHubActivity)}（${PetPrefs.sizePx(this@SystemHubActivity)}px）")
                appendLine("字体大小：${AppDataStore.fontLabel(this@SystemHubActivity)}")
                appendLine("音效：${if (AppDataStore.soundOn(this@SystemHubActivity)) "开" else "关"}")
                appendLine("语音模式：${if (AppDataStore.voiceMode(this@SystemHubActivity)) "开" else "关"}")
                appendLine("语音音量：${AppDataStore.voiceVolume(this@SystemHubActivity)}")
                appendLine("游戏难度：${AppDataStore.difficulty(this@SystemHubActivity)}")
                appendLine("显示层级：手机悬浮窗已置顶，无需调整")
            }
        }
        refresh()
        clearButtons()
        listOf("小", "中", "大").forEach { label ->
            addBtn("大小·$label") {
                PetPrefs.setSizeLabel(this, label)
                startService(
                    Intent(this, PetOverlayService::class.java).apply {
                        action = PetOverlayService.ACTION_RESIZE
                    },
                )
                refresh()
            }
        }
        AppDataStore.FONT_PRESETS.keys.forEach { label ->
            addBtn("字体·$label") {
                AppDataStore.setFontLabel(this, label)
                refresh()
            }
        }
        addBtn("音效 开/关") {
            AppDataStore.setSoundOn(this, !AppDataStore.soundOn(this))
            refresh()
        }
        addBtn("语音模式 开/关") {
            AppDataStore.setVoiceMode(this, !AppDataStore.voiceMode(this))
            refresh()
        }
        addBtn("语音音量 −") {
            AppDataStore.setVoiceVolume(this, AppDataStore.voiceVolume(this) - 10)
            refresh()
        }
        addBtn("语音音量 +") {
            AppDataStore.setVoiceVolume(this, AppDataStore.voiceVolume(this) + 10)
            refresh()
        }
        AppDataStore.DIFF_PRESETS.forEach { d ->
            addBtn("难度·$d") {
                AppDataStore.setDifficulty(this, d)
                refresh()
            }
        }
        addBtn("显示层级说明") {
            Toast.makeText(
                this,
                "手机悬浮已在系统叠加层，无需像电脑那样调窗口层级",
                Toast.LENGTH_LONG,
            ).show()
        }
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
            · 点立绘打开四大模块菜单（模式/面板/互动/系统）
            · 拖动移动；漫步/自由走动；跟随点空白处引路
            · 工作：运送箱到旗；番茄钟=工作运送↔休息睡眠
            · 音乐：先在「工具与档案」导入本地歌曲（网易云云端不可直连）
            · 所属人与电脑 data/pet_profile.json 可互导
            · 家园 layout 可存读，与电脑 home_layout.json 互导
            · 系统→我的：日记/成就/画廊/留声；设置：大小字体声音难度
            · 悬浮需系统「显示在其他应用上层」权限
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
