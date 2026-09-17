# -*- coding: utf-8 -*-
"""Phase B: DesktopPet method wiring for scoped align."""
from __future__ import annotations

from pathlib import Path

PET = Path(r"c:\Users\36255\Desktop\VpetAOBA\VpetPNG\pet.py")


def once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        if f"# scoped:{label}" in text or new[:60] in text:
            print(f"  skip: {label}")
            return text
        raise SystemExit(f"missing for {label}:\n{old[:160]!r}")
    print(f"  patch: {label}")
    return text.replace(old, new, 1)


def main() -> None:
    pet = PET.read_text(encoding="utf-8")

    # Init font_family + apply on start
    pet = once(
        pet,
        "        self.font_size = max(8, min(24, int(app_cfg.get(\"font_size\", 12))))\n"
        "        self.app_config = app_cfg\n",
        "        self.font_size = max(8, min(24, int(app_cfg.get(\"font_size\", 12))))\n"
        "        self.font_family = _normalize_font_family_key(app_cfg.get(\"font_family\"))\n"
        "        self.app_config = app_cfg\n"
        "        self.app_config[\"font_family\"] = self.font_family\n",
        "init-font-family",
    )
    pet = once(
        pet,
        "            _init_ui_fonts(self.root, self.font_size)\n",
        "            _init_ui_fonts(self.root, self.font_size, self.font_family)\n",
        "init-ui-fonts-family",
    )

    # _set_font_family after _set_font_size
    if "def _set_font_family" not in pet:
        pet = once(
            pet,
            "    def _set_font_size(self, size: int, *, refresh_settings: bool = False, toast: bool = True) -> None:\n",
            "    def _set_font_family(self, family_key: str, *, refresh_settings: bool = False, toast: bool = True) -> None:\n"
            "        key = _normalize_font_family_key(family_key)\n"
            "        if key == getattr(self, \"font_family\", None):\n"
            "            if refresh_settings:\n"
            "                self._refresh_panel_settings_if_open()\n"
            "            return\n"
            "        self.font_family = key\n"
            "        _apply_ui_font_family(key, self.root)\n"
            "        _apply_font_size(int(self.font_size))\n"
            "        self.app_config[\"font_family\"] = key\n"
            "        self._defer_save_app_config()\n"
            "        if toast:\n"
            "            self._show_toast(f\"字体样式：{key}\", PIXEL_COLOR)\n"
            "        if refresh_settings:\n"
            "            try:\n"
            "                self.root.after(30, self._rebuild_panel_settings_if_open)\n"
            "            except Exception:\n"
            "                self._rebuild_panel_settings_if_open()\n\n"
            "    def _set_font_size(self, size: int, *, refresh_settings: bool = False, toast: bool = True) -> None:\n",
            "set-font-family-method",
        )

    # Settings UI: font family row before font size
    pet = once(
        pet,
        "        font_row = tk.Frame(frame, bg=MENU_BG)\n"
        "        font_row.pack(fill=tk.X, pady=(4, 2))\n"
        "        tk.Label(font_row, text=\"字体大小\", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG).pack(side=tk.LEFT)\n",
        "        fam_row = tk.Frame(frame, bg=MENU_BG)\n"
        "        fam_row.pack(fill=tk.X, pady=(4, 2))\n"
        "        tk.Label(fam_row, text=\"字体样式\", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG).pack(side=tk.LEFT)\n"
        "        fam_val = tk.Label(\n"
        "            fam_row,\n"
        "            text=str(getattr(self, \"font_family\", UI_FONT_FAMILY_DEFAULT)),\n"
        "            font=PIXEL_FONT,\n"
        "            fg=\"#88ccff\",\n"
        "            bg=MENU_BG,\n"
        "        )\n"
        "        fam_val.pack(side=tk.RIGHT)\n"
        "        ui[\"font_family_val\"] = fam_val\n"
        "        fam_btns_row = tk.Frame(frame, bg=MENU_BG)\n"
        "        fam_btns_row.pack(fill=tk.X, pady=(2, 4))\n"
        "        fam_btns: dict = {}\n"
        "        cur_fam = _normalize_font_family_key(getattr(self, \"font_family\", UI_FONT_FAMILY_DEFAULT))\n"
        "        for name in UI_FONT_FAMILY_ORDER:\n"
        "            mark = \" ✓\" if name == cur_fam else \"\"\n"
        "            btn = tk.Button(\n"
        "                fam_btns_row,\n"
        "                text=f\"{name}{mark}\",\n"
        "                command=lambda n=name: self._set_font_family(n, refresh_settings=True),\n"
        "                font=HINT_FONT,\n"
        "                bg=MENU_ACTIVE if mark else MENU_BG,\n"
        "                fg=MENU_FG,\n"
        "                relief=tk.FLAT,\n"
        "                highlightthickness=1,\n"
        "                highlightbackground=MENU_BTN_EDGE if mark else \"#223044\",\n"
        "                padx=8,\n"
        "                pady=3,\n"
        "            )\n"
        "            btn.pack(side=tk.LEFT, padx=2)\n"
        "            fam_btns[name] = btn\n"
        "        ui[\"font_family_btns\"] = fam_btns\n\n"
        "        font_row = tk.Frame(frame, bg=MENU_BG)\n"
        "        font_row.pack(fill=tk.X, pady=(4, 2))\n"
        "        tk.Label(font_row, text=\"字体大小\", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG).pack(side=tk.LEFT)\n",
        "settings-font-family-ui",
    )

    # sync settings font family
    pet = once(
        pet,
        "        # 字体\n"
        "        font_val = ui.get(\"font_val\")\n",
        "        # 字体样式\n"
        "        cur_fam = _normalize_font_family_key(getattr(self, \"font_family\", UI_FONT_FAMILY_DEFAULT))\n"
        "        fam_val = ui.get(\"font_family_val\")\n"
        "        try:\n"
        "            if fam_val and fam_val.winfo_exists():\n"
        "                fam_val.configure(text=str(cur_fam))\n"
        "        except Exception:\n"
        "            pass\n"
        "        for name, btn in (ui.get(\"font_family_btns\") or {}).items():\n"
        "            self._style_settings_choice_btn(btn, selected=name == cur_fam, label=name)\n\n"
        "        # 字体\n"
        "        font_val = ui.get(\"font_val\")\n",
        "sync-font-family",
    )

    # Outfit: group order + preview stand
    pet = once(
        pet,
        "        group_order = [g for g in (\"我的\", \"公开\") if g in by_group] + [\n"
        "            g for g in by_group if g not in (\"我的\", \"公开\")\n"
        "        ]\n",
        "        group_order = [g for g in pet_outfit.OUTFIT_GROUP_ORDER if g in by_group] + [\n"
        "            g for g in by_group if g not in pet_outfit.OUTFIT_GROUP_ORDER\n"
        "        ]\n",
        "outfit-group-order",
    )
    pet = once(
        pet,
        "        def refresh_preview() -> None:\n"
        "            size = preview_size - 8\n"
        "            base = Image.new(\"RGBA\", (size, size), preview_pad)\n"
        "            try:\n"
        "                stand_path = None\n"
        "                for cand in (\n"
        "                    GALLERY_DIR / \"stand.png\",\n"
        "                    SPRITES_DIR / \"stand.png\",\n"
        "                    SPRITES_DIR / \"stand.jpg\",\n"
        "                ):\n"
        "                    if cand.is_file():\n"
        "                        stand_path = cand\n"
        "                        break\n"
        "                if stand_path is not None:\n"
        "                    stand = Image.open(stand_path).convert(\"RGBA\")\n"
        "                    stand.thumbnail((size, size), Image.Resampling.NEAREST)\n"
        "                    ox = (size - stand.width) // 2\n"
        "                    oy = size - stand.height\n"
        "                    base.alpha_composite(stand, (ox, oy))\n"
        "            except Exception:\n"
        "                pass\n",
        "        def refresh_preview() -> None:\n"
        "            size = preview_size - 8\n"
        "            base = Image.new(\"RGBA\", (size, size), preview_pad)\n"
        "            try:\n"
        "                # 预览固定普通图组 + 默认人格 stand（无边框、非金目）\n"
        "                with _sprite_pack_override(SPRITE_PACK_NORMAL):\n"
        "                    with _persona_override(PERSONA_DEFAULT):\n"
        "                        stand = _sprite_rgba_image(\"stand.jpg\", size)\n"
        "                if stand is not None and stand.getbbox():\n"
        "                    base.alpha_composite(stand, (0, 0))\n"
        "            except Exception:\n"
        "                pass\n",
        "outfit-preview-stand",
    )
    # pick_asset defaults_for 4-tuple safe
    pet = once(
        pet,
        "        def pick_asset(kind: str, ref: str) -> None:\n"
        "            dnx, dny, dsc = pet_outfit.defaults_for(kind, ref)\n",
        "        def pick_asset(kind: str, ref: str) -> None:\n"
        "            _defs = pet_outfit.defaults_for(kind, ref)\n"
        "            dnx, dny, dsc = float(_defs[0]), float(_defs[1]), float(_defs[2])\n",
        "outfit-defaults-unpack",
    )

    # Owner prompt: avatar picker before entry
    pet = once(
        pet,
        "        frame = tk.Frame(win, bg=MENU_BG, padx=14, pady=12)\n"
        "        frame.pack()\n"
        "        tk.Label(frame, text=\"所属人\", font=PIXEL_FONT, fg=THEME_PINK, bg=MENU_BG).pack(anchor=tk.W)\n"
        "        tk.Label(\n"
        "            frame,\n"
        "            text=\"先告诉我，你要怎么被称呼吧～\\n昵称仅可填写一次，之后不能更改。\",\n"
        "            font=(\"Courier New\", 9),\n"
        "            fg=\"#aabbcc\",\n"
        "            bg=MENU_BG,\n"
        "            justify=tk.LEFT,\n"
        "            wraplength=300,\n"
        "        ).pack(anchor=tk.W, pady=(6, 8))\n"
        "        entry = tk.Entry(frame, width=18, font=PIXEL_FONT)\n"
        "        entry.pack(anchor=tk.W)\n"
        "        tip = tk.Label(frame, text=\"\", font=(\"Courier New\", 9), fg=\"#ff8866\", bg=MENU_BG)\n"
        "        tip.pack(anchor=tk.W, pady=(4, 0))\n\n"
        "        def confirm(_event=None) -> None:\n"
        "            raw = entry.get().strip()[:OWNER_NAME_MAX_LEN]\n"
        "            if not raw:\n"
        "                tip.config(text=\"昵称不能为空哦，再想想～\")\n"
        "                return\n"
        "            self.pet_profile[\"owner_name\"] = raw\n"
        "            self.pet_profile[\"owner_set_at\"] = datetime.now().strftime(\"%Y-%m-%d %H:%M\")\n"
        "            _save_pet_profile(self.pet_profile)\n",
        "        frame = tk.Frame(win, bg=MENU_BG, padx=14, pady=12)\n"
        "        frame.pack()\n"
        "        tk.Label(frame, text=\"所属人\", font=PIXEL_FONT, fg=THEME_PINK, bg=MENU_BG).pack(anchor=tk.W)\n"
        "        tk.Label(\n"
        "            frame,\n"
        "            text=\"先告诉我，你要怎么被称呼吧～\\n昵称仅可填写一次，之后不能更改。\",\n"
        "            font=(\"Courier New\", 9),\n"
        "            fg=\"#aabbcc\",\n"
        "            bg=MENU_BG,\n"
        "            justify=tk.LEFT,\n"
        "            wraplength=300,\n"
        "        ).pack(anchor=tk.W, pady=(6, 8))\n"
        "        av_row = tk.Frame(frame, bg=MENU_BG)\n"
        "        av_row.pack(anchor=tk.W, fill=tk.X, pady=(0, 6))\n"
        "        av_lbl = tk.Label(av_row, bg=MENU_BG, bd=0)\n"
        "        av_lbl.pack(side=tk.LEFT)\n"
        "        av_btns = tk.Frame(av_row, bg=MENU_BG)\n"
        "        av_btns.pack(side=tk.LEFT, padx=(10, 0))\n"
        "        avatar_pick: dict = {\"path\": None}\n"
        "        av_keep: dict = {\"photo\": None}\n\n"
        "        def _refresh_avatar_preview(path=None) -> None:\n"
        "            try:\n"
        "                if path:\n"
        "                    pil = _pil_circle_avatar_from_image(Image.open(path), 48)\n"
        "                else:\n"
        "                    pil = _pil_default_owner_avatar(48)\n"
        "                photo = ImageTk.PhotoImage(pil.convert(\"RGBA\"))\n"
        "                av_lbl.configure(image=photo)\n"
        "                av_keep[\"photo\"] = photo\n"
        "            except Exception:\n"
        "                pass\n\n"
        "        def _pick_avatar() -> None:\n"
        "            path = filedialog.askopenfilename(\n"
        "                parent=win,\n"
        "                title=\"选择所属人头像\",\n"
        "                filetypes=[(\"图片\", \"*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.gif\"), (\"全部\", \"*.*\")],\n"
        "            )\n"
        "            if not path:\n"
        "                return\n"
        "            avatar_pick[\"path\"] = path\n"
        "            _refresh_avatar_preview(path)\n"
        "            tip.config(text=\"\")\n\n"
        "        def _clear_avatar() -> None:\n"
        "            avatar_pick[\"path\"] = None\n"
        "            _refresh_avatar_preview(None)\n"
        "            tip.config(text=\"\")\n\n"
        "        tk.Button(av_btns, text=\"选择头像\", command=_pick_avatar, font=HINT_FONT, bg=MENU_ACTIVE, fg=MENU_FG).pack(anchor=tk.W)\n"
        "        tk.Button(av_btns, text=\"用默认剪影\", command=_clear_avatar, font=HINT_FONT, bg=MENU_BG, fg=\"#8899aa\").pack(anchor=tk.W, pady=(4, 0))\n"
        "        _refresh_avatar_preview(None)\n"
        "        entry = tk.Entry(frame, width=18, font=PIXEL_FONT)\n"
        "        entry.pack(anchor=tk.W)\n"
        "        tip = tk.Label(frame, text=\"\", font=(\"Courier New\", 9), fg=\"#ff8866\", bg=MENU_BG)\n"
        "        tip.pack(anchor=tk.W, pady=(4, 0))\n\n"
        "        def confirm(_event=None) -> None:\n"
        "            raw = entry.get().strip()[:OWNER_NAME_MAX_LEN]\n"
        "            if not raw:\n"
        "                tip.config(text=\"昵称不能为空哦，再想想～\")\n"
        "                return\n"
        "            self.pet_profile[\"owner_name\"] = raw\n"
        "            self.pet_profile[\"owner_set_at\"] = datetime.now().strftime(\"%Y-%m-%d %H:%M\")\n"
        "            try:\n"
        "                pick = avatar_pick.get(\"path\")\n"
        "                if pick:\n"
        "                    self.pet_profile[\"owner_avatar\"] = _save_owner_avatar_image(str(pick))\n"
        "                else:\n"
        "                    self.pet_profile[\"owner_avatar\"] = \"\"\n"
        "                    if OWNER_AVATAR_FILE.is_file():\n"
        "                        try:\n"
        "                            OWNER_AVATAR_FILE.unlink()\n"
        "                        except Exception:\n"
        "                            pass\n"
        "            except Exception:\n"
        "                self.pet_profile[\"owner_avatar\"] = \"\"\n"
        "            _save_pet_profile(self.pet_profile)\n",
        "owner-prompt-avatar",
    )

    # Owner info: head with avatar + change button
    pet = once(
        pet,
        "        _pack_theme_motif_banner(frame, OWNER_THEME, \"owner\")\n"
        "        tk.Label(frame, text=\"所属人\", font=PIXEL_FONT, fg=accent, bg=paper).pack(anchor=tk.W)\n"
        "        tk.Label(frame, text=name, font=PIXEL_FONT, fg=ink, bg=paper).pack(anchor=tk.W, pady=(4, 2))\n"
        "        if set_at:\n",
        "        _pack_theme_motif_banner(frame, OWNER_THEME, \"owner\")\n"
        "        tk.Label(frame, text=\"所属人\", font=PIXEL_FONT, fg=accent, bg=paper).pack(anchor=tk.W)\n"
        "        head = tk.Frame(frame, bg=paper)\n"
        "        head.pack(anchor=tk.W, fill=tk.X, pady=(4, 2))\n"
        "        av_lbl = tk.Label(head, bg=paper, bd=0)\n"
        "        av_lbl.pack(side=tk.LEFT)\n"
        "        name_col = tk.Frame(head, bg=paper)\n"
        "        name_col.pack(side=tk.LEFT, padx=(10, 0))\n"
        "        tk.Label(name_col, text=name, font=PIXEL_FONT, fg=ink, bg=paper).pack(anchor=tk.W)\n"
        "        av_keep: dict = {\"photo\": None}\n\n"
        "        def _refresh_info_avatar() -> None:\n"
        "            try:\n"
        "                pil = _load_owner_avatar_pil(self.pet_profile, 48)\n"
        "                photo = ImageTk.PhotoImage(pil.convert(\"RGBA\"))\n"
        "                av_lbl.configure(image=photo)\n"
        "                av_keep[\"photo\"] = photo\n"
        "            except Exception:\n"
        "                pass\n\n"
        "        def _change_avatar() -> None:\n"
        "            path = filedialog.askopenfilename(\n"
        "                parent=win,\n"
        "                title=\"更换所属人头像\",\n"
        "                filetypes=[(\"图片\", \"*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.gif\"), (\"全部\", \"*.*\")],\n"
        "            )\n"
        "            if not path:\n"
        "                return\n"
        "            try:\n"
        "                self.pet_profile[\"owner_avatar\"] = _save_owner_avatar_image(path)\n"
        "                _save_pet_profile(self.pet_profile)\n"
        "                _refresh_info_avatar()\n"
        "                self._show_toast(\"头像已更新\", THEME_PINK)\n"
        "            except Exception:\n"
        "                self._show_toast(\"头像保存失败\", \"#ff8866\")\n\n"
        "        tk.Button(\n"
        "            name_col,\n"
        "            text=\"更换头像\",\n"
        "            command=_change_avatar,\n"
        "            font=HINT_FONT,\n"
        "            bg=paper,\n"
        "            fg=muted,\n"
        "            relief=tk.FLAT,\n"
        "            cursor=\"hand2\",\n"
        "        ).pack(anchor=tk.W, pady=(2, 0))\n"
        "        _refresh_info_avatar()\n"
        "        if set_at:\n",
        "owner-info-avatar",
    )

    # Preset dialog chat_role
    pet = once(
        pet,
        "        reply = random.choice(answers)\n"
        "        self._show_speech_dialog(f\"你：{question}\", auto_hide_ms=2400, use_border5=True)\n"
        "        delay = _typing_duration_ms(f\"你：{question}\") + 500\n"
        "        self.preset_dialog_job = self.root.after(\n"
        "            delay, lambda q=question, r=reply: self._show_preset_dialog_answer(q, r)\n"
        "        )\n\n"
        "    def _show_preset_dialog_answer(self, question: str, reply: str) -> None:\n"
        "        self.preset_dialog_job = None\n"
        "        text = (reply or \"\").strip() or \"……\"\n"
        "        # 打完后再多留一会儿，长回复按字数加长停留\n"
        "        hold_ms = max(6200, 2800 + len(text) * 45)\n"
        "        self._show_speech_dialog(\n"
        "            text,\n"
        "            auto_hide_ms=hold_ms,\n"
        "            typewriter_ms=TYPEWRITER_MS,\n"
        "            use_border5=True,\n"
        "        )\n",
        "        reply = random.choice(answers)\n"
        "        self._show_speech_dialog(\n"
        "            question,\n"
        "            auto_hide_ms=2400,\n"
        "            use_border5=False,\n"
        "            chat_role=\"owner\",\n"
        "            instant=True,\n"
        "        )\n"
        "        delay = _typing_duration_ms(question) + 500\n"
        "        self.preset_dialog_job = self.root.after(\n"
        "            delay, lambda q=question, r=reply, pool=answers: self._show_preset_dialog_answer(q, r, pool)\n"
        "        )\n\n"
        "    def _show_preset_dialog_answer(self, question: str, reply: str, answers: tuple[str, ...] | None = None) -> None:\n"
        "        self.preset_dialog_job = None\n"
        "        text = (reply or \"\").strip() or \"……\"\n"
        "        hold_ms = max(6200, 2800 + len(text) * 45)\n"
        "        self._show_speech_dialog(\n"
        "            text,\n"
        "            auto_hide_ms=hold_ms,\n"
        "            typewriter_ms=TYPEWRITER_MS,\n"
        "            use_border5=False,\n"
        "            chat_role=\"aoba\",\n"
        "        )\n",
        "preset-dialog-chat-role",
    )

    # _show_speech_dialog add chat_role
    pet = once(
        pet,
        "    def _show_speech_dialog(\n"
        "        self,\n"
        "        text: str,\n"
        "        auto_hide_ms: int | None = None,\n"
        "        *,\n"
        "        on_complete=None,\n"
        "        color: str = SPEECH_FG_VPET,\n"
        "        typewriter_ms: int | None = None,\n"
        "        instant: bool = False,\n"
        "        use_border5: bool = False,\n"
        "        from_voice: bool = False,\n"
        "    ) -> None:\n",
        "    def _show_speech_dialog(\n"
        "        self,\n"
        "        text: str,\n"
        "        auto_hide_ms: int | None = None,\n"
        "        *,\n"
        "        on_complete=None,\n"
        "        color: str = SPEECH_FG_VPET,\n"
        "        typewriter_ms: int | None = None,\n"
        "        instant: bool = False,\n"
        "        use_border5: bool = False,\n"
        "        from_voice: bool = False,\n"
        "        chat_role: str | None = None,\n"
        "    ) -> None:\n",
        "speech-chat-role-sig",
    )
    pet = once(
        pet,
        "        self.speech_use_border5 = use_border5\n"
        "        self._speech_border5_peak = (0, 0)\n"
        "        self._speech_border_layout_sig = None\n",
        "        self.speech_use_border5 = use_border5\n"
        "        role = (chat_role or \"\").strip().lower() or None\n"
        "        if role in (\"pet\", \"eiden\", \"苍叶\", \"aoba\"):\n"
        "            role = \"aoba\"\n"
        "        elif role in (\"owner\", \"user\", \"me\", \"所属人\"):\n"
        "            role = \"owner\"\n"
        "        self.speech_chat_role = role\n"
        "        if role:\n"
        "            # 头像气泡路径不用 border5\n"
        "            self.speech_use_border5 = False\n"
        "        self._speech_border5_peak = (0, 0)\n"
        "        self._speech_border_layout_sig = None\n",
        "speech-chat-role-set",
    )

    # layout: prefer chat bubble
    pet = once(
        pet,
        "    def _layout_speech_dialog(self, text: str, color: str, *, use_border5: bool | None = None) -> bool:\n"
        "        if not self.speech_canvas or not self.speech_canvas.winfo_exists():\n"
        "            return False\n"
        "        if use_border5 is None:\n"
        "            use_border5 = getattr(self, \"speech_use_border5\", False)\n",
        "    def _chat_display_name(self, role: str) -> str:\n"
        "        if role == \"owner\":\n"
        "            return (\n"
        "                _owner_display_name(self.pet_profile)\n"
        "                or str(getattr(self, \"owner_name\", \"\") or \"\").strip()\n"
        "                or \"你\"\n"
        "            )\n"
        "        return \"苍叶\"\n\n"
        "    def _chat_avatar_photo(self, role: str) -> ImageTk.PhotoImage:\n"
        "        size = CHAT_AVATAR_PX\n"
        "        if role == \"owner\":\n"
        "            pil = _load_owner_avatar_pil(self.pet_profile, size)\n"
        "        else:\n"
        "            pil = _load_pet_avatar_pil(size)\n"
        "        return ImageTk.PhotoImage(pil.convert(\"RGBA\"))\n\n"
        "    def _layout_chat_bubble(self, text: str, color: str) -> bool:\n"
        "        canvas = self.speech_canvas\n"
        "        if not canvas or not canvas.winfo_exists():\n"
        "            return False\n"
        "        role = str(getattr(self, \"speech_chat_role\", \"\") or \"aoba\")\n"
        "        is_owner = role == \"owner\"\n"
        "        fill = CHAT_OWNER_BUBBLE_FILL if is_owner else CHAT_PET_BUBBLE_FILL\n"
        "        text_fg = color if color and color not in (SPEECH_FG_VPET, \"\") else (\n"
        "            CHAT_OWNER_BUBBLE_FG if is_owner else CHAT_PET_BUBBLE_FG\n"
        "        )\n"
        "        name = self._chat_display_name(role)\n"
        "        measure = text if (text and str(text).strip()) else (getattr(self, \"speech_full_text\", \"\") or \" \")\n"
        "        wrap_w = CHAT_BUBBLE_MAX_W\n"
        "        content_w, content_h = self._speech_label_content_size(measure, wrap_w=wrap_w)\n"
        "        content_w = min(wrap_w, max(48, content_w))\n"
        "        content_h = max(18, content_h)\n"
        "        pad_x, pad_y = CHAT_BUBBLE_PAD_X, CHAT_BUBBLE_PAD_Y\n"
        "        av = CHAT_AVATAR_PX\n"
        "        gap = CHAT_BUBBLE_GAP\n"
        "        name_h = 16\n"
        "        body_w = content_w + pad_x * 2\n"
        "        body_h = content_h + pad_y * 2\n"
        "        tail_w = 7\n"
        "        bubble_w = body_w + tail_w\n"
        "        total_w = av + gap + bubble_w\n"
        "        total_h = max(av + name_h, body_h + name_h)\n"
        "        layout_sig = (role, total_w, total_h, body_w, body_h, content_w, content_h, name, fill)\n"
        "        if layout_sig == getattr(self, \"_speech_border_layout_sig\", None) and getattr(self, \"speech_text_item\", None) is not None:\n"
        "            try:\n"
        "                canvas.itemconfigure(self.speech_text_item, text=text or \"\", fill=text_fg)\n"
        "            except Exception:\n"
        "                pass\n"
        "            return True\n"
        "        self._speech_border_layout_sig = layout_sig\n"
        "        canvas.delete(\"all\")\n"
        "        self.speech_text_item = None\n"
        "        canvas.config(width=total_w, height=total_h, bg=\"magenta\")\n"
        "        body_img = _solid_bubble_on_magenta(body_w, body_h, fill)\n"
        "        body_photo = ImageTk.PhotoImage(body_img)\n"
        "        av_photo = self._chat_avatar_photo(role)\n"
        "        self.speech_chat_photos = [body_photo, av_photo]\n"
        "        self.speech_border_photo = body_photo\n"
        "        if is_owner:\n"
        "            av_x = total_w - av\n"
        "            body_x = 0\n"
        "            tail_x0, tail_x1 = body_w - 1, body_w + tail_w - 1\n"
        "        else:\n"
        "            av_x = 0\n"
        "            body_x = av + gap + tail_w\n"
        "            bub_x = av + gap\n"
        "            tail_x0, tail_x1 = bub_x, bub_x + tail_w\n"
        "        canvas.create_text(av_x + av // 2, 0, text=name, fill=CHAT_NAME_FG, font=HINT_FONT, anchor=tk.N)\n"
        "        av_y = name_h\n"
        "        canvas.create_image(av_x, av_y, image=av_photo, anchor=tk.NW)\n"
        "        body_y = name_h + max(0, (av - body_h) // 2)\n"
        "        mid_y = body_y + body_h // 2\n"
        "        if is_owner:\n"
        "            canvas.create_polygon(tail_x0, mid_y - 6, tail_x1, mid_y, tail_x0, mid_y + 6, fill=fill, outline=\"\")\n"
        "        else:\n"
        "            canvas.create_polygon(tail_x1, mid_y - 6, tail_x0, mid_y, tail_x1, mid_y + 6, fill=fill, outline=\"\")\n"
        "        canvas.create_image(body_x, body_y, image=body_photo, anchor=tk.NW)\n"
        "        self.speech_text_item = canvas.create_text(\n"
        "            body_x + pad_x, body_y + pad_y, text=text or \"\", fill=text_fg, font=CUTE_FONT, anchor=tk.NW, width=max(40, content_w)\n"
        "        )\n"
        "        if self.speech_dialog and self.speech_dialog.winfo_exists():\n"
        "            self.speech_dialog.update_idletasks()\n"
        "            return self._place_speech_popup(self.speech_dialog)\n"
        "        return True\n\n"
        "    def _layout_speech_dialog(self, text: str, color: str, *, use_border5: bool | None = None) -> bool:\n"
        "        if not self.speech_canvas or not self.speech_canvas.winfo_exists():\n"
        "            return False\n"
        "        if getattr(self, \"speech_chat_role\", None):\n"
        "            return self._layout_chat_bubble(text, color)\n"
        "        if use_border5 is None:\n"
        "            use_border5 = getattr(self, \"speech_use_border5\", False)\n",
        "layout-chat-bubble",
    )

    # AI: replace _toggle_ai_chat with style gate + panel
    old_toggle = '''    def _toggle_ai_chat(self) -> None:
        self._hide_main_menu()
        if self.ai_chat_win and self.ai_chat_win.winfo_exists():
            self._close_ai_chat()
            return
        if self._vpet_voice_category_ready("email") and random.random() < 0.5:
            self._addon_voice_vpet("email")

        self.ai_chat_win = tk.Toplevel(self.root)
        self.ai_chat_win.overrideredirect(True)
        self._apply_window_layer(self.ai_chat_win)
        self.ai_chat_win.configure(bg="#111122")

        border = tk.Frame(self.ai_chat_win, bg=PIXEL_COLOR, padx=1, pady=1)
        border.pack()
        inner = tk.Frame(border, bg="#111122", padx=6, pady=4)
        inner.pack()

        header = tk.Frame(inner, bg="#111122")
        header.pack(fill=tk.X)
        close_btn = tk.Label(
            header,
            text="×",
            font=("Courier New", 14, "bold"),
            fg=THEME_PINK,
            bg="#111122",
            cursor="hand2",
            padx=4,
        )
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", lambda _e: self._close_ai_chat())
        close_btn.bind("<FocusOut>", self._ai_chat_focus_out, add="+")
        close_btn.bind("<FocusIn>", self._ai_chat_focus_in, add="+")

        row = tk.Frame(inner, bg="#111122")
        row.pack(fill=tk.X)

        self.ai_input = tk.Entry(
            row, width=22, font=PIXEL_FONT, bg="#222233", fg=PIXEL_COLOR, insertbackground=PIXEL_COLOR
        )
        self.ai_input.pack(side=tk.LEFT, padx=(0, 4))
        self.ai_input.bind("<Return>", lambda _e: self._send_ai_message())
        self.ai_input.bind("<FocusOut>", self._ai_chat_focus_out, add="+")
        self.ai_input.bind("<FocusIn>", self._ai_chat_focus_in, add="+")

        send_btn = tk.Button(
            row,
            text="发送",
            command=self._send_ai_message,
            font=PIXEL_FONT,
            bg=MENU_ACTIVE,
            fg=MENU_FG,
            relief=tk.FLAT,
            padx=6,
        )
        send_btn.pack(side=tk.LEFT)
        send_btn.bind("<FocusOut>", self._ai_chat_focus_out, add="+")
        send_btn.bind("<FocusIn>", self._ai_chat_focus_in, add="+")
        self._place_ai_chat()
        self.ai_input.focus_set()
'''
    new_toggle = '''    def _toggle_ai_chat(self) -> None:
        self._hide_main_menu()
        if self.ai_chat_win and self.ai_chat_win.winfo_exists():
            self._close_ai_chat()
            return
        cfg = _load_ai_config()
        if not bool(cfg.get("style_setup_done", False)):
            self._open_ai_style_editor(initial=True, on_done=self._open_ai_chat_panel)
            return
        self._open_ai_chat_panel()

    def _open_ai_chat_panel(self) -> None:
        if self._closing or not self._alive():
            return
        if self.ai_chat_win and self.ai_chat_win.winfo_exists():
            try:
                self.ai_chat_win.lift()
                if self.ai_input:
                    self.ai_input.focus_set()
            except Exception:
                pass
            return
        if self._vpet_voice_category_ready("email") and random.random() < 0.5:
            self._addon_voice_vpet("email")

        self.ai_chat_win = tk.Toplevel(self.root)
        self.ai_chat_win.overrideredirect(True)
        self._apply_window_layer(self.ai_chat_win)
        self.ai_chat_win.configure(bg=MENU_BG)

        border = tk.Frame(self.ai_chat_win, bg=PIXEL_COLOR, padx=1, pady=1)
        border.pack()
        inner = tk.Frame(border, bg=MENU_BG, padx=6, pady=4)
        inner.pack()

        header = tk.Frame(inner, bg=MENU_BG)
        header.pack(fill=tk.X)
        style_btn = tk.Label(
            header,
            text="初始设置",
            font=HINT_FONT,
            fg=MENU_FG,
            bg=MENU_BG,
            cursor="hand2",
            padx=4,
        )
        style_btn.pack(side=tk.LEFT)
        style_btn.bind("<Button-1>", lambda _e: self._open_ai_style_editor(initial=False))
        style_btn.bind("<FocusOut>", self._ai_chat_focus_out, add="+")
        style_btn.bind("<FocusIn>", self._ai_chat_focus_in, add="+")
        close_btn = tk.Label(
            header,
            text="×",
            font=("Courier New", 14, "bold"),
            fg=THEME_PINK,
            bg=MENU_BG,
            cursor="hand2",
            padx=4,
        )
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", lambda _e: self._close_ai_chat())
        close_btn.bind("<FocusOut>", self._ai_chat_focus_out, add="+")
        close_btn.bind("<FocusIn>", self._ai_chat_focus_in, add="+")

        row = tk.Frame(inner, bg=MENU_BG)
        row.pack(fill=tk.X)

        self.ai_input = tk.Entry(
            row, width=22, font=PIXEL_FONT, bg="#eef6ff", fg=MENU_FG, insertbackground=MENU_FG
        )
        self.ai_input.pack(side=tk.LEFT, padx=(0, 4))
        self.ai_input.bind("<Return>", lambda _e: self._send_ai_message())
        self.ai_input.bind("<FocusOut>", self._ai_chat_focus_out, add="+")
        self.ai_input.bind("<FocusIn>", self._ai_chat_focus_in, add="+")

        send_btn = tk.Button(
            row,
            text="发送",
            command=self._send_ai_message,
            font=PIXEL_FONT,
            bg=MENU_ACTIVE,
            fg=MENU_FG,
            relief=tk.FLAT,
            padx=6,
        )
        send_btn.pack(side=tk.LEFT)
        send_btn.bind("<FocusOut>", self._ai_chat_focus_out, add="+")
        send_btn.bind("<FocusIn>", self._ai_chat_focus_in, add="+")
        self._place_ai_chat()
        self.ai_input.focus_set()

    def _open_ai_style_editor(self, *, initial: bool = False, on_done=None) -> None:
        if self._closing or not self._alive():
            return
        old = getattr(self, "ai_style_win", None)
        if old and old.winfo_exists():
            try:
                old.lift()
                old.focus_force()
            except Exception:
                pass
            return
        cfg = _load_ai_config()
        win = tk.Toplevel(self.root)
        self.ai_style_win = win
        win.title("苍叶 · AI 初始设置" if initial else "苍叶 · 性格与语风")
        win.configure(bg=MENU_BG)
        try:
            win.attributes("-topmost", True)
        except Exception:
            pass
        self._apply_window_layer(win)
        outer = tk.Frame(win, bg=MENU_BG, padx=12, pady=10)
        outer.pack()
        tk.Label(
            outer,
            text="先选一种感觉，再微调口癖 / 语气；也可选云端或本地开源千问。",
            bg=MENU_BG,
            fg=MENU_FG,
            font=HINT_FONT,
            wraplength=420,
            justify=tk.LEFT,
        ).pack(anchor=tk.W)

        fields: dict[str, tk.Text] = {}
        state: dict[str, str] = {
            "speech_quirk": str(cfg.get("speech_quirk") or ""),
            "personality_note": str(cfg.get("personality_note") or ""),
            "language_style": str(cfg.get("language_style") or ""),
            "tone_note": str(cfg.get("tone_note") or ""),
            "provider_preset": str(cfg.get("provider") or "dashscope"),
        }

        preset_row = tk.Frame(outer, bg=MENU_BG)
        preset_row.pack(fill=tk.X, pady=(8, 4))
        tk.Label(preset_row, text="性格预设", bg=MENU_BG, fg=MENU_FG, font=PIXEL_FONT).pack(side=tk.LEFT)

        def _apply_style_preset(name: str, patch: dict[str, str]) -> None:
            for k, v in patch.items():
                state[k] = v
                box = fields.get(k)
                if box is not None:
                    box.delete("1.0", tk.END)
                    box.insert("1.0", v)
            self._show_toast(f"已套用「{name}」", THEME_PINK, duration_ms=1400)

        for pname, ppatch in AI_STYLE_PRESETS:
            tk.Button(
                preset_row,
                text=pname,
                command=lambda n=pname, p=ppatch: _apply_style_preset(n, p),
                font=HINT_FONT,
                bg=MENU_ACTIVE,
                fg=MENU_FG,
                relief=tk.FLAT,
                padx=6,
            ).pack(side=tk.LEFT, padx=(6, 0))

        def _add_field(key: str, label: str, height: int = 2) -> None:
            tk.Label(outer, text=label, bg=MENU_BG, fg=MENU_FG, font=PIXEL_FONT).pack(anchor=tk.W, pady=(8, 2))
            box = tk.Text(outer, width=52, height=height, font=HINT_FONT, bg="#eef6ff", fg=MENU_FG, wrap=tk.WORD)
            box.insert("1.0", state.get(key, ""))
            box.pack(fill=tk.X)
            fields[key] = box

        _add_field("personality_note", "性格", 2)
        _add_field("tone_note", "语气", 2)
        _add_field("speech_quirk", "口癖", 2)
        _add_field("language_style", "语风（用词节奏）", 2)

        tk.Label(outer, text="对话模型（千问）", bg=MENU_BG, fg=MENU_FG, font=PIXEL_FONT).pack(anchor=tk.W, pady=(10, 2))
        model_row = tk.Frame(outer, bg=MENU_BG)
        model_row.pack(fill=tk.X)
        model_var = tk.StringVar(value=str(cfg.get("provider") or "dashscope"))
        provider_labels = {
            "dashscope": "云端·千问 Plus",
            "dashscope_max": "云端·千问 Max",
            "ollama": "本地·Ollama qwen2.5",
            "ollama_qwen3": "本地·Ollama qwen3",
        }
        for pid in ("dashscope", "dashscope_max", "ollama", "ollama_qwen3"):
            if pid not in AI_PROVIDER_PRESETS:
                continue
            tk.Radiobutton(
                model_row,
                text=provider_labels.get(pid, pid),
                variable=model_var,
                value=pid,
                bg=MENU_BG,
                fg=MENU_FG,
                selectcolor=MENU_BG,
                font=HINT_FONT,
                anchor=tk.W,
            ).pack(anchor=tk.W)

        key_row = tk.Frame(outer, bg=MENU_BG)
        key_row.pack(fill=tk.X, pady=(8, 0))
        tk.Label(key_row, text="API Key", width=8, anchor="w", bg=MENU_BG, fg=MENU_FG, font=PIXEL_FONT).pack(side=tk.LEFT)
        key_ent = tk.Entry(key_row, width=40, font=("Consolas", 9), bg="#eef6ff", fg=MENU_FG, show="*")
        key_ent.insert(0, str(cfg.get("api_key") or ""))
        key_ent.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_row = tk.Frame(outer, bg=MENU_BG)
        btn_row.pack(fill=tk.X, pady=(12, 0))

        def _close_editor() -> None:
            try:
                win.destroy()
            except Exception:
                pass
            self.ai_style_win = None

        def _save(and_open: bool = False) -> None:
            patch = {k: fields[k].get("1.0", tk.END).strip() for k in fields}
            patch["style_setup_done"] = True
            key_val = key_ent.get().strip()
            if key_val:
                patch["api_key"] = key_val
            pid = model_var.get() or "dashscope"
            preset = AI_PROVIDER_PRESETS.get(pid) or AI_PROVIDER_PRESETS.get("dashscope") or {}
            patch["provider"] = pid if pid.startswith("ollama") else "dashscope"
            if preset.get("base_url"):
                patch["base_url"] = preset.get("base_url")
            if preset.get("model"):
                patch["model"] = preset.get("model")
            if str(pid).startswith("ollama") and not key_val:
                patch["api_key"] = "ollama"
            _save_ai_config(patch)
            _close_editor()
            self._show_toast("AI 初始设置已保存", "#88aa88", duration_ms=1800)
            if and_open and callable(on_done):
                self.root.after(120, on_done)
            elif and_open:
                self.root.after(120, self._open_ai_chat_panel)

        tk.Button(
            btn_row,
            text="保存并开始对话" if initial else "保存",
            command=lambda: _save(and_open=bool(initial) or callable(on_done)),
            font=PIXEL_FONT,
            bg=MENU_ACTIVE,
            fg=MENU_FG,
            relief=tk.FLAT,
            padx=10,
        ).pack(side=tk.RIGHT)
        if initial:
            tk.Button(
                btn_row,
                text="稍后再说",
                command=lambda: (
                    _save_ai_config({"style_setup_done": True}),
                    _close_editor(),
                    self.root.after(80, self._open_ai_chat_panel),
                ),
                font=HINT_FONT,
                bg=MENU_BG,
                fg=MENU_FG,
                relief=tk.FLAT,
                padx=8,
            ).pack(side=tk.RIGHT, padx=(0, 8))
'''
    pet = once(pet, old_toggle, new_toggle, "ai-toggle-panel-style")

    # AI send/reply with chat_role + compose system prompt
    pet = once(
        pet,
        "    def _show_ai_reply(self, reply: str) -> None:\n"
        "        self.ai_reply_job = None\n"
        "        # 输入窗关掉也仍须弹出回答文本框（V-BORDER5 / 系统→对话）\n"
        "        text = (reply or \"\").strip() or \"……\"\n"
        "        self._show_speech_dialog(\n"
        "            text,\n"
        "            auto_hide_ms=AI_DIALOG_HIDE_MS,\n"
        "            typewriter_ms=TYPEWRITER_MS,\n"
        "            use_border5=True,\n"
        "        )\n",
        "    def _show_ai_reply(self, reply: str) -> None:\n"
        "        self.ai_reply_job = None\n"
        "        text = (reply or \"\").strip() or \"……\"\n"
        "        self._show_speech_dialog(\n"
        "            text,\n"
        "            auto_hide_ms=AI_DIALOG_HIDE_MS,\n"
        "            typewriter_ms=TYPEWRITER_MS,\n"
        "            use_border5=False,\n"
        "            chat_role=\"aoba\",\n"
        "        )\n",
        "ai-reply-chat-role",
    )
    pet = once(
        pet,
        "        self._cancel_ai_chat_close()\n"
        "        self._show_speech_dialog(f\"你：{text}\", auto_hide_ms=AI_DIALOG_HIDE_MS, use_border5=True)\n",
        "        self._cancel_ai_chat_close()\n"
        "        self._show_speech_dialog(\n"
        "            text,\n"
        "            auto_hide_ms=AI_DIALOG_HIDE_MS,\n"
        "            use_border5=False,\n"
        "            chat_role=\"owner\",\n"
        "            instant=True,\n"
        "        )\n",
        "ai-send-chat-role",
    )
    pet = once(
        pet,
        "        system = AI_SYSTEM_PROMPT\n"
        "        seed = str(getattr(self, \"_ai_topic_seed\", \"\") or \"\").strip()\n"
        "        keyword = str(getattr(self, \"_ai_topic_keyword\", \"\") or \"\").strip()\n"
        "        if seed or keyword:\n"
        "            extra = seed or f\"请围绕关键词「{keyword}」展开简短对话。\"\n"
        "            system = f\"{AI_SYSTEM_PROMPT} 额外：{extra}\"\n",
        "        system = _compose_ai_system_prompt(\n"
        "            config,\n"
        "            owner_name=_owner_display_name(self.pet_profile) or self.owner_name or \"\",\n"
        "        )\n"
        "        seed = str(getattr(self, \"_ai_topic_seed\", \"\") or \"\").strip()\n"
        "        keyword = str(getattr(self, \"_ai_topic_keyword\", \"\") or \"\").strip()\n"
        "        if seed or keyword:\n"
        "            extra = seed or f\"请围绕关键词「{keyword}」展开简短对话。\"\n"
        "            system = f\"{system} 额外：{extra}\"\n",
        "ai-compose-system",
    )

    # open_ai_chat_stub already calls _toggle_ai_chat - OK

    PET.write_text(pet, encoding="utf-8")
    print("phase B done")


if __name__ == "__main__":
    main()
