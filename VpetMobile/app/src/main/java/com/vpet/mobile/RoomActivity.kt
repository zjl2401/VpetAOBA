package com.vpet.mobile

import android.annotation.SuppressLint
import android.graphics.Point
import android.os.Bundle
import android.os.SystemClock
import android.view.MotionEvent
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.vpet.mobile.databinding.ActivityRoomBinding
import kotlin.math.abs

/** 普通 App 壳：同一套立绘与四大模块菜单。 */
class RoomActivity : AppCompatActivity() {

    private lateinit var binding: ActivityRoomBinding
    private lateinit var animator: PetAnimator
    private lateinit var menuPanel: PetMenuPanel
    private lateinit var hub: PetModeHub

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityRoomBinding.inflate(layoutInflater)
        setContentView(binding.root)

        animator = PetAnimator(this, binding.petImage) {
            if (hub.onWalkAnimStep()) stepLocomotion()
        }
        animator.applyDisplaySize()
        animator.setMode(PetAnimator.Mode.STAND)

        hub = PetModeHub(
            context = this,
            animator = animator,
            roomHost = binding.roomRoot,
            screenSize = {
                Point(
                    binding.roomRoot.width.coerceAtLeast(1),
                    binding.roomRoot.height.coerceAtLeast(1),
                )
            },
            petSize = { PetPrefs.sizePx(this) },
            petTopLeft = {
                val v = binding.petImage
                val left = ((binding.roomRoot.width - v.width) / 2f + v.translationX).toInt()
                val top = ((binding.roomRoot.height - v.height) / 2f + v.translationY).toInt()
                Point(left, top)
            },
            setPetTopLeft = { x, y ->
                val v = binding.petImage
                val baseLeft = (binding.roomRoot.width - v.width) / 2f
                val baseTop = (binding.roomRoot.height - v.height) / 2f
                v.translationX = x - baseLeft
                v.translationY = y - baseTop
            },
            raisePetOverlay = { binding.petImage.bringToFront() },
        )
        hub.attach()

        val actions = PetMenuActions(
            context = this,
            animator = animator,
            hub = hub,
            onResize = { },
            onExitOverlay = {
                Toast.makeText(this, "房间模式无悬浮可退，点返回即可", Toast.LENGTH_SHORT).show()
            },
            onFontChanged = {
                if (::menuPanel.isInitialized) menuPanel.refreshFonts()
            },
        )
        menuPanel = PetMenuPanel(
            context = this,
            actions = actions,
            asOverlay = false,
            petTopLeft = {
                val v = binding.petImage
                val left = ((binding.roomRoot.width - v.width) / 2f + v.translationX).toInt()
                val top = ((binding.roomRoot.height - v.height) / 2f + v.translationY).toInt()
                Point(left, top)
            },
            petSize = { PetPrefs.sizePx(this) },
            screenSize = {
                Point(
                    binding.roomRoot.width.coerceAtLeast(1),
                    binding.roomRoot.height.coerceAtLeast(1),
                )
            },
            roomHost = binding.roomRoot,
        )
        hub.raiseToolbars = { menuPanel.raiseLayer() }

