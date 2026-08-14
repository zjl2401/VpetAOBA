package com.vpet.mobile

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.PixelFormat
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.ImageView
import com.vpet.mobile.databinding.OverlayWorkHudBinding
import kotlin.math.hypot

/**
 * 工作旗/箱/HUD：悬浮窗用 WindowManager；房间模式挂到 [roomHost]。
 * 旗可拖：对照桌面 work_flag_drag。
 * 堆箱：对照 `_work_stack_offsets` + WORK_STACK_OFFSET，锚点=底边中心（旗脚周围）。
 */
class WorkPropsUi(
    private val context: Context,
    private val windowManager: WindowManager? = null,
    private val roomHost: FrameLayout? = null,
    private val onEndClick: () -> Unit,
    private val onFlagFootDrag: ((footX: Int, footY: Int) -> Unit)? = null,
    private val onFlagDragEnd: ((movedPx: Int) -> Unit)? = null,
) {
    private var hudBinding: OverlayWorkHudBinding? = null
    private var hudLp: WindowManager.LayoutParams? = null
    private var startBox: ImageView? = null
    private var flagView: ImageView? = null
    private val stackViews = mutableListOf<ImageView>()
    private var overlayMode = windowManager != null && roomHost == null
    private var flagDragEnabled = true
    private var lastFlagX = 0
    private var lastFlagY = 0
    private val boxBmp: Bitmap by lazy { loadPropBitmap(SpriteAssets.BOX, fallbackBox()) }
    private val flagBmp: Bitmap by lazy { loadPropBitmap(SpriteAssets.FLAG, fallbackFlag()) }

    fun showHud(delivered: Int, total: Int, continuous: Boolean, showEndButton: Boolean = continuous) {
        ensureHud()
        val text = if (continuous) {
            if (showEndButton) "自由运送 · $delivered 箱" else "定时运送 · $delivered 箱"
        } else {
            "运送 $delivered / $total"
        }
        hudBinding?.workProgress?.text = text
        hudBinding?.workEnd?.visibility = if (showEndButton) View.VISIBLE else View.GONE
        setVisible(hudBinding?.root, true)
    }

    fun hideHud() {
        setVisible(hudBinding?.root, false)
    }

    fun updateProps(
        startBoxVisible: Boolean,
        flagX: Int,
        flagY: Int,
        startX: Int,
        startY: Int,
        stack: Int,
    ) {
        val showDest = AppDataStore.workShowProps(context)
        val showStack = AppDataStore.workShowStack(context)
        val prop = WorkEngine.WORK_PROP_SIZE
        ensureStartBox()
        ensureFlag()
        lastFlagX = flagX
        lastFlagY = flagY
        place(startBox!!, startX, startY, prop)
        setVisible(startBox, showStack && startBoxVisible)
        place(flagView!!, flagX, flagY, prop)
        setVisible(flagView, showDest)

        val showN = if (showStack) stack.coerceIn(0, 16) else 0
        while (stackViews.size < showN) {
            val iv = makePropView(boxBmp)
            stackViews.add(iv)
            attach(iv)
        }
        val offsets = stackOffsets(showN)
        val flagFootX = flagX + prop / 2
        val flagFootY = flagY + prop
        val step = WorkEngine.WORK_STACK_OFFSET
        for (i in stackViews.indices) {
            val v = stackViews[i]
            if (i < showN) {
                val (dx, dy) = offsets[i]
                val footX = flagFootX + dx * step
                val footY = flagFootY + dy * step
                place(v, footX - prop / 2, footY - prop, prop)
                setVisible(v, true)
            } else {
                setVisible(v, false)
            }
        }
    }

    fun clear() {
        hideHud()
        setVisible(startBox, false)
        setVisible(flagView, false)
        stackViews.forEach { setVisible(it, false) }
    }

    fun destroy() {
        clear()
        detach(hudBinding?.root)
        detach(startBox)
        detach(flagView)
        stackViews.forEach { detach(it) }
        stackViews.clear()
        hudBinding = null
        startBox = null
        flagView = null
    }

    private fun ensureHud() {
        if (hudBinding != null) return
        val b = OverlayWorkHudBinding.inflate(LayoutInflater.from(context))
        b.workEnd.setOnClickListener { onEndClick() }
        hudBinding = b
        if (overlayMode) {
            hudLp = baseLp(WindowManager.LayoutParams.WRAP_CONTENT, WindowManager.LayoutParams.WRAP_CONTENT).apply {
                gravity = Gravity.TOP or Gravity.CENTER_HORIZONTAL
                y = 48
            }
            windowManager?.addView(b.root, hudLp)
        } else {
            val lp = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,
                FrameLayout.LayoutParams.WRAP_CONTENT,
            ).apply {
                gravity = Gravity.TOP or Gravity.CENTER_HORIZONTAL
                topMargin = 100
            }
            roomHost?.addView(b.root, lp)
        }
    }

    private fun ensureStartBox() {
        if (startBox != null) return
        startBox = makePropView(boxBmp).also { attach(it) }
    }

    @SuppressLint("ClickableViewAccessibility")
    private fun ensureFlag() {
        if (flagView != null) return
        flagView = makePropView(flagBmp).also { iv ->
            attach(iv)
            var downRawX = 0f
            var downRawY = 0f
            var originFootX = 0
            var originFootY = 0
            var dragging = false
            var totalMoved = 0
            iv.setOnTouchListener { _, e ->
                if (!flagDragEnabled || onFlagFootDrag == null) return@setOnTouchListener false
                val prop = WorkEngine.WORK_PROP_SIZE
                when (e.action) {
                    MotionEvent.ACTION_DOWN -> {
                        downRawX = e.rawX
                        downRawY = e.rawY
                        originFootX = lastFlagX + prop / 2
                        originFootY = lastFlagY + prop
                        dragging = true
                        totalMoved = 0
                        true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        if (!dragging) return@setOnTouchListener true
                        val dx = (e.rawX - downRawX).toInt()
                        val dy = (e.rawY - downRawY).toInt()
                        totalMoved = hypot(dx.toDouble(), dy.toDouble()).toInt()
                        onFlagFootDrag.invoke(originFootX + dx, originFootY + dy)
                        true
                    }
                    MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                        if (dragging) {
                            dragging = false
                            onFlagDragEnd?.invoke(totalMoved)
                        }
                        true
                    }
                    else -> false
                }
            }
        }
    }

    private fun makePropView(bmp: Bitmap): ImageView =
        ImageView(context).apply {
            scaleType = ImageView.ScaleType.FIT_XY
            setImageBitmap(bmp)
            visibility = View.GONE
            // 避免部分机型把透明叠层合成没了
            setBackgroundColor(Color.TRANSPARENT)
            elevation = 24f
        }

    private fun attach(v: View) {
        val prop = WorkEngine.WORK_PROP_SIZE
        if (overlayMode) {
            try {
                windowManager?.addView(v, baseLp(prop, prop))
            } catch (_: Exception) {
            }
        } else {
            roomHost?.addView(v, FrameLayout.LayoutParams(prop, prop))
        }
    }

    private fun detach(v: View?) {
        if (v == null) return
        try {
            if (overlayMode) windowManager?.removeView(v)
            else roomHost?.removeView(v)
        } catch (_: Exception) {
        }
    }

    private fun place(v: View, x: Int, y: Int, size: Int) {
        if (overlayMode) {
            val lp = (v.layoutParams as? WindowManager.LayoutParams) ?: baseLp(size, size)
            lp.width = size
            lp.height = size
            lp.x = x
            lp.y = y
            lp.gravity = Gravity.TOP or Gravity.START
            try {
                windowManager?.updateViewLayout(v, lp)
            } catch (_: Exception) {
                try {
                    windowManager?.addView(v, lp)
                } catch (_: Exception) {
                }
            }
        } else {
            val lp = (v.layoutParams as? FrameLayout.LayoutParams)
                ?: FrameLayout.LayoutParams(size, size)
            lp.width = size
            lp.height = size
            lp.leftMargin = x
            lp.topMargin = y
            lp.gravity = Gravity.TOP or Gravity.START
            v.layoutParams = lp
            v.requestLayout()
        }
    }

    private fun setVisible(v: View?, visible: Boolean) {
        v?.visibility = if (visible) View.VISIBLE else View.GONE
        if (visible) v?.bringToFront()
    }

    private fun baseLp(w: Int, h: Int): WindowManager.LayoutParams =
        WindowManager.LayoutParams(
            w,
            h,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT,
        ).apply {
            gravity = Gravity.TOP or Gravity.START
        }

    private fun loadPropBitmap(assetPath: String, fallback: Bitmap): Bitmap {
        val bmp = SpriteAssets.load(context, assetPath, WorkEngine.WORK_PROP_SIZE)
        return bmp ?: fallback
    }

    private fun fallbackBox(): Bitmap {
        val s = WorkEngine.WORK_PROP_SIZE
        val bmp = Bitmap.createBitmap(s, s, Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp)
        val p = Paint(Paint.ANTI_ALIAS_FLAG)
        p.color = Color.parseColor("#C4A574")
        c.drawRoundRect(4f, 10f, s - 4f, s - 4f, 6f, 6f, p)
        p.color = Color.parseColor("#8B6914")
        p.style = Paint.Style.STROKE
        p.strokeWidth = 3f
        c.drawRoundRect(4f, 10f, s - 4f, s - 4f, 6f, 6f, p)
        p.style = Paint.Style.FILL
        p.color = Color.parseColor("#FFE08A")
        c.drawRect(s * 0.2f, s * 0.35f, s * 0.8f, s * 0.45f, p)
        return bmp
    }

    private fun fallbackFlag(): Bitmap {
        val s = WorkEngine.WORK_PROP_SIZE
        val bmp = Bitmap.createBitmap(s, s, Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp)
        val p = Paint(Paint.ANTI_ALIAS_FLAG)
        p.color = Color.parseColor("#666666")
        c.drawRect(s * 0.18f, 4f, s * 0.28f, s - 4f, p)
        p.color = Color.parseColor("#FF3355")
        c.drawRect(s * 0.28f, 6f, s * 0.88f, s * 0.48f, p)
        return bmp
    }

    companion object {
        fun stackOffsets(count: Int): List<Pair<Int, Int>> {
            if (count <= 0) return emptyList()
            val positions = mutableListOf<Pair<Int, Int>>()
            var ring = 1
            while (positions.size < count) {
                positions.addAll(stackRingPositions(ring))
                ring += 1
                if (ring > 8) break
            }
            return positions.take(count)
        }

        private fun stackRingPositions(ring: Int): List<Pair<Int, Int>> {
            val positions = mutableListOf<Pair<Int, Int>>()
            for (dx in -ring..ring) {
                for (dy in 0..ring) {
                    if (dx == 0 && dy == 0) continue
                    if (maxOf(kotlin.math.abs(dx), dy) != ring) continue
                    positions.add(dx to dy)
                }
            }
            return positions.sortedWith(compareBy({ it.second }, { kotlin.math.abs(it.first) }))
        }
    }
}
