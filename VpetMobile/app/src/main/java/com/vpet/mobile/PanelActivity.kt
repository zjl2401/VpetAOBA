package com.vpet.mobile

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.vpet.mobile.databinding.ActivityPanelBinding

/**
 * 面板：体力/心情 + 可折叠背包。
 * 点食物：扣 1 份、加体心，并通知悬浮桌宠播 eat（只喂苍叶）。
 */
class PanelActivity : AppCompatActivity() {
    private lateinit var binding: ActivityPanelBinding
    private var bagOpen = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityPanelBinding.inflate(layoutInflater)
        setContentView(binding.root)
        FoodInventoryStore.ensureSeeded(this)
        if (WalletStore.tryDailyLoginCoin(this)) {
            Toast.makeText(this, "每日登录礼：金币 +1", Toast.LENGTH_SHORT).show()
        }
        refresh()
        binding.btnToggleBag.setOnClickListener {
            bagOpen = !bagOpen
            binding.bagList.visibility = if (bagOpen) View.VISIBLE else View.GONE
            binding.btnToggleBag.text = if (bagOpen) "背包 ▼" else "背包 ▶"
            if (bagOpen) rebuildBag()
        }
        binding.btnPanelClose.setOnClickListener { finish() }
    }

    override fun onResume() {
        super.onResume()
        refresh()
        if (bagOpen) rebuildBag()
    }

    private fun refresh() {
        val s = AppDataStore.stamina(this)
        val m = AppDataStore.mood(this)
        val persona = if (AppDataStore.isJinmu(this)) "金目" else "默认"
        val coins = WalletStore.coins(this)
        val boxes = WalletStore.itemCount(this, WalletStore.ITEM_WORK_BOX)
        val delivered = WalletStore.workBoxesTotal(this)
        binding.panelStats.text =
            "人格：$persona\n体力：$s / 100\n心情：$m / 100\n" +
                "难度：${AppDataStore.difficulty(this)}\n" +
                "金币：$coins · 工作宝箱：$boxes\n" +
                "生涯运送：$delivered 箱（每 25 箱得 1 宝箱）"
        binding.barStamina.progress = s
        binding.barMood.progress = m
    }

    private fun rebuildBag() {
        val list = binding.bagList
        list.removeAllViews()
        // 工作宝箱
        val boxN = WalletStore.itemCount(this, WalletStore.ITEM_WORK_BOX)
        list.addView(
            makeRow("🎁 工作宝箱 ×$boxN", boxN > 0, onClick = {
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
            list.addView(makeRow("🪵 木材 ×$wood", false, onClick = {}))
        }
        val flowers = WalletStore.itemCount(this, "flower_cut")
        val wearing = PetProfileStore.wearingFlower(this)
        list.addView(
            makeRow(
                "🌸 采下的花 ×$flowers · ${if (wearing) "戴着（点摘）" else "点戴头顶"}",
                flowers > 0 || wearing,
                onClick = {
                    val msg = PetProfileStore.toggleWearFlower(this)
                    Toast.makeText(this, msg, Toast.LENGTH_SHORT).show()
                    // 通知悬浮刷新头顶花
                    startService(
                        Intent(this, PetOverlayService::class.java).setAction(PetOverlayService.ACTION_SYNC_FLOWER),
                    )
                    refresh()
                    rebuildBag()
                },
            ),
        )
        for (f in FoodCatalog.ALL) {
            val n = FoodInventoryStore.count(this, f.id)
            list.addView(
                makeRow(
                    "${f.emoji} ${f.label} ×$n  ·体+${f.stamina} 心+${f.mood}\n（点按直喂 · 长按拖到桌宠）",
                    n > 0,
                    onClick = { feed(f.id) },
                    onLong = { startDragFeed(f.id) },
                ),
            )
        }
    }

    private fun makeRow(
        label: String,
        enabled: Boolean,
        onClick: () -> Unit,
        onLong: (() -> Unit)? = null,
    ): Button {
        return Button(this).apply {
            text = label
            isEnabled = enabled
            alpha = if (enabled) 1f else 0.45f
            textSize = 13f
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT,
            ).also { it.bottomMargin = 6 }
            setOnClickListener { onClick() }
            if (onLong != null) {
                setOnLongClickListener {
                    onLong()
                    true
                }
            }
        }
    }

    /** 长按：进入拖喂（到悬浮桌宠上点一下喂；数值在松手时扣）。 */
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
        // 只喂苍叶：数值始终加给主宠；伴侣不吃
        AppDataStore.addStaminaMood(this, food.stamina, food.mood)
        Toast.makeText(
            this,
            "喂苍叶：${food.label}（体+${food.stamina} 心+${food.mood}）",
            Toast.LENGTH_SHORT,
        ).show()
        // 通知悬浮播 eat
        val i = Intent(this, PetOverlayService::class.java).apply {
            action = PetOverlayService.ACTION_FEED
            putExtra(PetOverlayService.EXTRA_FOOD_ID, foodId)
        }
        startService(i)
        refresh()
        rebuildBag()
    }
}
