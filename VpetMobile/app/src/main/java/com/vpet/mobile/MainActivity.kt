package com.vpet.mobile

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.text.InputFilter
import android.view.View
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
        runCatching { VpetSharedInit.init(applicationContext) }
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        UiFonts.applyTree(binding.root)

        if (Build.VERSION.SDK_INT >= 33) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED
            ) {
                notifyPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }

        binding.btnClosePage.setOnClickListener { finishAndRemoveTask() }
        binding.btnStartOverlay.setOnClickListener { startOverlay() }
        binding.dataStream.start()
        refreshStatus()
        maybePromptOwner()
        PetProfileStore.checkBirthdayToasts(this).forEach {
            Toast.makeText(this, it, Toast.LENGTH_LONG).show()
        }
        FoodInventoryStore.ensureSeeded(this)
        if (WalletStore.tryDailyLoginCoin(this)) {
            Toast.makeText(this, "每日登录礼：金币 +1", Toast.LENGTH_SHORT).show()
        }
    }

    override fun onResume() {
        super.onResume()
        binding.dataStream.start()
        refreshStatus()
        maybePromptOwner()
    }

    override fun onPause() {
        binding.dataStream.stop()
        super.onPause()
    }

    private fun maybePromptOwner() {
        if (PetPrefs.hasOwner(this)) return
        if (ownerDialog?.isShowing == true) return
        val pad = (20 * resources.displayMetrics.density).toInt()
        val input = EditText(this).apply {
            hint = "昵称（最多 ${PetPrefs.OWNER_NAME_MAX_LEN} 字）"
            filters = arrayOf(InputFilter.LengthFilter(PetPrefs.OWNER_NAME_MAX_LEN))
            setSingleLine()
            typeface = UiFonts.cute(this@MainActivity)
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

    private fun refreshStatus() {
        val owner = PetPrefs.ownerName(this)
        if (owner.isNotEmpty()) {
            binding.statusText.visibility = View.VISIBLE
            binding.statusText.text = "所属人：$owner · 相伴第 ${PetPrefs.companionDays(this)} 天"
        } else {
            binding.statusText.visibility = View.GONE
        }
        // 有所属人即可点；无权限时点按再弹窗引导
        binding.btnStartOverlay.isEnabled = PetPrefs.hasOwner(this)
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
            AlertDialog.Builder(this)
                .setTitle("需要悬浮窗权限")
                .setMessage("开启桌宠需要允许「显示在其他应用上层」。去系统设置打开后，再点一次「开启桌宠」即可。")
                .setPositiveButton("去开启") { _, _ -> openOverlaySettings() }
                .setNegativeButton("取消", null)
                .show()
            return
        }
        val intent = Intent(this, PetOverlayService::class.java).apply {
            action = PetOverlayService.ACTION_START
        }
        ContextCompat.startForegroundService(this, intent)
        Toast.makeText(this, R.string.overlay_started_hint, Toast.LENGTH_SHORT).show()
        finishAndRemoveTask()
    }
}
