"""跨宠长谈：selecttalk1/2/3/# 帧动画 + 红框叠选项像素图。

素材走 assets/friend/talk（绿幕 JPG），经 friend_crossover 抠图。
"""
from __future__ import annotations

from typing import Callable

from PIL import Image

import friend_crossover as fc

FRAME_MS = int(getattr(fc, "SELECTTALK_FRAME_MS", 200) or 200)
DISPLAY_MAX = 280  # 左右对图后总宽约 2×，单帧先略缩小


def load_frame(name: str, *, pair_lr: bool = True) -> Image.Image | None:
    key = str(name or "1").strip()
    if key in ("hash", "selecttalk#"):
        key = "#"
    elif key.startswith("selecttalk") and key[-1:].isdigit():
        key = key[-1]
    # # 帧由 compose 再 pair；1/2/3 直接左右对图
    if key == "#":
        return fc.load_selecttalk_frame(key, display_w=DISPLAY_MAX, pair_lr=False)
    return fc.load_selecttalk_frame(key, display_w=DISPLAY_MAX, pair_lr=pair_lr)


def compose_result_on_frame3(
    overlay: Image.Image | None = None,
    *,
    label: str = "",
    pair_lr: bool = True,
) -> Image.Image | None:
    """最终结果叠在 selecttalk3 上；红框坐标仍按 # 标定映射。"""
    base = load_frame("3", pair_lr=False)
    if base is None:
        return None
    if overlay is not None:
        return fc.compose_selecttalk_with_icon(base, overlay, pair_lr=pair_lr)
    text = str(label or "").strip()
    if text:
        return fc.compose_selecttalk_with_label(base, text, pair_lr=pair_lr)
    if pair_lr:
        return fc.make_selecttalk_lr_pair(base)
    return base


def scale_for_display(img: Image.Image, *, max_side: int = 520) -> Image.Image:
    out = img.copy()
    # 左右对图较宽：按宽限制
    if out.size[0] > max_side:
        h = max(1, int(out.size[1] * max_side / out.size[0]))
        out = out.resize((max_side, h), Image.NEAREST)
    return out


def intro_frame_names() -> tuple[str, ...]:
    return ("1", "2", "3")


def resolve_frame_names() -> tuple[str, ...]:
    """选好后只播 123；内容落在第 3 帧（# 仅标定位置，不播出）。"""
    return ("1", "2", "3")


def try_load_choice_image(choice: dict | None, *, size: int = 96) -> Image.Image | None:
    """仅当有真实素材图时返回；没有则 None（调用方改显示文字）。"""
    c = choice or {}
    cid = str(c.get("id") or c.get("icon") or "").strip()
    if not cid:
        return None
    try:
        root = fc.friend_assets_dir() / "choices"
        names = (
            f"{cid}.png",
            f"food_{cid}.png",
            f"quarrel_{cid}.png",
            f"choice_{cid}.png",
        )
        aliases = {
            "peace": "quarrel_reconcile.png",
            "cold": "quarrel_cold.png",
            "break": "quarrel_break.png",
            "ramen": "food_ramen.png",
            "cake": "food_cake.png",
            "onigiri": "food_ramen.png",
            "bento": "food_ramen.png",
        }
        for name in names:
            path = root / name
            if path.is_file():
                img = Image.open(path).convert("RGBA")
                img.thumbnail((size, size), Image.NEAREST)
                return img
        alt = aliases.get(cid)
        if alt and (root / alt).is_file():
            img = Image.open(root / alt).convert("RGBA")
            img.thumbnail((size, size), Image.NEAREST)
            return img
    except Exception:
        pass
    # 也尝试食物/装扮像素渲染由调用方处理；这里不造假图
    return None


def choice_overlay(choice: dict | None, *, size: int = 96) -> Image.Image | None:
    """兼容旧调用：有真图返回图，否则 None（勿再回落像素占位，以便改显示文字）。"""
    return try_load_choice_image(choice, size=size)


