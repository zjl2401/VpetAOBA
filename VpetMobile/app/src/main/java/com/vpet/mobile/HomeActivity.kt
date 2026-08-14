package com.vpet.mobile

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.View
import android.widget.Button
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.vpet.mobile.databinding.ActivityHomeBinding
import org.json.JSONObject

/** 家园：布置 + 经营（锄种浇收砍钓采）。 */
class HomeActivity : AppCompatActivity() {
    private lateinit var binding: ActivityHomeBinding
    private lateinit var animator: PetAnimator
    private lateinit var layout: JSONObject
    private var voice: VoicePlayer? = null
    private val handler = Handler(Looper.getMainLooper())

    private var farmMode = false
    private var tool = HomeFarmEngine.Tool.TILL
    private var seedId = "seed_wheat"
    private lateinit var farmGrid: Array<Array<JSONObject?>>
    private lateinit var tillHits: MutableMap<String, Int>
    private lateinit var chopJobs: MutableMap<String, JSONObject>
    private lateinit var treeRegrow: MutableList<JSONObject>
    private lateinit var crafted: MutableList<String>

    /** 钓鱼：等待上钩 / 已上钩待确认 */
    private var fishWaiting = false
    private var fishBite = false
    private var fishStandX = 0
    private var fishStandY = 0

    private val tickFarm = object : Runnable {
        override fun run() {
            if (!::farmGrid.isInitialized) return
            HomeFarmEngine.advanceFarm(farmGrid)
            val n = HomeFarmEngine.processTreeRegrow(
                binding.homeScene.outdoorTileOps(),
                treeRegrow,
                binding.homeScene.cols,
                binding.homeScene.rows,
            )
            if (n > 0) Toast.makeText(this@HomeActivity, "树再生 ×$n", Toast.LENGTH_SHORT).show()
            binding.homeScene.farmGrid = farmGrid
            binding.homeScene.invalidate()
            if (farmMode) refreshFarmHud()
            handler.postDelayed(this, 2000L)
        }
    }

