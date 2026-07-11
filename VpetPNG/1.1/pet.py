"""桌面桌宠 v1.1：四处走走停停，walk 两帧交替，停下 stand，随机 squat，Ctrl+Shift+H 打招呼。"""

import ctypes
import random
import sys
import tkinter as tk
from ctypes import wintypes
from pathlib import Path

from PIL import Image, ImageTk

ASSET_DIR = Path(__file__).parent
DISPLAY_HEIGHT = 128
WALK_FRAME_MS = 180
MOVE_INTERVAL_MS = 50
MOVE_STEP = 3
HI_DURATION_MS = 2000
SQUAT_CHANCE = 0.25

HOTKEY_ID = 1
WM_HOTKEY = 0x0312
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004


def _is_chroma_green(r: int, g: int, b: int) -> bool:
    return g > 150 and g > r + 30 and g > b + 50


def _crop_and_transparent(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size

    min_x, min_y = width, height
    max_x, max_y = 0, 0
    for y in range(height):
        for x in range(width):
            r, g, b, _a = pixels[x, y]
            if _is_chroma_green(r, g, b):
                pixels[x, y] = (r, g, b, 0)
                continue
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)

    if max_x >= min_x and max_y >= min_y:
        rgba = rgba.crop((min_x, min_y, max_x + 1, max_y + 1))

    scale = DISPLAY_HEIGHT / rgba.height
    new_size = (max(1, int(rgba.width * scale)), DISPLAY_HEIGHT)
    return rgba.resize(new_size, Image.Resampling.NEAREST)


def _load_sprite(filename: str, flip: bool = False) -> ImageTk.PhotoImage:
    img = Image.open(ASSET_DIR / filename)
    if flip:
        img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return ImageTk.PhotoImage(_crop_and_transparent(img))


