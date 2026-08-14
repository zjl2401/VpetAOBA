package com.vpet.mobile

import android.content.Intent
import android.os.Bundle
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.Button
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.vpet.mobile.databinding.ActivityPanelBinding

/**
 * 状态面板：紧凑浮窗（对照桌面 PANEL_VIEW），点外侧关闭。
 * 体力/心情 + 可折叠背包；点食物喂苍叶（像素图标）。
 */
class PanelActivity : AppCompatActivity() {
    private lateinit var binding: ActivityPanelBinding
    private var bagOpen = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityPanelBinding.inflate(layoutInflater)
        setContentView(binding.root)
        applyCompactWindow()
        FoodInventoryStore.ensureSeeded(this)
        if (WalletStore.tryDailyLoginCoin(this)) {
            Toast.makeText(this, "每日登录礼：金币 +1", Toast.LENGTH_SHORT).show()
        }
        applyFonts()
        refresh()
        binding.btnToggleBag.setOnClickListener {
            bagOpen = !bagOpen
            binding.bagScroll.visibility = if (bagOpen) View.VISIBLE else View.GONE
            binding.bagHint.visibility = if (bagOpen) View.VISIBLE else View.GONE
            binding.btnToggleBag.text = if (bagOpen) "背包 ▼" else "背包 ▶"
            if (bagOpen) {
                rebuildBag()
                applyBagMaxHeight()
            }
        }
        binding.btnPanelClose.setOnClickListener { finish() }
    }

    private fun applyCompactWindow() {
        val dm = resources.displayMetrics
        val width = (dm.widthPixels * 0.78f).toInt().coerceIn(
            dp(260),
            (dm.widthPixels * 0.92f).toInt(),
        )
        window.setLayout(width, WindowManager.LayoutParams.WRAP_CONTENT)
        window.setGravity(Gravity.CENTER)
        setFinishOnTouchOutside(true)
    }

    private fun applyBagMaxHeight() {
        val maxH = (resources.displayMetrics.heightPixels * 0.42f).toInt()
        binding.bagScroll.layoutParams = binding.bagScroll.layoutParams.apply {
            height = maxH
        }
        binding.bagScroll.requestLayout()
    }

    private fun dp(v: Int): Int =
        TypedValue.applyDimension(
            TypedValue.COMPLEX_UNIT_DIP,
            v.toFloat(),
            resources.displayMetrics,
        ).toInt()

    /** 跟随系统「字体大小」设置，各层级相对偏移（与菜单统一）。 */
    private fun applyFonts() {
        AppDataStore.applySp(binding.panelTitle, AppDataStore.fontTitleSp(this))
        AppDataStore.applySp(binding.btnPanelClose, AppDataStore.fontBodySp(this))
        AppDataStore.applySp(binding.panelStats, AppDataStore.fontBodySp(this))
        AppDataStore.applySp(binding.labelStamina, AppDataStore.fontCaptionSp(this))
        AppDataStore.applySp(binding.labelMood, AppDataStore.fontCaptionSp(this))
        AppDataStore.applySp(binding.btnToggleBag, AppDataStore.fontBodySp(this))
        AppDataStore.applySp(binding.bagHint, AppDataStore.fontHintSp(this))
    }

    override fun onResume() {
        super.onResume()
        applyFonts()
        refresh()
        if (bagOpen) {
            rebuildBag()
            applyBagMaxHeight()
        }
    }

    private fun refresh() {
        val s = AppDataStore.stamina(this)
        val m = AppDataStore.mood(this)
        val persona = if (AppDataStore.isJinmu(this)) "金目" else "默认"
        val coins = WalletStore.coins(this)
        val boxes = WalletStore.itemCount(this, WalletStore.ITEM_WORK_BOX)
        val delivered = WalletStore.workBoxesTotal(this)
        binding.panelStats.text =
            "人格 $persona · 难度 ${AppDataStore.difficulty(this)}\n" +
                "体力 $s  心情 $m  ·  金币 $coins · 宝箱 $boxes\n" +
                "生涯运送 $delivered（每 25 箱得 1 宝箱）\n" +
                MusicAffinityStore.summaryLine(this)
        binding.barStamina.progress = s
        binding.barMood.progress = m
    }

    private fun rebuildBag() {
        val list = binding.bagList
        list.removeAllViews()
        val rowSp = AppDataStore.fontBodySp(this)
        val boxN = WalletStore.itemCount(this, WalletStore.ITEM_WORK_BOX)
        list.addView(
            makeRow("🎁 工作宝箱 ×$boxN", boxN > 0, rowSp, onClick = {
                val msg = WalletStore.openWorkRewardBox(this)
                if (msg == null) {
                    Toast.makeText(this, "没有宝箱", Toast.LENGTH_SHORT).show()
                } else {
                    Toast.makeText(this, msg, Toast.LENGTH_LONG).show()
                    refresh()
                    rebuildBag()
                }
            }),
        )
        val wood = WalletStore.itemCount(this, WalletStore.ITEM_WOOD)
        if (wood > 0) {
            list.addView(makeRow("🪵 木材 ×$wood", false, rowSp, onClick = {}))
        }
        val flowers = WalletStore.itemCount(this, "flower_cut")
        val wearing = PetProfileStore.wearingFlower(this)
        list.addView(
            makeRow(
                "🌸 花 ×$flowers · ${if (wearing) "戴着（点摘）" else "点戴头顶"}",
                flowers > 0 || wearing,
                rowSp,
                onClick = {
                    val msg = PetProfileStore.toggleWearFlower(this)
                    Toast.makeText(this, msg, Toast.LENGTH_SHORT).show()
                    startService(
                        Intent(this, PetOverlayService::class.java).setAction(PetOverlayService.ACTION_SYNC_FLOWER),
                    )
                    refresh()
                    rebuildBag()
                },
            ),
        )
        val iconPx = dp(26)
        for (f in FoodCatalog.ALL) {
            val n = FoodInventoryStore.count(this, f.id)
            list.addView(
                makeFoodRow(
                    f,
                    n,
                    rowSp,
                    iconPx,
                    onClick = { feed(f.id) },
                    onLong = { startDragFeed(f.id) },
                ),
            )
        }
    }

    private fun makeRow(
        label: String,
        enabled: Boolean,
        textSp: Float,
        onClick: () -> Unit,
        onLong: (() -> Unit)? = null,
    ): Button {
        return Button(this).apply {
            text = label
            isEnabled = enabled
            alpha = if (enabled) 1f else 0.45f
            AppDataStore.applySp(this, textSp)
            minHeight = 0
            minimumHeight = dp(40)
            setPadding(dp(10), dp(6), dp(10), dp(6))
            layoutParams = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
            ).also { it.bottomMargin = dp(4) }
            setOnClickListener { onClick() }
            if (onLong != null) {
                setOnLongClickListener {
                    onLong()
                    true
                }
            }
        }
    }

    private fun makeFoodRow(
        food: FoodCatalog.Food,
        count: Int,
        textSp: Float,
        iconPx: Int,
        onClick: () -> Unit,
        onLong: () -> Unit,
    ): View {
        val enabled = count > 0
        return LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(8), dp(6), dp(8), dp(6))
            alpha = if (enabled) 1f else 0.45f
            isEnabled = enabled
            setBackgroundColor(0xE01A2233.toInt())
            layoutParams = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
            ).also { it.bottomMargin = dp(4) }
            addView(
                ImageView(this@PanelActivity).apply {
                    setImageBitmap(FoodPixelArt.bitmapFor(food.id, iconPx))
                    layoutParams = LinearLayout.LayoutParams(iconPx, iconPx).also {
                        it.marginEnd = dp(8)
                    }
                    scaleType = ImageView.ScaleType.FIT_CENTER
                },
            )
            addView(
                TextView(this@PanelActivity).apply {
                    text = "${food.label} ×$count  体+${food.stamina} 心+${food.mood}"
                    setTextColor(0xFFEEF2FF.toInt())
                    AppDataStore.applySp(this, textSp)
                    layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
                },
            )
            if (enabled) {
                setOnClickListener { onClick() }
                setOnLongClickListener {
                    onLong()
                    true
                }
            }
        }
    }

    private fun startDragFeed(foodId: String) {
        val food = FoodCatalog.byId(foodId) ?: return
        if (FoodInventoryStore.count(this, foodId) <= 0) {
            Toast.makeText(this, "没有${food.label}了", Toast.LENGTH_SHORT).show()
            return
        }
        val i = Intent(this, PetOverlayService::class.java).apply {
            action = PetOverlayService.ACTION_FEED_DRAG
            putExtra(PetOverlayService.EXTRA_FOOD_ID, foodId)
        }
        startService(i)
        Toast.makeText(this, "拿起${food.label} · 回到桌宠点一下喂食", Toast.LENGTH_SHORT).show()
        finish()
    }

    private fun feed(foodId: String) {
        val food = FoodCatalog.byId(foodId) ?: return
        if (!FoodInventoryStore.consumeOne(this, foodId)) {
            Toast.makeText(this, "没有${food.label}了", Toast.LENGTH_SHORT).show()
            return
        }
        AppDataStore.addStaminaMood(this, food.stamina, food.mood)
        Toast.makeText(
            this,
            "喂苍叶：${food.label}（体+${food.stamina} 心+${food.mood}）",
            Toast.LENGTH_SHORT,
        ).show()
        val i = Intent(this, PetOverlayService::class.java).apply {
            action = PetOverlayService.ACTION_FEED
            putExtra(PetOverlayService.EXTRA_FOOD_ID, foodId)
        }
        startService(i)
        refresh()
        rebuildBag()
    }
}