class SelectTalkPlayer:
    """Tk 顶层窗播放 selecttalk；调用方提供 root / after / 定位。"""

    def __init__(self, root, *, apply_layer=None, place_fn=None) -> None:
        self.root = root
        self.apply_layer = apply_layer
        self.place_fn = place_fn
        self.win = None
        self.label = None
        self._photos: list = []
        self._job = None
        self._on_done: Callable[[], None] | None = None

    def close(self) -> None:
        if self._job is not None:
            try:
                self.root.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        win = self.win
        self.win = None
        self.label = None
        self._photos.clear()
        if win is not None:
            try:
                if win.winfo_exists():
                    win.destroy()
            except Exception:
                pass

    def _ensure_win(self) -> None:
        import tkinter as tk

        if self.win is not None:
            try:
                if self.win.winfo_exists():
                    return
            except Exception:
                pass
        win = tk.Toplevel(self.root)
        self.win = win
        win.overrideredirect(True)
        try:
            setattr(win, "_vpet_no_glass", True)
            setattr(win, "_vpet_menu_overlay", True)
        except Exception:
            pass
        if self.apply_layer:
            try:
                self.apply_layer(win)
            except Exception:
                pass
        win.configure(bg="magenta")
        try:
            win.wm_attributes("-transparentcolor", "magenta")
            win.attributes("-topmost", True)
        except Exception:
            pass
        self.label = tk.Label(win, bg="magenta", bd=0)
        self.label.pack()

    def _show_image(self, img: Image.Image) -> None:
        from PIL import ImageTk

        self._ensure_win()
        # load_frame / compose_hash_frame 已做左右对置，这里只做显示缩放
        disp = scale_for_display(img)
        canvas = Image.new("RGBA", disp.size, (255, 0, 255, 255))
        canvas.paste(disp, (0, 0), disp)
        photo = ImageTk.PhotoImage(canvas.convert("RGB"), master=self.root)
        self._photos.append(photo)
        assert self.label is not None and self.win is not None
        self.label.configure(image=photo)
        try:
            self.win.geometry(f"{disp.size[0]}x{disp.size[1]}")
        except Exception:
            pass
        if self.place_fn:
            try:
                self.place_fn(self.win, disp.size[0], disp.size[1])
            except Exception:
                pass
        try:
            self.win.lift()
        except Exception:
            pass

    def play(
        self,
        names: tuple[str, ...] | list[str],
        *,
        overlay: Image.Image | None = None,
        label: str = "",
        hold_last_ms: int = 900,
        on_done: Callable[[], None] | None = None,
        result_on_last: bool = False,
    ) -> None:
        self.close()
        self._on_done = on_done
        frames: list[Image.Image] = []
        name_list = list(names)
        for i, name in enumerate(name_list):
            is_last = i + 1 >= len(name_list)
            if name in ("#", "hash", "selecttalk#"):
                # 兼容旧调用；实际结算改用 frame3
                fr = compose_result_on_frame3(overlay, label=label, pair_lr=True)
            elif result_on_last and is_last and str(name) in ("3", "selecttalk3"):
                fr = compose_result_on_frame3(overlay, label=label, pair_lr=True)
            else:
                fr = load_frame(name, pair_lr=True)
            if fr is not None:
                frames.append(fr)
        if not frames:
            if on_done:
                on_done()
            return

        state = {"i": 0}

        def _tick() -> None:
            self._job = None
            i = state["i"]
            if i >= len(frames):
                done = self._on_done
                self._on_done = None
                if done:
                    done()
                return
            self._show_image(frames[i])
            state["i"] = i + 1
            delay = hold_last_ms if i + 1 >= len(frames) else FRAME_MS
            try:
                self._job = self.root.after(delay, _tick)
            except Exception:
                if self._on_done:
                    self._on_done()
                    self._on_done = None

        _tick()

    def play_intro(self, *, on_done: Callable[[], None] | None = None) -> None:
        self.play(intro_frame_names(), overlay=None, hold_last_ms=500, on_done=on_done)

    def play_resolve(
        self,
        overlay: Image.Image | None = None,
        *,
        label: str = "",
        on_done: Callable[[], None] | None = None,
    ) -> None:
        """选好后播 1→2→3，选项图/字叠在第 3 帧（# 只标定红框位置）。"""
        self.play(
            resolve_frame_names(),
            overlay=overlay,
            label=label,
            hold_last_ms=1400,
            on_done=on_done,
            result_on_last=True,
        )
