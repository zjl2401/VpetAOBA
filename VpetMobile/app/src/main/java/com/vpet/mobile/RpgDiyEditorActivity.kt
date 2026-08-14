package com.vpet.mobile

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.vpet.mobile.databinding.ActivityRpgDiyBinding
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/** DIY 地图编辑器：双层、公主笔刷、擦除、导出 JSON、试玩。 */
class RpgDiyEditorActivity : AppCompatActivity() {
    companion object {
        const val EXTRA_PLAY_PATH = "diy_play_path"
        private const val DIY_NAME = "user_diy.json"
    }

    private lateinit var binding: ActivityRpgDiyBinding

    private val palette = listOf(
        RpgMapLoader.GRASS to "草",
        RpgMapLoader.LAND to "土",
        RpgMapLoader.WATER to "水",
        RpgMapLoader.BRICK to "砖",
        RpgMapLoader.ROCK to "石",
        RpgMapLoader.TREE to "树",
        RpgMapLoader.OBSTACLE to "障",
        RpgMapLoader.HOUSE to "屋",
        RpgMapLoader.STAIRS to "梯",
        RpgMapLoader.CAVE to "洞",
        RpgMapLoader.GATE to "门",
        RpgMapLoader.TRAP_SPIKE to "刺",
        RpgMapLoader.TRAP_PIT to "坑",
        RpgMapLoader.PICKUP_COIN to "币",
        RpgMapLoader.TREASURE to "箱",
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityRpgDiyBinding.inflate(layoutInflater)
        setContentView(binding.root)
        OverlayGate.pause(this)

        if (!loadUserDiy()) binding.diyCanvas.resetBlank()
        refreshLayerBtn()

        for ((id, label) in palette) {
            binding.diyPalette.addView(
                Button(this).apply {
                    text = label
                    textSize = 11f
                    setOnClickListener {
                        binding.diyCanvas.princessBrush = false
                        binding.diyCanvas.placeMode = RpgDiyCanvas.PlaceMode.TILE
                        binding.diyCanvas.brush = id
                        Toast.makeText(this@RpgDiyEditorActivity, "笔刷：$label", Toast.LENGTH_SHORT).show()
                    }
                },
            )
        }

        binding.btnDiyStart.setOnClickListener {
            binding.diyCanvas.placeMode = RpgDiyCanvas.PlaceMode.START
            Toast.makeText(this, "点格子设起点（当前层）", Toast.LENGTH_SHORT).show()
        }
        binding.btnDiyGoal.setOnClickListener {
            binding.diyCanvas.placeMode = RpgDiyCanvas.PlaceMode.GOAL
            Toast.makeText(this, "点格子设出口（出口层=当前层）", Toast.LENGTH_SHORT).show()
        }
        binding.btnDiyLayer.setOnClickListener {
            binding.diyCanvas.toggleLayer()
            refreshLayerBtn()
            Toast.makeText(this, "编辑：${binding.diyCanvas.layerLabel()}", Toast.LENGTH_SHORT).show()
        }
        binding.btnDiyErase.setOnClickListener {
            binding.diyCanvas.princessBrush = false
            binding.diyCanvas.placeMode = RpgDiyCanvas.PlaceMode.ERASE
            Toast.makeText(this, "擦除模式", Toast.LENGTH_SHORT).show()
        }
        binding.btnDiyPrincess.setOnClickListener {
            binding.diyCanvas.princessBrush = !binding.diyCanvas.princessBrush
            binding.diyCanvas.princess = binding.diyCanvas.princessBrush
            binding.diyCanvas.placeMode = RpgDiyCanvas.PlaceMode.TILE
            binding.diyCanvas.brush = RpgMapLoader.GRASS
            Toast.makeText(
                this,
                if (binding.diyCanvas.princessBrush) "公主笔刷开：粉土+偶发宝箱（地图标记公主）" else "公主笔刷关",
                Toast.LENGTH_SHORT,
            ).show()
            binding.diyCanvas.invalidate()
        }
        binding.btnDiyNew.setOnClickListener {
            binding.diyCanvas.resetBlank()
            refreshLayerBtn()
            Toast.makeText(this, "已新建空白图", Toast.LENGTH_SHORT).show()
        }
        binding.btnDiySave.setOnClickListener {
            if (saveUserDiy()) Toast.makeText(this, "已保存到本地 DIY", Toast.LENGTH_SHORT).show()
            else Toast.makeText(this, "保存失败", Toast.LENGTH_SHORT).show()
        }
        binding.btnDiyExport.setOnClickListener {
            if (!saveUserDiy()) {
                Toast.makeText(this, "保存失败", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            val exported = exportCopy()
            if (exported != null) {
                Toast.makeText(this, "已导出：${exported.name}", Toast.LENGTH_LONG).show()
            } else {
                Toast.makeText(this, "导出失败", Toast.LENGTH_SHORT).show()
            }
        }
        binding.btnDiyPlay.setOnClickListener {
            if (!saveUserDiy()) {
                Toast.makeText(this, "保存失败，无法试玩", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            startActivity(
                Intent(this, RpgActivity::class.java)
                    .putExtra(EXTRA_PLAY_PATH, diyFile().absolutePath),
            )
        }
        binding.btnDiyBack.setOnClickListener { finish() }
    }

    override fun onDestroy() {
        OverlayGate.resume(this)
        super.onDestroy()
    }

    private fun refreshLayerBtn() {
        binding.btnDiyLayer.text = if (binding.diyCanvas.editLayer == "underground") "地下" else "地面"
    }

    private fun diyFile(): File = File(filesDir, DIY_NAME)

    private fun exportDir(): File = File(filesDir, "exports").also { it.mkdirs() }

    private fun exportCopy(): File? {
        return try {
            val dest = File(exportDir(), "diy_${System.currentTimeMillis()}.json")
            diyFile().copyTo(dest, overwrite = true)
            dest
        } catch (_: Exception) {
            null
        }
    }

    private fun saveUserDiy(): Boolean {
        return try {
            val c = binding.diyCanvas
            val surf = JSONArray()
            val under = JSONArray()
            for (y in 0 until c.rows) {
                val sr = JSONArray()
                val ur = JSONArray()
                for (x in 0 until c.cols) {
                    sr.put(c.surface[y][x])
                    ur.put(c.underground[y][x])
                }
                surf.put(sr)
                under.put(ur)
            }
            val o = JSONObject()
                .put("name", "用户 DIY")
                .put("width", c.cols)
                .put("height", c.rows)
                .put("start", JSONArray().put(c.startX).put(c.startY))
                .put("goal", JSONArray().put(c.goalX).put(c.goalY))
                .put("goal_layer", c.goalLayer)
                .put("princess", c.princess)
                .put("level_idx", -2)
                .put("surface", surf)
                .put("underground", under)
                .put("stairs", JSONArray())
                .put("caves", JSONArray())
            diyFile().writeText(o.toString())
            true
        } catch (_: Exception) {
            false
        }
    }

    private fun loadUserDiy(): Boolean {
        val f = diyFile()
        if (!f.isFile) return false
        return try {
            val o = JSONObject(f.readText())
            val w = o.getInt("width")
            val h = o.getInt("height")
            val surfArr = o.optJSONArray("surface") ?: o.getJSONArray("tiles")
            val underArr = o.optJSONArray("underground") ?: surfArr
            val surf = Array(h) { IntArray(w) }
            val under = Array(h) { IntArray(w) }
            for (y in 0 until h) {
                val sr = surfArr.getJSONArray(y)
                val ur = underArr.getJSONArray(y)
                for (x in 0 until w) {
                    surf[y][x] = sr.getInt(x)
                    under[y][x] = ur.getInt(x)
                }
            }
            val s = o.getJSONArray("start")
            val g = o.getJSONArray("goal")
            binding.diyCanvas.load(
                w, h, surf, under,
                s.getInt(0), s.getInt(1), g.getInt(0), g.getInt(1),
                o.optString("goal_layer", "surface"),
                o.optBoolean("princess", false),
            )
            true
        } catch (_: Exception) {
            false
        }
    }
}
