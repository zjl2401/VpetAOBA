package com.vpet.mobile

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.PixelFormat
import android.graphics.Point
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.util.TypedValue
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import com.vpet.mobile.databinding.OverlayMainMenuBinding

/**
 * 悬浮/房间共用菜单。
 * 布局对齐桌面：等宽四大骨架 + pack_menu_chrome + 像素图标 + 点击粒子。
 */
class PetMenuPanel(
    private val context: Context,
    private val actions: PetMenuActions,
    private val asOverlay: Boolean,
    private val windowManager: WindowManager? = null,
    private val petTopLeft: () -> Point = { Point(80, 280) },
    private val petSize: () -> Int = { PetPrefs.sizePx(context) },
    private val screenSize: () -> Point = {
        val dm = context.resources.displayMetrics
        Point(dm.widthPixels, dm.heightPixels)
    },
    private val roomHost: FrameLayout? = null,
) {
    companion object {
        const val POPUP_PET_GAP = 10
        const val POPUP_EDGE_MARGIN = 20
        private const val MODULE_H_DP = 36f
        private const val ITEM_H_DP = 34f
    }

    private var binding: OverlayMainMenuBinding? = null
    private var layoutParams: WindowManager.LayoutParams? = null
    private var roomLp: FrameLayout.LayoutParams? = null
    private var stack = ArrayDeque<List<DesktopMenuCatalog.Item>>()
    private var selectedModuleId: String = "interact"
    private val moduleButtons = LinkedHashMap<String, TextView>()
    private var currentLevelItems: List<DesktopMenuCatalog.Item> = emptyList()
    private val clickBurst = PixelClickBurst(
        context,
        windowManager = if (asOverlay) windowManager else null,
        roomHost = if (!asOverlay) roomHost else null,
    )

    val isShowing: Boolean
        get() = binding?.root?.parent != null &&
            (asOverlay || binding!!.root.visibility == View.VISIBLE)

    @SuppressLint("InflateParams")
    fun toggle(attachTo: ViewGroup? = null) {
        if (isShowing) {
            hide()
            return
        }
        show(attachTo)
    }

    fun show(attachTo: ViewGroup? = null) {
        if (binding == null) {
            binding = OverlayMainMenuBinding.inflate(LayoutInflater.from(context))
            styleClose(binding!!.btnMenuClose)
            binding!!.btnMenuClose.setOnClickListener { v ->
                clickBurst.play(v)
                hide()
            }
        }
        applyMenuFonts()
        buildModules()
        stack.clear()
        val interact = DesktopMenuCatalog.root.first { it.id == "interact" }
        selectModule(interact)

        val root = binding!!.root
        root.measure(
            View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED),
            View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED),
        )
        val mw = root.measuredWidth.coerceAtLeast(1)
        val mh = root.measuredHeight.coerceAtLeast(1)
        val (x, y) = bestPopupPos(mw, mh)

        if (asOverlay) {
            val wm = windowManager ?: return
            if (root.parent != null) {
                layoutParams?.let {
                    it.x = x
                    it.y = y
                    try {
                        wm.updateViewLayout(root, it)
                    } catch (_: Exception) {
                    }
                }
                return
            }
            layoutParams = WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
                PixelFormat.TRANSLUCENT,
            ).apply {
                gravity = Gravity.TOP or Gravity.START
                this.x = x
                this.y = y
            }
            wm.addView(root, layoutParams)
        } else {
            val host = (attachTo ?: roomHost) ?: return
            if (root.parent == null) {
                roomLp = FrameLayout.LayoutParams(
                    FrameLayout.LayoutParams.WRAP_CONTENT,
                    FrameLayout.LayoutParams.WRAP_CONTENT,
                ).apply {
                    gravity = Gravity.TOP or Gravity.START
                    leftMargin = x
                    topMargin = y
                }
                host.addView(root, roomLp)
            } else {
                roomLp?.let {
                    it.leftMargin = x
                    it.topMargin = y
                    root.layoutParams = it
                }
            }
            root.visibility = View.VISIBLE
        }
    }

    fun hide() {
        val root = binding?.root ?: return
        if (asOverlay) {
            try {
                windowManager?.removeView(root)
            } catch (_: Exception) {
            }
        } else {
            (root.parent as? ViewGroup)?.removeView(root)
            root.visibility = View.GONE
        }
        stack.clear()
    }

    /** 工具栏抬层：应在桌宠/伴侣之前调用，使宠与伴侣压在菜单之上。 */
    fun raiseLayer() {
        val root = binding?.root ?: return
        if (!isShowing) return
        try {
            if (asOverlay) {
                val wm = windowManager ?: return
                val lp = layoutParams ?: return
                wm.removeView(root)
                wm.addView(root, lp)
            } else {
                root.bringToFront()
            }
        } catch (_: Exception) {
        }
    }

    private fun styleClose(tv: TextView) {
        tv.background = MenuDecor.menuItemBg()
        tv.setTextColor(MenuDecor.MENU_FG)
        tv.typeface = Typeface.MONOSPACE
        bindPressBg(tv, MenuDecor.THEME_ITEM_BG, MenuDecor.MENU_ACTIVE)
    }

    /** 对齐桌面 `_panel_popup_candidates` + `_best_popup_pos`：优先右/左/下/上，避开桌宠矩形。 */
    private fun bestPopupPos(panelW: Int, panelH: Int): Pair<Int, Int> {
        val gap = POPUP_PET_GAP
        val margin = POPUP_EDGE_MARGIN
        val pet = petTopLeft()
        val size = petSize()
        val scr = screenSize()
        val sw = scr.x.coerceAtLeast(1)
        val sh = scr.y.coerceAtLeast(1)
        val petRight = pet.x + size
        val petBottom = pet.y + size
        val petCx = pet.x + size / 2
        val centerX = maxOf(margin, (sw - panelW) / 2)
        val centerY = maxOf(margin, (sh - panelH) / 2)

        val candidates = listOf(
            petRight + gap to pet.y,
            pet.x - panelW - gap to pet.y,
            pet.x to petBottom + gap,
            petCx - panelW / 2 to pet.y - panelH - gap,
            petRight + gap to petBottom + gap,
            pet.x - panelW - gap to petBottom - panelH,
            centerX to centerY,
            centerX to margin,
            centerX to sh - panelH - margin,
            margin to centerY,
            sw - panelW - margin to centerY,
        )

        var best: Pair<Int, Int>? = null
        var bestScore = Int.MIN_VALUE
        for ((px, py) in candidates) {
            val cx = px.coerceIn(margin, (sw - panelW - margin).coerceAtLeast(margin))
            val cy = py.coerceIn(margin, (sh - panelH - margin).coerceAtLeast(margin))
            var score = minOf(
                cx - margin,
                cy - margin,
                sw - margin - cx - panelW,
                sh - margin - cy - panelH,
            )
            if (rectsOverlap(cx, cy, panelW, panelH, pet.x, pet.y, size, size)) {
                score -= 1_000_000
            }
            if (score > bestScore) {
                bestScore = score
                best = cx to cy
            }
        }
        return best ?: (margin to margin)
    }

    private fun rectsOverlap(
        ax: Int, ay: Int, aw: Int, ah: Int,
        bx: Int, by: Int, bw: Int, bh: Int,
    ): Boolean {
        return ax < bx + bw && ax + aw > bx && ay < by + bh && ay + ah > by
    }

    /** 设置改字体后：若菜单正开着则重建字号与条目。 */
    fun refreshFonts() {
        if (binding == null) return
        applyMenuFonts()
        if (!isShowing) return
        val modId = selectedModuleId
        val level = currentLevelItems
        val savedStack = ArrayDeque(stack)
        buildModules()
        selectedModuleId = modId
        refreshModuleStyles()
        stack = savedStack
        if (level.isNotEmpty()) showLevel(level)
    }

    private fun applyMenuFonts() {
        val b = binding ?: return
        val sp = AppDataStore.fontMenuSp(context)
        b.btnMenuClose.setTextSize(TypedValue.COMPLEX_UNIT_SP, sp)
    }

    private fun buildModules() {
        val row = binding!!.moduleRow
        row.removeAllViews()
        moduleButtons.clear()
        val h = MenuDecor.dp(context, MODULE_H_DP)
        val gap = MenuDecor.dp(context, 2f)
        val menuSp = AppDataStore.fontMenuSp(context)
        DesktopMenuCatalog.root.forEachIndexed { index, mod ->
            val btn = TextView(context).apply {
                text = mod.title
                setTextColor(MenuDecor.MENU_FG)
                setTextSize(TypedValue.COMPLEX_UNIT_SP, menuSp)
                typeface = Typeface.MONOSPACE
                gravity = Gravity.CENTER
                includeFontPadding = false
                setPadding(MenuDecor.dp(context, 2f), 0, MenuDecor.dp(context, 2f), 0)
                val glyph = MenuDecor.glyphDrawable(context, mod.title, menuSp)
                setCompoundDrawables(glyph, null, null, null)
                compoundDrawablePadding = MenuDecor.dp(context, 3f)
                background = MenuDecor.moduleBtnBg(false)
                setOnClickListener { v ->
                    clickBurst.play(v)
                    selectModule(mod)
                }
            }
            moduleButtons[mod.id] = btn
            val lp = LinearLayout.LayoutParams(0, h, 1f).apply {
                if (index < DesktopMenuCatalog.root.lastIndex) marginEnd = gap
            }
            row.addView(btn, lp)
        }
        refreshModuleStyles()
    }

    private fun selectModule(mod: DesktopMenuCatalog.Item) {
        selectedModuleId = mod.id
        refreshModuleStyles()
        stack.clear()
        showLevel(mod.children)
        binding?.root?.post { repositionIfShowing() }
    }

    private fun refreshModuleStyles() {
        for ((id, btn) in moduleButtons) {
            val selected = id == selectedModuleId
            btn.background = MenuDecor.moduleBtnBg(selected)
            btn.setTextColor(if (selected) MenuDecor.THEME_PINK else MenuDecor.MENU_FG)
        }
    }

    private fun showLevel(items: List<DesktopMenuCatalog.Item>) {
        currentLevelItems = items
        val list = binding!!.subList
        list.removeAllViews()
        if (stack.isNotEmpty()) {
            list.addView(makeItemBtn("◀ 返回") {
                val prev = stack.removeLast()
                showLevel(prev)
            })
        }
        for (item in items) {
            val base = when {
                item.children.isNotEmpty() -> item.title
                item.status == DesktopMenuCatalog.Status.READY -> item.title
                item.status == DesktopMenuCatalog.Status.STUB -> "${item.title} ·"
                else -> "${item.title} …"
            }
            val checked = item.children.isEmpty() && actions.isChecked(item.id)
            val label = if (checked) "✓ $base" else "　 $base"
            list.addView(makeItemBtn(label, checked = checked) {
                when {
                    item.children.isNotEmpty() -> {
                        stack.addLast(items)
                        showLevel(item.children)
                    }
                    else -> {
                        actions.run(item.id)
                        if (item.id == "sys_exit") hide()
                        else showLevel(currentLevelItems)
                    }
                }
            })
        }
        binding?.root?.post { repositionIfShowing() }
    }

    private fun repositionIfShowing() {
        if (!isShowing) return
        val root = binding?.root ?: return
        root.measure(
            View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED),
            View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED),
        )
        val mw = root.measuredWidth.coerceAtLeast(1)
        val mh = root.measuredHeight.coerceAtLeast(1)
        val (x, y) = bestPopupPos(mw, mh)
        if (asOverlay) {
            val lp = layoutParams ?: return
            lp.x = x
            lp.y = y
            try {
                windowManager?.updateViewLayout(root, lp)
            } catch (_: Exception) {
            }
        } else {
            val lp = roomLp ?: return
            lp.leftMargin = x
            lp.topMargin = y
            root.layoutParams = lp
        }
    }

    private fun makeItemBtn(text: String, checked: Boolean = false, onClick: () -> Unit): TextView {
        val glyphKey = text.trimStart('✓', '　', ' ')
        val h = MenuDecor.dp(context, ITEM_H_DP)
        val sp = AppDataStore.fontMenuSp(context)
        return TextView(context).apply {
            this.text = text
            setTextColor(if (checked) MenuDecor.THEME_PINK else MenuDecor.MENU_FG)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, sp)
            typeface = Typeface.MONOSPACE
            gravity = Gravity.CENTER_VERTICAL or Gravity.START
            includeFontPadding = false
            setPadding(MenuDecor.dp(context, 8f), 0, MenuDecor.dp(context, 8f), 0)
            val glyph = MenuDecor.glyphDrawable(context, glyphKey, sp)
            setCompoundDrawables(glyph, null, null, null)
            compoundDrawablePadding = MenuDecor.dp(context, 6f)
            background = MenuDecor.menuItemBg()
            bindPressBg(this, MenuDecor.THEME_ITEM_BG, MenuDecor.MENU_ACTIVE)
            setOnClickListener { v ->
                clickBurst.play(v)
                onClick()
            }
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                h,
            ).also { it.bottomMargin = MenuDecor.dp(context, 2f) }
        }
    }

    @SuppressLint("ClickableViewAccessibility")
    private fun bindPressBg(view: TextView, normal: Int, pressed: Int) {
        view.setOnTouchListener { v, e ->
            when (e.action) {
                MotionEvent.ACTION_DOWN -> {
                    (v.background as? GradientDrawable)?.setColor(pressed)
                        ?: run { v.setBackgroundColor(pressed) }
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    v.background = MenuDecor.menuItemBg()
                }
            }
            false
        }
    }
}