        setupPetTouch()
        binding.btnSizeS.setOnClickListener { applySize("小") }
        binding.btnSizeM.setOnClickListener { applySize("中") }
        binding.btnSizeL.setOnClickListener { applySize("大") }
        refreshSizeHints()
    }

    override fun onDestroy() {
        hub.destroy()
        menuPanel.hide()
        animator.stop()
        super.onDestroy()
    }

    private fun applySize(label: String) {
        PetPrefs.setSizeLabel(this, label)
        hub.applyDisplaySizeToPetAndCompanion()
        refreshSizeHints()
    }

    private fun refreshSizeHints() {
        val cur = PetPrefs.sizeLabel(this)
        binding.btnSizeS.alpha = if (cur == "小") 1f else 0.55f
        binding.btnSizeM.alpha = if (cur == "中") 1f else 0.55f
        binding.btnSizeL.alpha = if (cur == "大") 1f else 0.55f
    }

    private fun stepLocomotion() {
        val v = binding.petImage
        val parent = binding.roomRoot
        val petW = v.width.coerceAtLeast(1)
        val petH = v.height.coerceAtLeast(1)
        val baseLeft = (parent.width - petW) / 2f
        val baseTop = (parent.height - petH) / 2f
        val (dx, dy) = animator.walkDelta()
        var absX = (baseLeft + v.translationX + dx).toInt()
        var absY = (baseTop + v.translationY + dy).toInt()
        val maxX = (parent.width - petW).coerceAtLeast(0)
        val maxY = (parent.height - petH).coerceAtLeast(0)
        if (absX < 0 || absX > maxX || absY < 0 || absY > maxY) {
            val curX = (baseLeft + v.translationX).toInt()
            val curY = (baseTop + v.translationY).toInt()
            val next = animator.pickInboundDir { d ->
                val step = animator.walkStepPx()
                val tx = curX + d.dx * step
                val ty = curY + d.dy * step
                tx in 0..maxX && ty in 0..maxY
            }
            if (next != null) {
                animator.setWalkDir(next)
                val (ndx, ndy) = animator.walkDelta()
                absX = (curX + ndx).coerceIn(0, maxX)
                absY = (curY + ndy).coerceIn(0, maxY)
            } else {
                absX = curX.coerceIn(0, maxX)
                absY = curY.coerceIn(0, maxY)
            }
        }
        v.translationX = absX - baseLeft
        v.translationY = absY - baseTop
    }

    @SuppressLint("ClickableViewAccessibility")
    private fun setupPetTouch() {
        var downX = 0f
        var downY = 0f
        var startTx = 0f
        var startTy = 0f
        var moved = false
        var downAt = 0L
        var yuqiFired = false

        binding.petImage.setOnTouchListener { v, event ->
            val busy = hub.isWorking || hub.isFollowing
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    downX = event.rawX
                    downY = event.rawY
                    startTx = v.translationX
                    startTy = v.translationY
                    moved = false
                    yuqiFired = false
                    downAt = SystemClock.elapsedRealtime()
                    if (hub.locomotionEnabled) hub.stopLocomotion()
                    hub.resetDragYuqiSession()
                    hub.noteUserActivity()
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    if (busy || hub.isQuiet) return@setOnTouchListener true
                    val dx = event.rawX - downX
                    val dy = event.rawY - downY
                    if (abs(dx) > 16 || abs(dy) > 16) {
                        if (!moved) {
                            moved = true
                            animator.setMode(PetAnimator.Mode.WALK)
                        }
                    }
                    v.translationX = startTx + dx
                    v.translationY = startTy + dy
                    hub.noteUserActivity()
                    val held = SystemClock.elapsedRealtime() - downAt
                    if (moved && held >= PetAnimator.DRAG_YUQI_MS) {
                        if (hub.onDragHeld(held)) yuqiFired = true
                    }
                    true
                }
                MotionEvent.ACTION_UP -> {
                    if (!moved) {
                        if (hub.isQuiet) hub.peekQuiet()
                        else {
                            val part = PetClickZones.partAt(event.x, event.y, v.width, v.height)
                            if (part != null) hub.tryInterjection(part)
                            menuPanel.toggle(binding.roomRoot)
                        }
                        hub.resumeWalkingAfterPause()
                    } else if (!busy && !hub.isQuiet) {
                        hub.playLandSettle { ny ->
                            val baseTop = (binding.roomRoot.height - v.height) / 2f
                            v.translationY = ny - baseTop
                            hub.resumeWalkingAfterPause()
                        }
                    } else {
                        hub.resumeWalkingAfterPause()
                    }
                    true
                }
                else -> false
            }
        }
    }
}