    private val importLayout = registerForActivityResult(
        ActivityResultContracts.OpenDocument(),
    ) { uri ->
        if (uri == null) return@registerForActivityResult
        try {
            val text = contentResolver.openInputStream(uri)?.bufferedReader()?.readText()
                ?: return@registerForActivityResult
            layout = HomeLayoutStore.importJson(this, text)
            reloadFarmFromLayout()
            binding.homeScene.applyLayout(layout)
            placePet()
            Toast.makeText(this, "已导入家园 layout", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            Toast.makeText(this, "导入失败：${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    private val exportLayout = registerForActivityResult(
        ActivityResultContracts.CreateDocument("application/json"),
    ) { uri ->
        if (uri == null) return@registerForActivityResult
        try {
            persistLayout()
            contentResolver.openOutputStream(uri)?.use {
                it.write(HomeLayoutStore.exportJson(this).toByteArray(Charsets.UTF_8))
            }
            Toast.makeText(this, "已导出 home_layout.json", Toast.LENGTH_LONG).show()
        } catch (e: Exception) {
            Toast.makeText(this, "导出失败：${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityHomeBinding.inflate(layoutInflater)
        setContentView(binding.root)
        OverlayGate.pause(this)
        voice = VoicePlayer(this)
        WalletStore.ensureFarmItems(this)
        layout = HomeLayoutStore.load(this)
        AppDataStore.unlock(this, "home_visit")
        reloadFarmFromLayout()

        val days = PetPrefs.companionDays(this).coerceAtLeast(1)
        binding.homeHint.text = binding.homeScene.maxRoomsHint(days) +
            "\n点格子移动 · 门切换 · 室外可开「经营」"

        animator = PetAnimator(this, binding.homePet)
        animator.setMode(PetAnimator.Mode.STAND)
        binding.homeScene.applyLayout(layout)
        binding.homeScene.farmGrid = farmGrid

        binding.homeScene.listener = object : HomeSceneView.Listener {
            override fun onPetCell(cx: Int, cy: Int) {
                animator.setMode(PetAnimator.Mode.WALK)
                placePet()
                binding.homePet.postDelayed({
                    if (!isFinishing) animator.setMode(PetAnimator.Mode.STAND)
                }, 400L)
            }

            override fun onDoorUsed() {
                Toast.makeText(
                    this@HomeActivity,
                    if (binding.homeScene.zone == HomeSceneView.Zone.INDOOR) "回到室内" else "来到室外",
                    Toast.LENGTH_SHORT,
                ).show()
                if (binding.homeScene.zone == HomeSceneView.Zone.INDOOR) setFarmMode(false)
                placePet()
            }

            override fun onTapPet() {
                animator.setMode(PetAnimator.Mode.HI)
                if (voice?.playHi() != true) {
                    Toast.makeText(this@HomeActivity, InteractLines.HI_TEXT, Toast.LENGTH_SHORT).show()
                }
                binding.homePet.postDelayed({
                    if (!isFinishing) animator.setMode(PetAnimator.Mode.STAND)
                }, 1200L)
            }

            override fun onFarmTap(cx: Int, cy: Int) {
                actFarmAt(cx, cy)
            }

            override fun onIndoorTap(cx: Int, cy: Int) {
                actVaseAt(cx, cy)
            }
        }

        binding.btnIndoor.setOnClickListener {
            binding.homeScene.setZone(HomeSceneView.Zone.INDOOR)
            setFarmMode(false)
            if (editMode) buildEditBrushes()
            placePet()
        }
        binding.btnOutdoor.setOnClickListener {
            binding.homeScene.setZone(HomeSceneView.Zone.OUTDOOR)
            if (editMode) buildEditBrushes()
            placePet()
        }
        binding.btnFarmMode.setOnClickListener {
            if (binding.homeScene.zone != HomeSceneView.Zone.OUTDOOR) {
                binding.homeScene.setZone(HomeSceneView.Zone.OUTDOOR)
                placePet()
            }
            setFarmMode(!farmMode)
        }
        binding.btnHomeBack.setOnClickListener { finish() }
        binding.btnUp.setOnClickListener { binding.homeScene.tryMove(0, -1); placePet() }
        binding.btnDown.setOnClickListener { binding.homeScene.tryMove(0, 1); placePet() }
        binding.btnLeft.setOnClickListener { binding.homeScene.tryMove(-1, 0); placePet() }
        binding.btnRight.setOnClickListener { binding.homeScene.tryMove(1, 0); placePet() }

        binding.btnHomeSave.setOnClickListener {
            persistLayout()
            Toast.makeText(this, "家园已保存", Toast.LENGTH_SHORT).show()
        }
        binding.btnHomeEdit.setOnClickListener { toggleEditMode() }
        binding.btnHomeImport.setOnClickListener {
            importLayout.launch(arrayOf("application/json", "text/*", "*/*"))
        }
        binding.btnHomeExport.setOnClickListener { exportLayout.launch("home_layout.json") }
        binding.btnHomeReset.setOnClickListener {
            AlertDialog.Builder(this)
                .setTitle("重置家园？")
                .setMessage("恢复默认布置（本地 layout）。")
                .setPositiveButton("重置") { _, _ ->
                    layout = HomeLayoutStore.reset(this)
                    reloadFarmFromLayout()
                    binding.homeScene.applyLayout(layout)
                    binding.homeScene.farmGrid = farmGrid
                    placePet()
                    Toast.makeText(this, "已重置", Toast.LENGTH_SHORT).show()
                }
                .setNegativeButton("取消", null)
                .show()
        }

        binding.btnFarmShop.setOnClickListener { showShop() }
        binding.btnFarmCraft.setOnClickListener { showCraft() }
        binding.btnFarmSell.setOnClickListener { showSell() }

        buildToolButtons()
        buildSeedButtons()
        binding.homeScene.post {
            syncHomePetSize()
            placePet()
        }
        handler.post(tickFarm)
    }

    private fun syncHomePetSize() {
        val tile = binding.homeScene.tilePx().coerceIn(24, 160)
        animator.applyDisplaySize(tile)
        placePet()
    }

    private var editMode = false
    private var editBrush: String? = "plant"

    private fun toggleEditMode() {
        editMode = !editMode
        binding.homeScene.editMode = editMode
        binding.homeScene.editBrush = editBrush
        binding.homeEditBar.visibility = if (editMode) View.VISIBLE else View.GONE
        binding.btnHomeEdit.text = if (editMode) "完成" else "编辑"
        if (editMode) {
            setFarmMode(false)
            buildEditBrushes()
            Toast.makeText(this, "编辑地图：点格子放置，选「擦除」清空", Toast.LENGTH_SHORT).show()
        } else {
            persistLayout()
            Toast.makeText(this, "已退出编辑并保存", Toast.LENGTH_SHORT).show()
        }
    }

    private fun buildEditBrushes() {
        val box = binding.homeEditBrushes
        box.removeAllViews()
        val indoor = listOf(
            null to "擦除",
            "bed" to "床",
            "table" to "桌",
            "chair" to "椅",
            "sofa" to "沙发",
            "plant" to "盆栽",
            "lamp" to "灯",
            "vase" to "花瓶",
            "carpet" to "地毯",
            "window" to "窗",
            "door" to "门",
            "shelf" to "架",
        )
        val outdoor = listOf(
            null to "擦除",
            "grass" to "草",
            "tree" to "树",
            "flower" to "花",
            "fence" to "篱",
            "bush" to "灌",
            "water" to "水",
            "rock" to "石",
            "path" to "路",
            "land" to "土",
            "house" to "屋",
            "door" to "门",
        )
        val brushes = if (binding.homeScene.zone == HomeSceneView.Zone.INDOOR) indoor else outdoor
        for ((kind, label) in brushes) {
            box.addView(
                Button(this).apply {
                    text = label
                    textSize = 11f
                    minimumWidth = 0
                    minWidth = 0
                    setPadding(18, 8, 18, 8)
                    setOnClickListener {
                        editBrush = kind
                        binding.homeScene.editBrush = kind
                        Toast.makeText(this@HomeActivity, "笔刷：$label", Toast.LENGTH_SHORT).show()
                    }
                },
            )
        }
    }

    private fun reloadFarmFromLayout() {
        farmGrid = HomeFarmEngine.ensureFarmGrid(layout)
        tillHits = HomeFarmEngine.loadTillHits(layout)
        chopJobs = HomeFarmEngine.loadChopJobs(layout)
        treeRegrow = HomeFarmEngine.loadTreeRegrow(layout)
        crafted = HomeFarmEngine.loadCrafted(layout)
        HomeFarmEngine.advanceFarm(farmGrid)
    }

    private fun setFarmMode(on: Boolean) {
        farmMode = on
        binding.homeScene.farmMode = on
        binding.farmBar.visibility = if (on) View.VISIBLE else View.GONE
        binding.btnFarmMode.alpha = if (on) 1f else 0.7f
        fishWaiting = false
        fishBite = false
        if (on) {
            AppDataStore.unlock(this, "farm_open")
            refreshFarmHud()
            Toast.makeText(this, "经营：选工具后点格子执行", Toast.LENGTH_SHORT).show()
        }
    }

    private fun buildToolButtons() {
        binding.farmTools.removeAllViews()
        for (t in HomeFarmEngine.Tool.entries) {
            binding.farmTools.addView(
                Button(this).apply {
                    text = t.label
                    textSize = 12f
                    setOnClickListener {
                        tool = t
                        fishWaiting = false
                        fishBite = false
                        refreshFarmHud()
                    }
                },
            )
        }
    }

    private fun buildSeedButtons() {
        binding.farmSeeds.removeAllViews()
        for ((id, label) in listOf(
            "seed_wheat" to "麦种",
            "seed_berry" to "莓种",
            "seed_corn" to "玉米种",
        )) {
            binding.farmSeeds.addView(
                Button(this).apply {
                    tag = id
                    textSize = 11f
                    setOnClickListener {
                        seedId = id
                        refreshFarmHud()
                    }
                },
            )
        }
    }

    private fun refreshFarmHud() {
        val coins = WalletStore.coins(this)
        binding.farmHint.text =
            "金币 $coins · 工具 ${tool.label} · ${tool.hint}\n" +
                "麦${WalletStore.itemCount(this, "seed_wheat")} " +
                "莓${WalletStore.itemCount(this, "seed_berry")} " +
                "玉${WalletStore.itemCount(this, "seed_corn")} " +
                "木${WalletStore.itemCount(this, "wood")}"
        for (i in 0 until binding.farmTools.childCount) {
            val b = binding.farmTools.getChildAt(i) as? Button ?: continue
            val t = HomeFarmEngine.Tool.entries.getOrNull(i) ?: continue
            b.alpha = if (t == tool) 1f else 0.55f
        }
        for (i in 0 until binding.farmSeeds.childCount) {
            val b = binding.farmSeeds.getChildAt(i) as? Button ?: continue
            val id = b.tag as? String ?: continue
            val n = WalletStore.itemCount(this, id)
            val name = HomeFarmEngine.ITEM_LABELS[id] ?: id
            b.text = "$name×$n"
            b.alpha = if (id == seedId) 1f else 0.55f
        }
    }

    private fun actFarmAt(tx: Int, ty: Int) {
        // 先走到邻格（砍/钓）或本格
        val petX = binding.homeScene.petX
        val petY = binding.homeScene.petY
        if (petX != tx || petY != ty) {
            // 逐步靠近一格
            val dx = (tx - petX).coerceIn(-1, 1)
            val dy = (ty - petY).coerceIn(-1, 1)
            if (dx != 0 || dy != 0) {
                binding.homeScene.tryMove(dx, dy)
                placePet()
            }
        }
        val tiles = binding.homeScene.outdoorTileOps()
        val px = binding.homeScene.petX
        val py = binding.homeScene.petY
        val result = when (tool) {
            HomeFarmEngine.Tool.TILL ->
                HomeFarmEngine.tryTill(farmGrid, tx, ty, tillHits, tiles)
            HomeFarmEngine.Tool.PLANT ->
                HomeFarmEngine.tryPlant(this, farmGrid, tx, ty, seedId, tiles)
            HomeFarmEngine.Tool.WATER ->
                HomeFarmEngine.tryWater(farmGrid, tx, ty)
            HomeFarmEngine.Tool.HARVEST ->
                HomeFarmEngine.tryHarvest(this, farmGrid, tx, ty)
            HomeFarmEngine.Tool.CHOP -> {
                val tree = HomeFarmEngine.findAdjacent(
                    tiles, px, py, "tree",
                    binding.homeScene.cols, binding.homeScene.rows,
                ) ?: (if (tiles.kind(tx, ty) == "tree") tx to ty else null)
                if (tree == null) HomeFarmEngine.ActResult(false, "请站在树四周")
                else HomeFarmEngine.tryChop(this, tiles, tree.first, tree.second, chopJobs, treeRegrow)
            }
            HomeFarmEngine.Tool.FISH -> handleFish(px, py, tiles)
            HomeFarmEngine.Tool.PICK ->
                HomeFarmEngine.tryPick(this, tiles, tx, ty)
        }
        Toast.makeText(this, result.msg, Toast.LENGTH_SHORT).show()
        binding.homeScene.farmGrid = farmGrid
        binding.homeScene.invalidate()
        refreshFarmHud()
        persistLayout()
    }

    private fun actVaseAt(tx: Int, ty: Int) {
        val tiles = binding.homeScene.indoorTileOps()
        val kind = tiles.kind(tx, ty)
        val result = when (kind) {
            "vase_filled" -> HomeFarmEngine.tryTakeFlowerFromVase(this, tiles, tx, ty)
            "vase" -> HomeFarmEngine.tryPutFlowerInVase(this, tiles, tx, ty)
            else -> HomeFarmEngine.ActResult(false, "不是花瓶")
        }
        Toast.makeText(this, result.msg, Toast.LENGTH_SHORT).show()
        persistLayout()
    }

    private fun handleFish(px: Int, py: Int, tiles: HomeFarmEngine.TileOps): HomeFarmEngine.ActResult {
        if (fishBite && fishStandX == px && fishStandY == py) {
            fishBite = false
            fishWaiting = false
            return HomeFarmEngine.applyFishRoll(this)
        }
        val water = HomeFarmEngine.findAdjacent(
            tiles, px, py, "water",
            binding.homeScene.cols, binding.homeScene.rows,
        ) ?: return HomeFarmEngine.ActResult(false, "请站在水面四周")
        if (fishWaiting) return HomeFarmEngine.ActResult(false, "还在等鱼…")
        fishWaiting = true
        fishBite = false
        fishStandX = px
        fishStandY = py
        val wait = (1600L..4200L).random()
        handler.postDelayed({
            if (!farmMode || !fishWaiting) return@postDelayed
            if (binding.homeScene.petX != fishStandX || binding.homeScene.petY != fishStandY) {
                fishWaiting = false
                Toast.makeText(this, "走动打断了钓鱼", Toast.LENGTH_SHORT).show()
                return@postDelayed
            }
            fishBite = true
            Toast.makeText(this, "上钩了！再点一次岸边确认", Toast.LENGTH_LONG).show()
            handler.postDelayed({
                if (fishBite) {
                    fishBite = false
                    fishWaiting = false
                    Toast.makeText(this, "错过了…", Toast.LENGTH_SHORT).show()
                }
            }, 950L)
        }, wait)
        return HomeFarmEngine.ActResult(true, "抛竿…等待上钩（邻水格 $water）")
    }

    private fun showShop() {
        val items = HomeFarmEngine.SHOP_PRICES.keys.toList()
        val labels = items.map {
            "${HomeFarmEngine.ITEM_LABELS[it]} · ${HomeFarmEngine.SHOP_PRICES[it]}金"
        }.toTypedArray()
        AlertDialog.Builder(this)
            .setTitle("商店 · 金币 ${WalletStore.coins(this)}")
            .setItems(labels) { _, which ->
                val r = HomeFarmEngine.buy(this, items[which])
                Toast.makeText(this, r.msg, Toast.LENGTH_SHORT).show()
                refreshFarmHud()
            }
            .setNegativeButton("关闭", null)
            .show()
    }

    private fun showSell() {
        val items = HomeFarmEngine.SELL_PRICES.keys.filter { WalletStore.itemCount(this, it) > 0 }
        if (items.isEmpty()) {
            Toast.makeText(this, "没有可售物品", Toast.LENGTH_SHORT).show()
            return
        }
        val labels = items.map {
            "${HomeFarmEngine.ITEM_LABELS[it]}×${WalletStore.itemCount(this, it)} · 卖${HomeFarmEngine.SELL_PRICES[it]}"
        }.toTypedArray()
        AlertDialog.Builder(this)
            .setTitle("出售")
            .setItems(labels) { _, which ->
                val r = HomeFarmEngine.sell(this, items[which])
                Toast.makeText(this, r.msg, Toast.LENGTH_SHORT).show()
                refreshFarmHud()
            }
            .setNegativeButton("关闭", null)
            .show()
    }

    private fun showCraft() {
        val labels = HomeFarmEngine.CRAFT_RECIPES.map { "${it.label}（${it.desc}）" }.toTypedArray()
        AlertDialog.Builder(this)
            .setTitle("合成")
            .setItems(labels) { _, which ->
                val r = HomeFarmEngine.tryCraft(this, crafted, HomeFarmEngine.CRAFT_RECIPES[which].id)
                Toast.makeText(this, r.msg, Toast.LENGTH_SHORT).show()
                persistLayout()
                refreshFarmHud()
            }
            .setNegativeButton("关闭", null)
            .show()
    }

    override fun onPause() {
        persistLayout()
        super.onPause()
    }

    override fun onDestroy() {
        handler.removeCallbacks(tickFarm)
        handler.removeCallbacksAndMessages(null)
        voice?.stop()
        animator.stop()
        OverlayGate.resume(this)
        super.onDestroy()
    }

    private fun persistLayout() {
        binding.homeScene.writeInto(layout)
        HomeFarmEngine.writeFarmGrid(layout, farmGrid)
        HomeFarmEngine.saveTillHits(layout, tillHits)
        HomeFarmEngine.saveChopJobs(layout, chopJobs)
        HomeFarmEngine.saveTreeRegrow(layout, treeRegrow)
        HomeFarmEngine.saveCrafted(layout, crafted)
        HomeLayoutStore.save(this, layout)
    }

    private fun placePet() {
        syncHomePetSizeIfNeeded()
        val size = binding.homePet.layoutParams?.width?.takeIf { it > 0 }
            ?: binding.homeScene.tilePx()
        val (x, y) = binding.homeScene.petPixelTopLeft(size)
        binding.homePet.x = x
        binding.homePet.y = y
    }

    private var lastSyncedTile = -1
    private fun syncHomePetSizeIfNeeded() {
        val tile = binding.homeScene.tilePx()
        if (tile == lastSyncedTile || tile < 12) return
        lastSyncedTile = tile
        animator.applyDisplaySize(tile.coerceIn(24, 160))
    }
}
