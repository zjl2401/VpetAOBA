package com.vpet.mobile

import android.annotation.SuppressLint
import android.content.Context
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
        setVisible(startBox, showDest && startBoxVisible)
        place(flagView!!, flagX, flagY, prop)
        setVisible(flagView, showDest)

        val showN = if (showStack) stack.coerceIn(0, 8) else 0
        while (stackViews.size < showN) {
            val iv = makePropView()
            stackViews.add(iv)
            attach(iv)
        }
        for (i in stackViews.indices) {
            val v = stackViews[i]
            if (i < showN) {
                val ox = flagX - prop - 8
                val oy = flagY + i * (WorkEngine.WORK_PROP_SIZE * 2 / 3)
                place(v, ox, oy, prop)
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
            hudLp = baseLp().apply {
                gravity = Gravity.TOP or Gravity.CENTER_HORIZONTAL
                y = 48
                flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS
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
        startBox = makePropView().also {
            it.setImageBitmap(SpriteAssets.load(context, SpriteAssets.BOX, WorkEngine.WORK_PROP_SIZE))
            attach(it)
        }
    }

    @SuppressLint("ClickableViewAccessibility")
    private fun ensureFlag() {
        if (flagView != null) return
        flagView = makePropView().also { iv ->
            iv.setImageBitmap(SpriteAssets.load(context, SpriteAssets.FLAG, WorkEngine.WORK_PROP_SIZE))
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

    private fun makePropView(): ImageView =
        ImageView(context).apply {
            scaleType = ImageView.ScaleType.FIT_CENTER
            visibility = View.GONE
            setImageBitmap(SpriteAssets.load(context, SpriteAssets.BOX, WorkEngine.WORK_PROP_SIZE))
        }

    private fun attach(v: View) {
        if (overlayMode) {
            // 旗需要可点：不加 NOT_TOUCHABLE
            windowManager?.addView(v, baseLp())
        } else {
            roomHost?.addView(
                v,
                FrameLayout.LayoutParams(WorkEngine.WORK_PROP_SIZE, WorkEngine.WORK_PROP_SIZE),
            )
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
            val lp = (v.layoutParams as? WindowManager.LayoutParams) ?: baseLp()
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
            v.layoutParams = lp
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
    }

    private fun baseLp(): WindowManager.LayoutParams =
        WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT,
        ).apply {
            gravity = Gravity.TOP or Gravity.START
        }
}
