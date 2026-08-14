package com.vpet.mobile

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.text.InputFilter
import android.widget.EditText
import android.widget.FrameLayout
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.vpet.mobile.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private var ownerDialog: AlertDialog? = null

    private val notifyPermission = registerForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { /* optional for FGS notification */ }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        if (Build.VERSION.SDK_INT >= 33) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED
            ) {
                notifyPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }

        binding.btnOverlayPermission.setOnClickListener { openOverlaySettings() }
        binding.btnStartOverlay.setOnClickListener { startOverlay() }
        binding.btnStopOverlay.setOnClickListener { stopOverlay() }
        binding.btnLeaveToPet.setOnClickListener { leaveToPetOnly() }
        binding.btnOpenRoom.setOnClickListener {
            if (!ensureOwnerNamed()) return@setOnClickListener
            startActivity(Intent(this, RoomActivity::class.java))
        }
        binding.btnOpenTools.setOnClickListener {
            if (!ensureOwnerNamed()) return@setOnClickListener
            startActivity(Intent(this, ToolsActivity::class.java))
        }
        binding.btnSizeS.setOnClickListener { applySize("小") }
        binding.btnSizeM.setOnClickListener { applySize("中") }
        binding.btnSizeL.setOnClickListener { applySize("大") }
        refreshStatus()
        refreshSizeHints()
        maybePromptOwner()
        PetProfileStore.checkBirthdayToasts(this).let { msgs ->
            if (msgs.isNotEmpty()) BirthdayGiftUi.showMessages(this, msgs)
        }
        FoodInventoryStore.ensureSeeded(this)
        if (WalletStore.tryDailyLoginCoin(this)) {
            Toast.makeText(this, "每日登录礼：金币 +1", Toast.LENGTH_SHORT).show()
        }
    }

    override fun onResume() {
        super.onResume()
        refreshStatus()
        refreshSizeHints()
        maybePromptOwner()
    }

    private fun maybePromptOwner() {
        if (PetPrefs.hasOwner(this)) return
        if (ownerDialog?.isShowing == true) return
        val pad = (20 * resources.displayMetrics.density).toInt()
        val input = EditText(this).apply {
            hint = "昵称（最多 ${PetPrefs.OWNER_NAME_MAX_LEN} 字）"
            filters = arrayOf(InputFilter.LengthFilter(PetPrefs.OWNER_NAME_MAX_LEN))
            setSingleLine()
        }
        val wrap = FrameLayout(this).apply {
            setPadding(pad, pad / 2, pad, 0)
            addView(input)
        }
        ownerDialog = AlertDialog.Builder(this)
            .setTitle("所属人")
            .setMessage("请登记所属人昵称（仅一次，不可修改）。认主后才能启动桌宠。")
            .setView(wrap)
            .setCancelable(false)
            .setPositiveButton("确定", null)
            .create()
            .also { dialog ->
                dialog.setOnShowListener {
                    dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener {
                        if (PetPrefs.setOwnerName(this, input.text.toString())) {
                            Toast.makeText(
                                this,
                                "认主成功，你好，${PetPrefs.ownerName(this)}",
                                Toast.LENGTH_SHORT,
                            ).show()
                            dialog.dismiss()
                            ownerDialog = null
                            refreshStatus()
                            startActivity(
                                Intent(this, SystemHubActivity::class.java)
                                    .putExtra(SystemHubActivity.EXTRA_PAGE, "guide")
                                    .putExtra(SystemHubActivity.EXTRA_AUTO_GUIDE, true),
                            )
                        } else {
                            Toast.makeText(this, "请输入有效昵称", Toast.LENGTH_SHORT).show()
                        }
                    }
                }
                dialog.show()
            }
    }

    private fun ensureOwnerNamed(): Boolean {
        if (PetPrefs.hasOwner(this)) return true
        Toast.makeText(this, "请先登记所属人", Toast.LENGTH_SHORT).show()
        maybePromptOwner()
        return false
    }

    private fun applySize(label: String) {
        PetPrefs.setSizeLabel(this, label)
        refreshSizeHints()
        val intent = Intent(this, PetOverlayService::class.java).apply {
            action = PetOverlayService.ACTION_RESIZE
        }
        startService(intent)
        Toast.makeText(
            this,
            "大小：$label（${PetPrefs.sizePx(this)}px）",
            Toast.LENGTH_SHORT,
        ).show()
    }

    private fun refreshSizeHints() {
        val cur = PetPrefs.sizeLabel(this)
        binding.btnSizeS.alpha = if (cur == "小") 1f else 0.55f
        binding.btnSizeM.alpha = if (cur == "中") 1f else 0.55f
        binding.btnSizeL.alpha = if (cur == "大") 1f else 0.55f
    }

    private fun refreshStatus() {
        val ok = Settings.canDrawOverlays(this)
        val owner = PetPrefs.ownerName(this)
        val ownerLine = if (owner.isNotEmpty()) {
            "所属人：$owner · 相伴第 ${PetPrefs.companionDays(this)} 天"
        } else {
            "所属人：未登记"
        }
        binding.statusText.text = if (ok) {
            "$ownerLine\n悬浮权限：已开启。大小=${PetPrefs.sizeLabel(this)}。"
        } else {
            "$ownerLine\n${getString(R.string.need_overlay)}"
        }
        binding.btnStartOverlay.isEnabled = ok && PetPrefs.hasOwner(this)
    }

    private fun openOverlaySettings() {
        val intent = Intent(
            Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
            Uri.parse("package:$packageName"),
        )
        startActivity(intent)
    }

    private fun startOverlay() {
        if (!ensureOwnerNamed()) return
        if (!Settings.canDrawOverlays(this)) {
            Toast.makeText(this, R.string.need_overlay, Toast.LENGTH_LONG).show()
            openOverlaySettings()
            return
        }
        val intent = Intent(this, PetOverlayService::class.java).apply {
            action = PetOverlayService.ACTION_START
        }
        ContextCompat.startForegroundService(this, intent)
        Toast.makeText(this, R.string.overlay_started_hint, Toast.LENGTH_SHORT).show()
        // Phase 0：关掉 App 页，只留悬浮桌宠（点宠操作）
        finishAndRemoveTask()
    }

    private fun stopOverlay() {
        val intent = Intent(this, PetOverlayService::class.java).apply {
            action = PetOverlayService.ACTION_STOP
        }
        startService(intent)
        Toast.makeText(this, "已关闭悬浮桌宠", Toast.LENGTH_SHORT).show()
    }

    /** 桌宠已在跑时，再次进启动页可一键离开，回到纯悬浮。 */
    private fun leaveToPetOnly() {
        if (!Settings.canDrawOverlays(this)) {
            Toast.makeText(this, R.string.need_overlay, Toast.LENGTH_LONG).show()
            return
        }
        // 确保服务在跑
        val intent = Intent(this, PetOverlayService::class.java).apply {
            action = PetOverlayService.ACTION_START
        }
        ContextCompat.startForegroundService(this, intent)
        finishAndRemoveTask()
    }
}