class DesktopPet:
    DIRECTIONS = ("front", "back", "left", "right")
    DELTAS = {
        "front": (0, MOVE_STEP),
        "back": (0, -MOVE_STEP),
        "left": (-MOVE_STEP, 0),
        "right": (MOVE_STEP, 0),
    }

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Vpet")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.config(bg="magenta")
        self.root.wm_attributes("-transparentcolor", "magenta")

        self.sprites = {
            "stand": _load_sprite("stand.jpg"),
            "hi": _load_sprite("hi.jpg"),
            "squat": _load_sprite("squat.jpg"),
            "front": (_load_sprite("walkfront1.jpg"), _load_sprite("walkfront2.jpg")),
            "back": (_load_sprite("walkback1.jpg"), _load_sprite("walkback2.jpg")),
            "left": (_load_sprite("walkleft1.jpg"), _load_sprite("walkleft2.jpg")),
            "right": (
                _load_sprite("walkleft1.jpg", flip=True),
                _load_sprite("walkleft2.jpg", flip=True),
            ),
        }

        self.label = tk.Label(self.root, image=self.sprites["stand"], bg="magenta", bd=0)
        self.label.pack()

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.x = random.randint(0, max(0, screen_w - DISPLAY_HEIGHT))
        self.y = random.randint(0, max(0, screen_h - DISPLAY_HEIGHT))

        self.state = "stand"
        self.direction = "front"
        self.walk_frame = 0
        self.walk_steps_left = 0

        self.drag_x = 0
        self.drag_y = 0
        self.dragging = False
        self.hotkey_registered = False

        self.label.bind("<Button-1>", self._on_press)
        self.label.bind("<B1-Motion>", self._on_drag)
        self.label.bind("<ButtonRelease-1>", self._on_release)
        self.label.bind("<Button-3>", self._show_menu)

        self._place_window()
        self.root.update_idletasks()
        self._register_hotkey()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(500, self._stand_tick)

    def _register_hotkey(self) -> None:
        if sys.platform != "win32":
            return
        hwnd = self.root.winfo_id()
        ok = ctypes.windll.user32.RegisterHotKey(
            hwnd, HOTKEY_ID, MOD_CONTROL | MOD_SHIFT, ord("H")
        )
        self.hotkey_registered = bool(ok)
        if self.hotkey_registered:
            self.root.after(100, self._poll_hotkey)

    def _unregister_hotkey(self) -> None:
        if sys.platform != "win32" or not self.hotkey_registered:
            return
        ctypes.windll.user32.UnregisterHotKey(self.root.winfo_id(), HOTKEY_ID)
        self.hotkey_registered = False

    def _poll_hotkey(self) -> None:
        if not self.hotkey_registered:
            return
        msg = wintypes.MSG()
        hwnd = self.root.winfo_id()
        while ctypes.windll.user32.PeekMessageW(
            ctypes.byref(msg), hwnd, WM_HOTKEY, WM_HOTKEY, 1
        ):
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                self._play_hi()
        self.root.after(100, self._poll_hotkey)

    def _place_window(self) -> None:
        self.root.geometry(f"+{self.x}+{self.y}")

    def _set_image(self, photo: ImageTk.PhotoImage) -> None:
        self.label.config(image=photo)
        self.label.image = photo

    def _on_press(self, event: tk.Event) -> None:
        self.dragging = True
        self.drag_x = event.x_root - self.x
        self.drag_y = event.y_root - self.y
        self.state = "stand"
        self._set_image(self.sprites["stand"])

    def _on_drag(self, event: tk.Event) -> None:
        if not self.dragging:
            return
        self.x = event.x_root - self.drag_x
        self.y = event.y_root - self.drag_y
        self._place_window()

    def _on_release(self, _event: tk.Event) -> None:
        self.dragging = False
        self.root.after(random.randint(800, 2000), self._stand_tick)

    def _show_menu(self, event: tk.Event) -> None:
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="打招呼 (Ctrl+Shift+H)", command=self._play_hi)
        menu.add_separator()
        menu.add_command(label="退出", command=self._on_close)
        menu.tk_popup(event.x_root, event.y_root)

    def _on_close(self) -> None:
        self._unregister_hotkey()
        self.root.destroy()

    def _play_hi(self) -> None:
        if self.dragging:
            return
        self.state = "hi"
        self._set_image(self.sprites["hi"])
        self.root.after(HI_DURATION_MS, self._after_hi)

    def _after_hi(self) -> None:
        if self.dragging or self.state != "hi":
            return
        self._stand_tick()

    def _play_squat(self) -> None:
        if self.dragging:
            return
        self.state = "squat"
        self._set_image(self.sprites["squat"])
        delay = random.randint(800, 1500)
        self.root.after(delay, self._after_squat)

    def _after_squat(self) -> None:
        if self.dragging or self.state != "squat":
            return
        self.state = "stand"
        self._set_image(self.sprites["stand"])
        delay = random.randint(800, 2000)
        self.root.after(delay, self._start_walk)

    def _stand_tick(self) -> None:
        if self.dragging:
            return

        if random.random() < SQUAT_CHANCE:
            self._play_squat()
            return

        self.state = "stand"
        self._set_image(self.sprites["stand"])
        delay = random.randint(1200, 3500)
        self.root.after(delay, self._start_walk)

    def _start_walk(self) -> None:
        if self.dragging or self.state not in ("stand", "squat"):
            return

        self.state = "walk"
        self.direction = random.choice(self.DIRECTIONS)
        self.walk_frame = 0
        self.walk_steps_left = random.randint(20, 80)
        self._walk_move()
        self._walk_animate()

    def _walk_animate(self) -> None:
        if self.state != "walk" or self.dragging:
            return

        frames = self.sprites[self.direction]
        self._set_image(frames[self.walk_frame % 2])
        self.walk_frame += 1
        self.root.after(WALK_FRAME_MS, self._walk_animate)

    def _walk_move(self) -> None:
        if self.state != "walk" or self.dragging:
            return

        if self.walk_steps_left <= 0:
            self._stand_tick()
            return

        dx, dy = self.DELTAS[self.direction]
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w = self.label.winfo_width() or DISPLAY_HEIGHT
        win_h = self.label.winfo_height() or DISPLAY_HEIGHT

        next_x = self.x + dx
        next_y = self.y + dy

        if next_x < 0 or next_x + win_w > screen_w or next_y < 0 or next_y + win_h > screen_h:
            self._stand_tick()
            return

        self.x = next_x
        self.y = next_y
        self.walk_steps_left -= 1
        self._place_window()
        self.root.after(MOVE_INTERVAL_MS, self._walk_move)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    DesktopPet().run()
