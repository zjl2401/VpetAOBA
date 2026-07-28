package com.vpet.mobile

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.provider.OpenableColumns
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.vpet.mobile.databinding.ActivityToolsBinding

/**
 * 档案同步 / 本地音乐 / 日程 / 生日（不做天气预报）。
 */
class ToolsActivity : AppCompatActivity() {

    private lateinit var binding: ActivityToolsBinding
    private var forceOwnerOnImport = false

    private val importProfile = registerForActivityResult(
        ActivityResultContracts.OpenDocument(),
    ) { uri ->
        if (uri == null) return@registerForActivityResult
        try {
            val text = contentResolver.openInputStream(uri)?.bufferedReader()?.readText() ?: return@registerForActivityResult
            val msg = PetProfileStore.importJson(this, text, forceOwner = forceOwnerOnImport)
            Toast.makeText(this, msg, Toast.LENGTH_LONG).show()
            refresh()
        } catch (e: Exception) {
            Toast.makeText(this, "导入失败：${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    private val exportProfile = registerForActivityResult(
        ActivityResultContracts.CreateDocument("application/json"),
    ) { uri ->
        if (uri == null) return@registerForActivityResult
        try {
            contentResolver.openOutputStream(uri)?.use {
                it.write(PetProfileStore.exportJson(this).toByteArray(Charsets.UTF_8))
            }
            Toast.makeText(this, "已导出 pet_profile.json，可拷到电脑版 data/ 覆盖或合并", Toast.LENGTH_LONG).show()
        } catch (e: Exception) {
            Toast.makeText(this, "导出失败：${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    private val pickMusic = registerForActivityResult(
        ActivityResultContracts.OpenDocument(),
    ) { uri ->
        if (uri == null) return@registerForActivityResult
        try {
            contentResolver.takePersistableUriPermission(
                uri,
                Intent.FLAG_GRANT_READ_URI_PERMISSION,
            )
        } catch (_: Exception) {
        }
        val title = queryDisplayName(uri) ?: "本地歌曲"
        PetProfileStore.setMusic(this, uri.toString(), title)
        Toast.makeText(this, "已导入：$title", Toast.LENGTH_SHORT).show()
        refresh()
    }

    private val exportAch = registerForActivityResult(
        ActivityResultContracts.CreateDocument("application/json"),
    ) { uri ->
        if (uri == null) return@registerForActivityResult
        try {
            contentResolver.openOutputStream(uri)?.use {
                it.write(ModeTimeStore.exportAchievementsPatch(this).toByteArray(Charsets.UTF_8))
            }
            Toast.makeText(this, "已导出 achievements 片段（含 mode_seconds）", Toast.LENGTH_LONG).show()
        } catch (e: Exception) {
            Toast.makeText(this, "导出失败：${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    private val importAch = registerForActivityResult(
        ActivityResultContracts.OpenDocument(),
    ) { uri ->
        if (uri == null) return@registerForActivityResult
        try {
            val text = contentResolver.openInputStream(uri)?.bufferedReader()?.readText()
                ?: return@registerForActivityResult
            val msg = ModeTimeStore.importAchievementsJson(this, text)
            Toast.makeText(this, msg, Toast.LENGTH_LONG).show()
            refresh()
        } catch (e: Exception) {
            Toast.makeText(this, "导入失败：${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityToolsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.btnExportProfile.setOnClickListener {
            exportProfile.launch("pet_profile.json")
        }
        binding.btnImportProfile.setOnClickListener {
            forceOwnerOnImport = false
            importProfile.launch(arrayOf("application/json", "text/*", "*/*"))
        }
        binding.btnForceOwner.setOnClickListener {
            forceOwnerOnImport = true
            importProfile.launch(arrayOf("application/json", "text/*", "*/*"))
        }
        binding.btnExportAch.setOnClickListener {
            exportAch.launch("achievements.json")
        }
        binding.btnImportAch.setOnClickListener {
            importAch.launch(arrayOf("application/json", "text/*", "*/*"))
        }
        binding.btnPickMusic.setOnClickListener {
            pickMusic.launch(arrayOf("audio/*", "audio/mpeg", "audio/mp4", "*/*"))
        }
        binding.btnAddSchedule.setOnClickListener {
            val ok = PetProfileStore.addSchedule(
                this,
                binding.scheduleTime.text.toString(),
                binding.scheduleText.text.toString(),
            )
            Toast.makeText(
                this,
                if (ok) "已添加日程" else "时间格式用 HH:MM，内容不能空",
                Toast.LENGTH_SHORT,
            ).show()
            if (ok) {
                binding.scheduleText.setText("")
                refresh()
            }
        }
        binding.btnSaveBless.setOnClickListener {
            val m = binding.blessMonth.text.toString().toIntOrNull() ?: 0
            val d = binding.blessDay.text.toString().toIntOrNull() ?: 0
            if (m !in 1..12 || d !in 1..31) {
                Toast.makeText(this, "请填写有效月/日", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            PetProfileStore.setBless(this, m, d, binding.blessMsg.text.toString())
            Toast.makeText(this, "已保存所属人生日", Toast.LENGTH_SHORT).show()
            refresh()
        }
        binding.btnSaveGift.setOnClickListener {
            PetProfileStore.setGiftText(this, binding.giftText.text.toString())
            Toast.makeText(this, "已保存礼物（苍叶生日 4/22）", Toast.LENGTH_SHORT).show()
            refresh()
        }
        refresh()
    }

    private fun refresh() {
        val name = PetPrefs.ownerName(this)
        val days = PetPrefs.companionDays(this)
        val p = PetProfileStore.profile(this)
        binding.profileSummary.text = buildString {
            append("所属人：${name.ifEmpty { "未登记" }}")
            if (days > 0) append(" · 相伴第 $days 天")
            append("\n登记时间：${p.optString("owner_set_at").ifEmpty { "—" }}")
            append("\n${ModeTimeStore.detailText(this@ToolsActivity)}")
            append("\n所属人生日：${p.optInt("bless_month")}/${p.optInt("bless_day")}")
            append(" · 礼物：${p.optString("gift_text").ifEmpty { "—" }}")
        }
        binding.musicLabel.text = PetProfileStore.musicUri(this)?.let {
            "当前：${PetProfileStore.musicTitle(this).ifEmpty { it }}"
        } ?: "当前：未导入（音乐模式将提示选歌）"
        val arr = PetProfileStore.schedules(this)
        binding.scheduleList.text = if (arr.length() == 0) {
            "暂无日程"
        } else {
            buildString {
                for (i in 0 until arr.length()) {
                    val o = arr.getJSONObject(i)
                    appendLine("${o.optString("time")}  ${o.optString("text")}")
                }
            }
        }
        if (p.optInt("bless_month") > 0) {
            binding.blessMonth.setText(p.optInt("bless_month").toString())
            binding.blessDay.setText(p.optInt("bless_day").toString())
            binding.blessMsg.setText(p.optString("bless_message"))
        }
        binding.giftText.setText(p.optString("gift_text"))
    }

    private fun queryDisplayName(uri: Uri): String? {
        contentResolver.query(uri, null, null, null, null)?.use { c ->
            val idx = c.getColumnIndex(OpenableColumns.DISPLAY_NAME)
            if (idx >= 0 && c.moveToFirst()) return c.getString(idx)
        }
        return null
    }
}
