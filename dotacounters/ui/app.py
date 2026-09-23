"""Главное окно приложения: вкладки поиска, настроек и обновлений."""

import io
import os
import subprocess
import threading
import tkinter as tk
import webbrowser
from datetime import date
from tkinter import font as tkfont
from tkinter import ttk

from PIL import Image, ImageTk

from .. import updates
from ..config import load_config, update_config
from ..dotabuff import (
    DEFAULT_LIMIT, MAX_LIMIT, DotabuffError, FetchError, HeroNotFound,
    ParseError, fetch_counters,
)
from ..draft import MAX_ENEMIES, analyse
from ..heroes import suggest
from ..i18n import I18N
from ..net import create_scraper
from ..patches import fetch_current_patch
from ..themes import THEMES
from ..version import APP_VERSION
from .hero_browser import HeroBrowserModal
from .patch_notes import PatchNotesModal
from .suggestions import HeroSuggestions
from .winapi import set_title_bar_color


class DotaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DOTABUFF — Counter Intelligence")
        self.root.geometry("760x860")
        self.root.resizable(True, True)
        self.root.minsize(620, 620)

        # Load config
        cfg = load_config()
        self._theme_key = cfg.get("theme", "cyber")
        self._lang      = cfg.get("lang",  "en")
        self._limit     = self._clamp_limit(cfg.get("limit", DEFAULT_LIMIT))
        self.T          = THEMES[self._theme_key]
        self.tr         = I18N[self._lang]

        self.hero_images       = []
        self._placeholder_active = False
        self._patch_version    = "…"
        self._active_tab       = "search"   # search | draft | settings | updates
        self._enemies          = []         # вражеский состав для драфта
        self._update           = None       # dotacounters.updates.Update, когда есть
        self._update_btn       = None
        self._update_status    = None
        updates.cleanup_old()               # хвост от прошлого обновления

        self._setup_fonts()
        self._apply_theme_styles()
        self.root.configure(bg=self.T["BG_DARK"])
        self._build_ui()
        self._animate_scanline()
        set_title_bar_color(self.root)

        try:
            img = tk.PhotoImage(file="icon.png")
            self.root.tk.call("wm", "iconphoto", self.root._w, img)
        except Exception:
            pass

        threading.Thread(target=self._load_patch, daemon=True).start()
        self._start_update_check()

    # ── Theme & styles ────────────────────────────────────────────────────────

    def _apply_theme_styles(self):
        T = self.T
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=T["BG_DARK"])
        for name in ("Dark.Vertical.TScrollbar", "HB.Vertical.TScrollbar"):
            style.configure(name,
                            background=T["SCROLLBAR_BG"], troughcolor=T["SCROLLBAR_BG"],
                            bordercolor=T["SCROLLBAR_BG"], darkcolor=T["SCROLLBAR_BG"],
                            lightcolor=T["SCROLLBAR_BG"], arrowcolor=T["TEXT_DIM"],
                            relief="flat", borderwidth=0)
            style.map(name,
                      background=[("active", T["BG_PANEL"]), ("disabled", T["SCROLLBAR_BG"])],
                      arrowcolor=[("active", T["ACCENT"])])

    def _setup_fonts(self):
        self.font_title  = ("Courier New", 26, "bold")
        self.font_sub    = ("Courier New", 9)
        self.font_label  = ("Courier New", 11)
        self.font_entry  = ("Courier New", 14)
        self.font_btn    = ("Courier New", 12, "bold")
        self.font_result = ("Courier New", 12)
        self.font_status = ("Courier New", 10)
        self.font_tab    = ("Courier New", 10, "bold")

    # ── Full UI rebuild (called on theme/lang change) ─────────────────────────

    def _build_ui(self):
        for w in self.root.winfo_children():
            w.destroy()
        # Полотна, которые должно прокручивать колесо. Список пересобирается
        # вместе с интерфейсом: прежние виджеты только что уничтожены.
        self._scrollables = []
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.root.bind(seq, self._on_wheel)

        T = self.T
        self.root.configure(bg=T["BG_DARK"])
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        outer = tk.Frame(self.root, bg=T["BG_DARK"])
        outer.grid(row=0, column=0, sticky="nsew", padx=16, pady=12)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(4, weight=1)

        self._build_header(outer)
        self._build_tab_bar(outer)
        self._build_update_banner(outer)
        tk.Frame(outer, bg=T["BORDER"], height=1).grid(row=3, column=0, sticky="ew", pady=(0, 10))

        # Content frame — swapped by tabs
        self._content = tk.Frame(outer, bg=T["BG_DARK"])
        self._content.grid(row=4, column=0, sticky="nsew")
        self._content.columnconfigure(0, weight=1)
        self._content.rowconfigure(0, weight=1)

        self._build_search_page()
        self._build_draft_page()
        self._build_settings_page()
        self._build_updates_page()
        self._build_footer(outer)

        self._switch_tab(self._active_tab, rebuild=False)

    # ── Обновления программы ──────────────────────────────────────────────────

    def _build_update_banner(self, parent):
        """Полоса под вкладками. Пустая и скрытая, пока обновления нет."""
        T = self.T
        self._banner = tk.Frame(parent, bg=T["BG_PANEL"],
                                highlightbackground=T["ACCENT3"], highlightthickness=1)
        self._banner.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self._banner.grid_remove()
        self._banner_label = tk.Label(self._banner, text="", font=("Courier New", 10, "bold"),
                                      fg=T["ACCENT3"], bg=T["BG_PANEL"])
        self._banner_label.pack(side=tk.LEFT, padx=12, pady=7)
        self._banner_buttons = tk.Frame(self._banner, bg=T["BG_PANEL"])
        self._banner_buttons.pack(side=tk.RIGHT, padx=8)
        if getattr(self, "_update", None):
            self._show_update(self._update)

    def _banner_button(self, text, command, accent=False):
        T = self.T
        btn = tk.Button(self._banner_buttons, text=text, font=("Courier New", 9, "bold"),
                        bg=T["ACCENT"] if accent else T["BG_PANEL"],
                        fg=T["BG_DARK"] if accent else T["ACCENT3"],
                        activebackground=T["ACCENT2"] if accent else T["GLOW"],
                        activeforeground=T["BG_DARK"] if accent else T["ACCENT"],
                        relief="flat", bd=0, padx=12, pady=5, cursor="hand2",
                        command=command)
        btn.pack(side=tk.LEFT, padx=4)
        return btn

    def _start_update_check(self, manual=False):
        """Проверка раз в сутки; по кнопке — всегда."""
        if not manual:
            today = date.today().isoformat()
            if load_config().get("last_update_check") == today:
                return
            update_config(last_update_check=today)
        if manual:
            self._set_update_status(self.tr["upd_checking"])
        threading.Thread(target=self._check_updates, args=(manual,), daemon=True).start()

    def _check_updates(self, manual):
        found = updates.check()
        self.root.after(0, self._apply_update_check, found, manual)

    def _apply_update_check(self, found, manual):
        self._update = found
        if found:
            self._show_update(found)
            self._set_update_status(self.tr["upd_available"].format(version=found.version))
        elif manual:
            self._set_update_status(self.tr["upd_uptodate"].format(version=APP_VERSION))

    def _set_update_status(self, text):
        label = getattr(self, "_update_status", None)
        if label is not None:
            try:
                label.config(text=text)
            except tk.TclError:
                pass  # вкладку пересобрали

    def _show_update(self, update):
        self._banner_label.config(text=self.tr["upd_available"].format(version=update.version),
                                  fg=self.T["ACCENT3"])
        for w in self._banner_buttons.winfo_children():
            w.destroy()
        if updates.can_install():
            self._update_btn = self._banner_button(self.tr["upd_install_btn"],
                                                   self._install_update, accent=True)
        else:
            self._update_btn = None
        self._banner_button(self.tr["upd_page_btn"], lambda: webbrowser.open(update.page))
        self._banner_button("✕", self._hide_update)
        self._banner.grid()

    def _hide_update(self):
        self._banner.grid_remove()

    def _install_update(self):
        """Скачать, сверить сумму, заменить файл и перезапуститься."""
        if self._update_btn:
            self._update_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._run_install, daemon=True).start()

    def _run_install(self):
        update = self._update
        exe = updates.current_exe()
        target = exe + ".new"
        try:
            def progress(received, total):
                if total:
                    self.root.after(0, self._banner_label.config, {
                        "text": self.tr["upd_downloading"].format(
                            percent=min(100, int(100 * received / total)))})
            updates.download(update, target, progress=progress)
            self.root.after(0, self._banner_label.config,
                            {"text": self.tr["upd_installing"]})
            updates.install(target, exe)
        except Exception as exc:
            try:
                os.unlink(target)
            except OSError:
                pass
            self.root.after(0, self._update_failed, exc)
            return
        self.root.after(0, self._restart_after_update, exe)

    def _update_failed(self, exc):
        self._banner_label.config(text=self.tr["upd_error"].format(detail=exc),
                                  fg=self.T["ACCENT2"])
        if self._update_btn:
            self._update_btn.config(state=tk.NORMAL)

    def _restart_after_update(self, exe):
        self._banner_label.config(text=self.tr["upd_restart"])
        self.root.update_idletasks()
        subprocess.Popen([exe], cwd=os.path.dirname(exe), close_fds=True)
        self.root.destroy()

    def _on_wheel(self, event):
        """Прокрутить полотно, внутри которого оказался курсор.

        Привязка висит на окне, потому что события колеса от вложенных
        виджетов (карточек тем, подписей) до самого полотна не доходят.
        """
        widget = event.widget
        if isinstance(widget, str):
            try:
                widget = self.root.nametowidget(widget)
            except KeyError:
                return None
        while widget is not None:
            if widget in self._scrollables:
                if event.num == 4:
                    step = -1
                elif event.num == 5:
                    step = 1
                else:
                    step = int(-1 * event.delta / 120)
                widget.yview_scroll(step, "units")
                return "break"
            widget = getattr(widget, "master", None)
        return None

    def _build_header(self, parent):
        T, tr = self.T, self.tr
        hdr = tk.Frame(parent, bg=T["BG_DARK"])
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        tk.Frame(hdr, bg=T["ACCENT"], width=4).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        title_col = tk.Frame(hdr, bg=T["BG_DARK"])
        title_col.pack(side=tk.LEFT)
        tk.Label(title_col, text="DOTABUFF", font=self.font_title,
                 fg=T["ACCENT"], bg=T["BG_DARK"]).pack(anchor="w")
        tk.Label(title_col, text=tr["app_subtitle"],
                 font=self.font_sub, fg=T["TEXT_DIM"], bg=T["BG_DARK"]).pack(anchor="w")
        right = tk.Frame(hdr, bg=T["BG_DARK"])
        right.pack(side=tk.RIGHT, padx=(0, 4))
        right.columnconfigure(0, weight=0)
        tk.Label(right, text="◈ LIVE", font=("Courier New", 9, "bold"),
                 fg=T["ACCENT3"], bg=T["BG_DARK"]).pack(anchor="e")
        self.patch_label = tk.Label(right, text=f"PATCH {self._patch_version}",
                                    font=("Courier New", 9, "bold"),
                                    fg=T["ACCENT"], bg=T["BG_DARK"])
        self.patch_label.pack(side=tk.LEFT, anchor="e")
         # Кнопка-инфо рядом с патчем
        self._patch_info_btn = tk.Button(
            right, text="ℹ", font=("Courier New", 9, "bold"),
            bg=T["BG_DARK"], fg=T["TEXT_DIM"],
            activebackground=T["BG_DARK"], activeforeground=T["ACCENT"],
            relief="flat", bd=0, cursor="hand2",
            command=self._open_patch_notes
        )
        self._patch_info_btn.pack(side=tk.LEFT, padx=(4, 0), anchor="e")
        self._patch_info_btn.bind("<Enter>", lambda e: self._patch_info_btn.config(fg=T["ACCENT"]))
        self._patch_info_btn.bind("<Leave>", lambda e: self._patch_info_btn.config(fg=T["TEXT_DIM"]))

    def _build_tab_bar(self, parent):
        T, tr = self.T, self.tr
        bar = tk.Frame(parent, bg=T["BG_DARK"])
        bar.grid(row=1, column=0, sticky="ew", pady=(0, 0))

        self._tab_btns = {}
        tabs = [("search", tr["tab_search"]), ("draft", tr["tab_draft"]),
                ("settings", tr["tab_settings"]), ("updates", tr["tab_updates"])]
        for key, label in tabs:
            btn = tk.Button(
                bar, text=label, font=self.font_tab,
                bg=T["BG_DARK"], fg=T["TEXT_DIM"],
                activebackground=T["BG_PANEL"], activeforeground=T["ACCENT"],
                relief="flat", bd=0, padx=18, pady=7,
                cursor="hand2",
                command=lambda k=key: self._switch_tab(k)
            )
            btn.pack(side=tk.LEFT)
            self._tab_btns[key] = btn

    def _switch_tab(self, key, rebuild=True):
        T = self.T
        self._active_tab = key
        # Style tab buttons
        for k, btn in self._tab_btns.items():
            if k == key:
                btn.config(fg=T["ACCENT"],
                           bg=T["BG_PANEL"],
                           relief="flat")
            else:
                btn.config(fg=T["TEXT_DIM"],
                           bg=T["BG_DARK"],
                           relief="flat")
        # Показываем одну страницу, остальные прячем
        pages = {"search": self._search_page, "draft": self._draft_page,
                 "settings": self._settings_page, "updates": self._updates_page}
        for name, page in pages.items():
            if name == key:
                page.grid(row=0, column=0, sticky="nsew")
            else:
                page.grid_remove()

    # ── Search page ───────────────────────────────────────────────────────────

    def _build_search_page(self):
        T, tr = self.T, self.tr
        page = tk.Frame(self._content, bg=T["BG_DARK"])
        self._search_page = page
        page.columnconfigure(0, weight=1)
        page.rowconfigure(1, weight=0)
        page.rowconfigure(2, weight=1)

        # Search card
        card = tk.Frame(page, bg=T["BG_CARD"],
                        highlightbackground=T["BORDER"], highlightthickness=1)
        card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        inner = tk.Frame(card, bg=T["BG_CARD"])
        inner.pack(fill=tk.X, padx=14, pady=12)
        tk.Label(inner, text=tr["hero_name_label"], font=self.font_label,
                 fg=T["TEXT_DIM"], bg=T["BG_CARD"]).pack(anchor="w", pady=(0, 4))
        row = tk.Frame(inner, bg=T["BG_CARD"])
        row.pack(fill=tk.X)

        ef = tk.Frame(row, bg=T["ACCENT"], padx=1, pady=1)
        ef.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ei = tk.Frame(ef, bg=T["BG_PANEL"])
        ei.pack(fill=tk.BOTH)
        self.hero_entry = tk.Entry(ei, font=self.font_entry,
                                   bg=T["BG_PANEL"], fg=T["TEXT_PRIMARY"],
                                   insertbackground=T["ACCENT"],
                                   relief="flat", bd=6, highlightthickness=0)
        self.hero_entry.pack(fill=tk.X)
        self.hero_entry.bind("<FocusIn>",  self._on_entry_focus)
        self.hero_entry.bind("<FocusOut>", self._on_entry_blur)
        self._show_placeholder()
        self._suggest = HeroSuggestions(
            page, self.hero_entry, T, self.font_entry,
            on_accept=self._search_hero,
            placeholder_active=lambda: self._placeholder_active)


        # Сколько строк показывать в каждом разделе (1..MAX_LIMIT).
        cnt = tk.Frame(row, bg=T["BG_CARD"])
        cnt.pack(side=tk.LEFT, padx=(0, 10))
        tk.Label(cnt, text=tr["count_label"], font=("Courier New", 9, "bold"),
                 fg=T["TEXT_DIM"], bg=T["BG_CARD"]).pack(side=tk.LEFT, padx=(0, 6))
        self._limit_var = tk.StringVar(value=str(self._limit))
        self._limit_spin = tk.Spinbox(
            cnt, from_=1, to=MAX_LIMIT, width=3, textvariable=self._limit_var,
            font=("Courier New", 12, "bold"), justify="center",
            state="readonly", cursor="hand2",
            bg=T["BG_PANEL"], fg=T["ACCENT3"], readonlybackground=T["BG_PANEL"],
            buttonbackground=T["BG_PANEL"], insertbackground=T["ACCENT"],
            relief="flat", bd=0, highlightthickness=1,
            highlightbackground=T["BORDER"], highlightcolor=T["ACCENT"],
            command=self._on_limit_change)
        self._limit_spin.pack(side=tk.LEFT, ipady=4)

        self.heroes_btn = tk.Button(row, text=tr["btn_heroes"],
                                    font=("Courier New", 11, "bold"),
                                    bg=T["BG_PANEL"], fg=T["ACCENT3"],
                                    activebackground=T["GLOW"], activeforeground=T["ACCENT"],
                                    relief="flat", bd=0, padx=12, pady=8,
                                    cursor="hand2",
                                    highlightbackground=T["BORDER"], highlightthickness=1,
                                    command=self._open_hero_browser)
        self.heroes_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.heroes_btn.bind("<Enter>", lambda e: self.heroes_btn.config(bg=T["GLOW"], fg=T["ACCENT"]))
        self.heroes_btn.bind("<Leave>", lambda e: self.heroes_btn.config(bg=T["BG_PANEL"], fg=T["ACCENT3"]))

        self.search_btn = tk.Button(row, text=tr["btn_search"], font=self.font_btn,
                                    bg=T["ACCENT"], fg=T["BG_DARK"],
                                    activebackground=T["ACCENT"], activeforeground=T["BG_DARK"],
                                    relief="flat", bd=0, padx=18, pady=8,
                                    cursor="hand2", command=self.start_search)
        self.search_btn.pack(side=tk.LEFT)
        self.search_btn.bind("<Enter>", lambda e: self.search_btn.config(bg=T["ACCENT2"]))
        self.search_btn.bind("<Leave>", lambda e: self.search_btn.config(bg=T["ACCENT"]))

        # Status bar
        bar = tk.Frame(page, bg=T["BG_DARK"])
        bar.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self.status_dot = tk.Label(bar, text="●", font=("Courier New", 9),
                                   fg=T["TEXT_MUTED"], bg=T["BG_DARK"])
        self.status_dot.pack(side=tk.LEFT)
        self.status_text = tk.Label(bar, text=tr["status_await"],
                                    font=self.font_status, fg=T["TEXT_DIM"], bg=T["BG_DARK"])
        self.status_text.pack(side=tk.LEFT, padx=4)
        self.scanline_label = tk.Label(bar, text="", font=("Courier New", 9),
                                       fg=T["ACCENT"], bg=T["BG_DARK"])
        self.scanline_label.pack(side=tk.RIGHT)

        # Results area
        wrap = tk.Frame(page, bg=T["BG_DARK"])
        wrap.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
        wrap.columnconfigure(1, weight=1)
        wrap.rowconfigure(0, weight=1)
        tk.Frame(wrap, bg=T["ACCENT"], width=2).grid(row=0, column=0, sticky="ns")
        result_card = tk.Frame(wrap, bg=T["BG_CARD"],
                               highlightbackground=T["BORDER"], highlightthickness=1)
        result_card.grid(row=0, column=1, sticky="nsew")
        result_card.columnconfigure(0, weight=1)
        result_card.rowconfigure(1, weight=1)
        card_hdr = tk.Frame(result_card, bg=T["BG_PANEL"])
        card_hdr.grid(row=0, column=0, sticky="ew")
        tk.Label(card_hdr, text=tr["output_header"],
                 font=("Courier New", 9, "bold"),
                 fg=T["TEXT_DIM"], bg=T["BG_PANEL"], pady=6).pack(side=tk.LEFT)
        tk.Label(card_hdr, text=tr["output_source"],
                 font=("Courier New", 8),
                 fg=T["TEXT_MUTED"], bg=T["BG_PANEL"]).pack(side=tk.RIGHT)
        tf = tk.Frame(result_card, bg=T["BG_CARD"])
        tf.grid(row=1, column=0, sticky="nsew")
        tf.columnconfigure(0, weight=1)
        tf.rowconfigure(0, weight=1)
        self.result_area = tk.Text(tf, wrap=tk.WORD, font=self.font_result,
                                   bg=T["BG_CARD"], fg=T["TEXT_PRIMARY"],
                                   insertbackground=T["ACCENT"],
                                   selectbackground=T["GLOW"],
                                   relief="flat", bd=0, padx=14, pady=10, spacing2=2)
        self.result_area.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(tf, orient="vertical", style="Dark.Vertical.TScrollbar",
                           command=self.result_area.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.result_area.config(yscrollcommand=sb.set)
        self._setup_tags()
        self._show_welcome()

    # ── Вкладка драфта ────────────────────────────────────────────────────────

    def _build_draft_page(self):
        T, tr = self.T, self.tr
        page = tk.Frame(self._content, bg=T["BG_DARK"])
        self._draft_page = page
        page.columnconfigure(0, weight=1)
        page.rowconfigure(2, weight=1)

        card = tk.Frame(page, bg=T["BG_CARD"],
                        highlightbackground=T["BORDER"], highlightthickness=1)
        card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        inner = tk.Frame(card, bg=T["BG_CARD"])
        inner.pack(fill=tk.X, padx=14, pady=12)
        tk.Label(inner, text=tr["draft_label"], font=self.font_label,
                 fg=T["TEXT_DIM"], bg=T["BG_CARD"]).pack(anchor="w", pady=(0, 4))

        row = tk.Frame(inner, bg=T["BG_CARD"])
        row.pack(fill=tk.X)
        ef = tk.Frame(row, bg=T["ACCENT"], padx=1, pady=1)
        ef.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ei = tk.Frame(ef, bg=T["BG_PANEL"])
        ei.pack(fill=tk.BOTH)
        self.draft_entry = tk.Entry(ei, font=self.font_entry,
                                    bg=T["BG_PANEL"], fg=T["TEXT_PRIMARY"],
                                    insertbackground=T["ACCENT"],
                                    relief="flat", bd=6, highlightthickness=0)
        self.draft_entry.pack(fill=tk.X)
        self._draft_suggest = HeroSuggestions(
            page, self.draft_entry, T, self.font_entry, on_accept=self._add_enemy)
        self.draft_entry.bind("<FocusOut>", lambda e: self._draft_suggest.hide_later())

        self._draft_browse_btn = tk.Button(
            row, text=tr["btn_heroes"], font=("Courier New", 11, "bold"),
            bg=T["BG_PANEL"], fg=T["ACCENT3"],
            activebackground=T["GLOW"], activeforeground=T["ACCENT"],
            relief="flat", bd=0, padx=12, pady=8, cursor="hand2",
            highlightbackground=T["BORDER"], highlightthickness=1,
            command=lambda: HeroBrowserModal(self.root, T, tr, on_select=self._add_enemy))
        self._draft_browse_btn.pack(side=tk.LEFT, padx=(0, 10))

        self._draft_btn = tk.Button(row, text=tr["draft_btn"], font=self.font_btn,
                                    bg=T["ACCENT"], fg=T["BG_DARK"],
                                    activebackground=T["ACCENT2"], activeforeground=T["BG_DARK"],
                                    relief="flat", bd=0, padx=18, pady=8,
                                    cursor="hand2", command=self.start_draft)
        self._draft_btn.pack(side=tk.LEFT)

        # Выбранные враги — по «фишке» на каждого, с крестиком
        self._draft_chips = tk.Frame(inner, bg=T["BG_CARD"])
        self._draft_chips.pack(fill=tk.X, pady=(10, 0))

        bar = tk.Frame(page, bg=T["BG_DARK"])
        bar.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self._draft_status = tk.Label(bar, text=tr["draft_hint"], font=self.font_status,
                                      fg=T["TEXT_DIM"], bg=T["BG_DARK"])
        self._draft_status.pack(side=tk.LEFT)

        wrap = tk.Frame(page, bg=T["BG_DARK"])
        wrap.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
        wrap.columnconfigure(1, weight=1)
        wrap.rowconfigure(0, weight=1)
        tk.Frame(wrap, bg=T["ACCENT"], width=2).grid(row=0, column=0, sticky="ns")
        result_card = tk.Frame(wrap, bg=T["BG_CARD"],
                               highlightbackground=T["BORDER"], highlightthickness=1)
        result_card.grid(row=0, column=1, sticky="nsew")
        result_card.columnconfigure(0, weight=1)
        result_card.rowconfigure(0, weight=1)
        tf = tk.Frame(result_card, bg=T["BG_CARD"])
        tf.grid(row=0, column=0, sticky="nsew")
        tf.columnconfigure(0, weight=1)
        tf.rowconfigure(0, weight=1)
        self.draft_area = tk.Text(tf, wrap=tk.WORD, font=self.font_result,
                                  bg=T["BG_CARD"], fg=T["TEXT_PRIMARY"],
                                  insertbackground=T["ACCENT"], selectbackground=T["GLOW"],
                                  relief="flat", bd=0, padx=14, pady=10, spacing2=3,
                                  state=tk.DISABLED)
        self.draft_area.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(tf, orient="vertical", style="Dark.Vertical.TScrollbar",
                           command=self.draft_area.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.draft_area.config(yscrollcommand=sb.set)
        for tag, colour in (("good", T["ACCENT"]), ("bad", T["ACCENT2"]),
                            ("divider", T["TEXT_MUTED"]), ("hero", T["TEXT_PRIMARY"]),
                            ("dim", T["TEXT_DIM"]), ("error", T["ACCENT2"])):
            self.draft_area.tag_config(tag, foreground=colour)
        self.draft_area.tag_config("good", foreground=T["ACCENT"],
                                   font=("Courier New", 12, "bold"))
        self.draft_area.tag_config("bad", foreground=T["ACCENT2"],
                                   font=("Courier New", 12, "bold"))

        self._render_chips()

    def _render_chips(self):
        """Перерисовать список выбранных врагов."""
        T, tr = self.T, self.tr
        for w in self._draft_chips.winfo_children():
            w.destroy()
        if not self._enemies:
            tk.Label(self._draft_chips, text=tr["draft_empty"], font=("Courier New", 9),
                     fg=T["TEXT_MUTED"], bg=T["BG_CARD"]).pack(side=tk.LEFT)
            return
        for hero in self._enemies:
            chip = tk.Frame(self._draft_chips, bg=T["BG_PANEL"],
                            highlightbackground=T["BORDER"], highlightthickness=1)
            chip.pack(side=tk.LEFT, padx=(0, 6))
            tk.Label(chip, text=hero, font=("Courier New", 10),
                     fg=T["ACCENT3"], bg=T["BG_PANEL"]).pack(side=tk.LEFT, padx=(8, 4), pady=3)
            close = tk.Button(chip, text="✕", font=("Courier New", 9, "bold"),
                              bg=T["BG_PANEL"], fg=T["TEXT_DIM"],
                              activebackground=T["BG_PANEL"], activeforeground=T["ACCENT2"],
                              relief="flat", bd=0, cursor="hand2",
                              command=lambda h=hero: self._remove_enemy(h))
            close.pack(side=tk.LEFT, padx=(0, 6))

    def _add_enemy(self, hero):
        """Добавить врага: имя приводится к известному герою, дубли отбрасываются."""
        matches = suggest(hero, limit=1)
        name = matches[0] if matches else hero.strip()
        self.draft_entry.delete(0, tk.END)
        if not name:
            return
        if name in self._enemies:
            self._draft_status.config(text=self.tr["draft_dup"].format(hero=name),
                                      fg=self.T["TEXT_DIM"])
            return
        if len(self._enemies) >= MAX_ENEMIES:
            self._draft_status.config(text=self.tr["draft_full"].format(max=MAX_ENEMIES),
                                      fg=self.T["ACCENT2"])
            return
        self._enemies.append(name)
        self._render_chips()
        self._draft_status.config(text=self.tr["draft_hint"], fg=self.T["TEXT_DIM"])
        self._switch_tab("draft")

    def _remove_enemy(self, hero):
        if hero in self._enemies:
            self._enemies.remove(hero)
            self._render_chips()

    def start_draft(self):
        if not self._enemies:
            self._draft_status.config(text=self.tr["draft_empty"], fg=self.T["ACCENT2"])
            return
        tr = self.tr
        self._draft_btn.config(state=tk.DISABLED, text=tr["draft_working"])
        self._draft_status.config(text=tr["status_scanning"], fg=self.T["ACCENT3"])
        self.draft_area.config(state=tk.NORMAL)
        self.draft_area.delete(1.0, tk.END)
        self.draft_area.insert(tk.END, tr["loading_msg"], "dim")
        self.draft_area.config(state=tk.DISABLED)
        threading.Thread(target=self._bg_draft, args=(list(self._enemies),),
                         daemon=True).start()

    def _bg_draft(self, enemies):
        """Страница на каждого врага, затем сложение матчапов."""
        # Одна сессия на весь подбор: на серии запросов с новым соединением
        # каждый раз Cloudflare отбивает часть из них.
        scraper = create_scraper()
        reports, failed = {}, []
        for hero in enemies:
            try:
                reports[hero] = fetch_counters(hero, scraper=scraper, limit=self._limit)
            except DotabuffError as exc:
                failed.append((hero, exc))
            except Exception as exc:
                failed.append((hero, FetchError(str(exc))))
        result = analyse(reports, limit=self._limit) if reports else None
        self.root.after(0, self._apply_draft, result, failed)

    def _apply_draft(self, result, failed):
        tr, T = self.tr, self.T
        area = self.draft_area
        area.config(state=tk.NORMAL)
        area.delete(1.0, tk.END)
        self.hero_images = []
        scraper = create_scraper()

        for hero, exc in failed:
            area.insert(tk.END, tr["draft_failed"].format(hero=hero, detail=exc), "error")
        if result and result.skipped:
            area.insert(tk.END, tr["draft_skipped"].format(
                heroes=", ".join(result.skipped)), "error")

        if not result or not result.picks:
            if not failed:
                area.insert(tk.END, tr["draft_nothing"], "error")
            area.config(state=tk.DISABLED)
            self._draft_status.config(text=tr["status_failed"], fg=T["ACCENT2"])
            self._draft_btn.config(state=tk.NORMAL, text=tr["draft_btn"])
            return

        rule = "  " + "─" * 46 + "\n"
        against = ", ".join(result.enemies)
        for tag, title, rows in (("good", tr["draft_best"], result.picks),
                                 ("bad", tr["draft_worst"], result.avoid)):
            area.insert(tk.END, rule, "divider")
            area.insert(tk.END, f"  {title}  ◈  {against}\n", tag)
            area.insert(tk.END, rule, "divider")
            for pick in rows:
                self._insert_icon(scraper, pick.icon_url, area)
                area.insert(tk.END, f" {pick.hero:<21}", "hero")
                area.insert(tk.END, "  %+.2f%%\n" % pick.total, tag)
            area.insert(tk.END, "\n", "divider")
        area.insert(tk.END, tr["draft_footnote"], "dim")

        area.config(state=tk.DISABLED)
        self._draft_status.config(text=tr["status_complete"], fg=T["ACCENT"])
        self._draft_btn.config(state=tk.NORMAL, text=tr["draft_btn"])

    # ── Settings page ─────────────────────────────────────────────────────────

    def _build_settings_page(self):
        T, tr = self.T, self.tr
        page = tk.Frame(self._content, bg=T["BG_DARK"])
        self._settings_page = page
        page.columnconfigure(0, weight=1)
        page.rowconfigure(0, weight=1)

        # Scrollable canvas
        canvas = tk.Canvas(page, bg=T["BG_DARK"], bd=0, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(page, orient="vertical", style="Dark.Vertical.TScrollbar",
                           command=canvas.yview)
        sb.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=sb.set)
        inner = tk.Frame(canvas, bg=T["BG_DARK"])
        cw = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))
        self._scrollables.append(canvas)

        inner.columnconfigure(0, weight=1)
        pad = {"padx": 20, "pady": (0, 16)}

        # ── Settings header ───────────────────────────────────────────────────
        hdr = tk.Frame(inner, bg=T["BG_DARK"])
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(6, 18))
        tk.Frame(hdr, bg=T["ACCENT"], width=3).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        lbl = tk.Frame(hdr, bg=T["BG_DARK"])
        lbl.pack(side=tk.LEFT)
        tk.Label(lbl, text=tr["set_title"], font=("Courier New", 18, "bold"),
                 fg=T["ACCENT"], bg=T["BG_DARK"]).pack(anchor="w")
        tk.Label(lbl, text=tr["set_subtitle"], font=("Courier New", 9),
                 fg=T["TEXT_DIM"], bg=T["BG_DARK"]).pack(anchor="w")

        # ── THEME section ─────────────────────────────────────────────────────
        self._add_section_header(inner, 1, tr["set_theme_head"], tr["set_theme_sub"])
        theme_grid = tk.Frame(inner, bg=T["BG_DARK"])
        theme_grid.grid(row=2, column=0, sticky="ew", **pad)
        theme_grid.columnconfigure((0, 1, 2, 3, 4), weight=1)

        self._theme_var = tk.StringVar(value=self._theme_key)
        theme_items = list(THEMES.items())
        for col, (tkey, tdata) in enumerate(theme_items):
            is_active = (tkey == self._theme_key)
            name = tdata[f"name_{self._lang}"]
            self._make_theme_card(theme_grid, tkey, tdata, name, col, is_active)

        # ── LANGUAGE section ──────────────────────────────────────────────────
        self._add_section_header(inner, 3, tr["set_lang_head"], tr["set_lang_sub"])
        lang_row = tk.Frame(inner, bg=T["BG_DARK"])
        lang_row.grid(row=4, column=0, sticky="ew", **pad)

        self._lang_var = tk.StringVar(value=self._lang)
        for lkey, lbl_text in [("en", tr["set_lang_en"]), ("ru", tr["set_lang_ru"])]:
            self._make_lang_btn(lang_row, lkey, lbl_text)

        # ── ABOUT section ─────────────────────────────────────────────────────
        self._add_section_header(inner, 5, tr["set_about_head"], "")
        about_card = tk.Frame(inner, bg=T["BG_CARD"],
                              highlightbackground=T["BORDER"], highlightthickness=1)
        about_card.grid(row=6, column=0, sticky="ew", **pad)
        about_card.columnconfigure(1, weight=1)

        rows_info = [
            (tr["set_ver"],    tr["set_ver_val"]),
            (tr["set_author"], tr["set_author_val"]),
            (tr["set_data"],   tr["set_data_val"]),
            (tr["set_patch"],  tr["set_patch_val"]),
            (tr["set_built"],  tr["set_built_val"]),
        ]
        # Каждая запись занимает две строки сетки: сама запись и разделитель
        # под ней. Раньше разделитель клали в ту же строку, и он перечёркивал
        # текст.
        for r, (label, val) in enumerate(rows_info):
            tk.Label(about_card, text=f"  {label}", font=("Courier New", 9, "bold"),
                     fg=T["TEXT_DIM"], bg=T["BG_CARD"],
                     pady=5).grid(row=r * 2, column=0, sticky="w")
            tk.Label(about_card, text=val, font=("Courier New", 9),
                     fg=T["TEXT_PRIMARY"], bg=T["BG_CARD"],
                     pady=5).grid(row=r * 2, column=1, sticky="w", padx=(10, 14))
            if r < len(rows_info) - 1:
                tk.Frame(about_card, bg=T["BORDER"], height=1).grid(
                    row=r * 2 + 1, column=0, columnspan=2, sticky="ew")

        # Description
        desc_card = tk.Frame(inner, bg=T["BG_PANEL"],
                             highlightbackground=T["BORDER"], highlightthickness=1)
        desc_card.grid(row=7, column=0, sticky="ew", padx=20, pady=(0, 24))
        tk.Label(desc_card, text=tr["set_desc"],
                 font=("Courier New", 9), fg=T["TEXT_DIM"], bg=T["BG_PANEL"],
                 justify=tk.LEFT, padx=16, pady=12).pack(anchor="w")

    # ── Updates page ──────────────────────────────────────────────────────────

    def _build_updates_page(self):
        T, tr = self.T, self.tr
        page = tk.Frame(self._content, bg=T["BG_DARK"])
        self._updates_page = page
        page.columnconfigure(0, weight=1)
        page.rowconfigure(0, weight=1)

        # Scrollable canvas
        canvas = tk.Canvas(page, bg=T["BG_DARK"], bd=0, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(page, orient="vertical", style="Dark.Vertical.TScrollbar",
                           command=canvas.yview)
        sb.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=sb.set)
        inner = tk.Frame(canvas, bg=T["BG_DARK"])
        cw = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))
        self._scrollables.append(canvas)

        inner.columnconfigure(0, weight=1)

        # Header
        hdr = tk.Frame(inner, bg=T["BG_DARK"])
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(6, 18))
        tk.Frame(hdr, bg=T["ACCENT"], width=3).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        lbl = tk.Frame(hdr, bg=T["BG_DARK"])
        lbl.pack(side=tk.LEFT)
        tk.Label(lbl, text=tr["upd_title"], font=("Courier New", 18, "bold"),
                 fg=T["ACCENT"], bg=T["BG_DARK"]).pack(anchor="w")
        tk.Label(lbl, text=tr["upd_subtitle"], font=("Courier New", 9),
                 fg=T["TEXT_DIM"], bg=T["BG_DARK"]).pack(anchor="w")

        # Проверка обновлений вручную
        check = tk.Frame(hdr, bg=T["BG_DARK"])
        check.pack(side=tk.RIGHT)
        btn = tk.Button(check, text=tr["upd_check_btn"], font=("Courier New", 9, "bold"),
                        bg=T["BG_PANEL"], fg=T["ACCENT3"],
                        activebackground=T["GLOW"], activeforeground=T["ACCENT"],
                        relief="flat", bd=0, padx=12, pady=6, cursor="hand2",
                        highlightbackground=T["BORDER"], highlightthickness=1,
                        command=lambda: self._start_update_check(manual=True))
        btn.pack(anchor="e")
        self._update_status = tk.Label(check, text="", font=("Courier New", 8),
                                       fg=T["TEXT_DIM"], bg=T["BG_DARK"])
        self._update_status.pack(anchor="e", pady=(4, 0))

        # Updates card
        card = tk.Frame(inner, bg=T["BG_CARD"],
                        highlightbackground=T["BORDER"], highlightthickness=1)
        card.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 24))
        card.columnconfigure(0, weight=1)

        text = tk.Text(card, wrap=tk.WORD, font=("Courier New", 10),
                       bg=T["BG_CARD"], fg=T["TEXT_PRIMARY"],
                       insertbackground=T["ACCENT"],
                       selectbackground=T["GLOW"],
                       relief="flat", bd=0, padx=16, pady=12, spacing2=2, height=10)
        text.grid(row=0, column=0, sticky="ew")
        text.tag_config("version", foreground=T["ACCENT"],
                        font=("Courier New", 11, "bold"), spacing1=4)
        for line in tr["upd_text"].split("\n"):
            is_header = line.startswith("v") and line[1:2].isdigit()
            text.insert(tk.END, line + "\n", "version" if is_header else ())
        text.delete("end-2c")  # лишний перевод строки в конце
        text.config(state=tk.DISABLED)

        # Высота поля — по фактической высоте текста с учётом переносов. С жёсткой
        # высотой в 10 строк история из двух версий обрезалась. Считаем в пикселях:
        # заголовки версий крупнее основного шрифта и с отступом, и счёт строк
        # занижал высоту. Пересчитываем при изменении ширины — от неё зависят
        # переносы.
        line_px = tkfont.Font(font=text.cget("font")).metrics("linespace")

        def fit_height(event=None):
            shown = text.count("1.0", "end", "ypixels")
            pixels = (shown[0] if isinstance(shown, tuple) else shown) or 0
            lines = max(1, -(-pixels // line_px))  # округление вверх
            if int(text.cget("height")) != lines:
                text.config(height=lines)
        text.bind("<Configure>", fit_height)

    def _add_section_header(self, parent, row, title, subtitle):
        T = self.T
        f = tk.Frame(parent, bg=T["BG_DARK"])
        f.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 8))
        tk.Label(f, text=title, font=("Courier New", 10, "bold"),
                 fg=T["ACCENT3"], bg=T["BG_DARK"]).pack(side=tk.LEFT)
        if subtitle:
            tk.Label(f, text=f"  —  {subtitle}", font=("Courier New", 9),
                     fg=T["TEXT_MUTED"], bg=T["BG_DARK"]).pack(side=tk.LEFT)
        # Линия идёт ПОСЛЕ текста и добирает оставшуюся ширину. Раньше она
        # ложилась в ту же ячейку сетки, что и подписи, и перечёркивала их.
        tk.Frame(f, bg=T["BORDER"], height=1).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(12, 0))

    def _make_theme_card(self, parent, tkey, tdata, name, col, is_active):
        T = self.T
        border_color = T["ACCENT"] if is_active else T["BORDER"]
        card = tk.Frame(parent, bg=tdata["BG_CARD"],
                        highlightbackground=border_color, highlightthickness=2,
                        cursor="hand2")
        card.grid(row=0, column=col, sticky="ew", padx=4, pady=2)

        # Color preview strip
        strip = tk.Frame(card, bg=tdata["BG_PANEL"], height=6)
        strip.pack(fill=tk.X)
        for c, color in enumerate([tdata["ACCENT"], tdata["ACCENT2"], tdata["ACCENT3"]]):
            tk.Frame(strip, bg=color, width=8, height=6).pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(card, text=name, font=("Courier New", 8, "bold"),
                 fg=tdata["ACCENT"], bg=tdata["BG_CARD"],
                 pady=4, padx=6).pack()

        if is_active:
            tk.Label(card, text="✓ ACTIVE", font=("Courier New", 7),
                     fg=tdata["ACCENT3"], bg=tdata["BG_CARD"]).pack(pady=(0, 4))
        else:
            tk.Label(card, text="", font=("Courier New", 7),
                     bg=tdata["BG_CARD"]).pack(pady=(0, 4))

        def on_click(k=tkey):
            self._set_theme(k)
        for w in [card, strip]:
            w.bind("<Button-1>", lambda e, k=tkey: on_click(k))
            w.bind("<Enter>",    lambda e, c=card, td=tdata: c.config(
                highlightbackground=td["ACCENT"]))
            w.bind("<Leave>",    lambda e, c=card, k=tkey: c.config(
                highlightbackground=T["ACCENT"] if k == self._theme_key else T["BORDER"]))
        for lbl in card.winfo_children():
            lbl.bind("<Button-1>", lambda e, k=tkey: on_click(k))

    def _make_lang_btn(self, parent, lkey, label):
        T = self.T
        is_active = (lkey == self._lang)
        bg = T["ACCENT"] if is_active else T["BG_PANEL"]
        fg = T["BG_DARK"] if is_active else T["TEXT_PRIMARY"]
        btn = tk.Button(parent, text=label, font=("Courier New", 11, "bold"),
                        bg=bg, fg=fg,
                        activebackground=T["ACCENT"], activeforeground=T["BG_DARK"],
                        relief="flat", bd=0, padx=24, pady=8,
                        cursor="hand2", command=lambda k=lkey: self._set_lang(k))
        btn.pack(side=tk.LEFT, padx=(0, 8))
        if not is_active:
            btn.bind("<Enter>",  lambda e, b=btn: b.config(bg=T["GLOW"], fg=T["ACCENT"]))
            btn.bind("<Leave>",  lambda e, b=btn: b.config(bg=T["BG_PANEL"], fg=T["TEXT_PRIMARY"]))

    # ── Theme / lang switching ────────────────────────────────────────────────

    def _set_theme(self, key):
        if key == self._theme_key:
            return
        self._theme_key = key
        self.T = THEMES[key]
        self._save_prefs()
        self._rebuild()

    def _set_lang(self, lang):
        if lang == self._lang:
            return
        self._lang = lang
        self.tr = I18N[lang]
        self._save_prefs()
        self._rebuild()

    @staticmethod
    def _clamp_limit(value):
        """Привести значение к допустимому диапазону 1..MAX_LIMIT."""
        try:
            n = int(value)
        except (TypeError, ValueError):
            n = DEFAULT_LIMIT
        return max(1, min(n, MAX_LIMIT))

    def _on_limit_change(self):
        """Новое значение применится при следующем поиске."""
        self._limit = self._clamp_limit(self._limit_var.get())
        self._limit_var.set(str(self._limit))
        self._save_prefs()

    def _save_prefs(self):
        update_config(theme=self._theme_key, lang=self._lang, limit=self._limit)

    def _rebuild(self):
        self._apply_theme_styles()
        self._build_ui()
        set_title_bar_color(self.root)

    # ── Footer ────────────────────────────────────────────────────────────────

    def _build_footer(self, parent):
        T, tr = self.T, self.tr
        ft = tk.Frame(parent, bg=T["BG_DARK"])
        ft.grid(row=5, column=0, sticky="ew", pady=(6, 0))
        tk.Label(ft, text=tr["footer_hint"],
                 font=("Courier New", 8), fg=T["TEXT_MUTED"], bg=T["BG_DARK"]).pack(side=tk.LEFT)

    # ── Patch loader ──────────────────────────────────────────────────────────

    def _load_patch(self):
        version = fetch_current_patch()
        self._patch_version = version
        self.root.after(0, self._apply_patch_label, version)

    def _apply_patch_label(self, version):
        try:
            self.patch_label.config(text=f"PATCH {version}")
        except Exception:
            pass

    # ── Tags ──────────────────────────────────────────────────────────────────

    def _setup_tags(self):
        T = self.T
        self.result_area.tag_config("bad",     foreground=T["ACCENT2"], font=("Courier New", 10, "bold"))
        self.result_area.tag_config("good",    foreground=T["ACCENT"],  font=("Courier New", 10, "bold"))
        self.result_area.tag_config("header",  foreground=T["ACCENT3"], font=("Courier New", 10, "bold"))
        self.result_area.tag_config("divider", foreground=T["TEXT_MUTED"])
        self.result_area.tag_config("hero",    foreground=T["TEXT_PRIMARY"])
        self.result_area.tag_config("wr_bad",  foreground=T["ACCENT2"])
        self.result_area.tag_config("wr_good", foreground=T["ACCENT"])
        self.result_area.tag_config("dim",     foreground=T["TEXT_DIM"])
        self.result_area.tag_config("error",   foreground=T["ACCENT2"], font=("Courier New", 10, "bold"))
        self.result_area.tag_config("loading", foreground=T["ACCENT3"])

    # ── Placeholder ───────────────────────────────────────────────────────────

    def _show_placeholder(self):
        T, tr = self.T, self.tr
        self.hero_entry.insert(0, tr["placeholder"])
        self.hero_entry.config(fg=T["TEXT_DIM"])
        self._placeholder_active = True

    def _on_entry_focus(self, event):
        if self._placeholder_active:
            self.hero_entry.delete(0, tk.END)
            self.hero_entry.config(fg=self.T["TEXT_PRIMARY"])
            self._placeholder_active = False

    def _on_entry_blur(self, event):
        if not self.hero_entry.get():
            self._show_placeholder()
        self._suggest.hide_later()

    # ── Scanline animation ────────────────────────────────────────────────────

    _scan_frames = ["▰▱▱▱▱", "▰▰▱▱▱", "▰▰▰▱▱", "▰▰▰▰▱", "▰▰▰▰▰"]
    _scan_idx = 0

    def _animate_scanline(self):
        try:
            self.scanline_label.config(text=self._scan_frames[self._scan_idx])
        except Exception:
            pass
        self._scan_idx = (self._scan_idx + 1) % len(self._scan_frames)
        self.root.after(150, self._animate_scanline)

    def _set_status(self, text, color=None):
        if color is None:
            color = self.T["TEXT_DIM"]
        try:
            self.status_text.config(text=text, fg=color)
            self.status_dot.config(fg=color)
        except Exception:
            pass

    # ── Welcome screen ────────────────────────────────────────────────────────

    def _show_welcome(self):
        tr = self.tr
        self.result_area.config(state=tk.NORMAL)
        title = tr["welcome_title"]
        box_w = max(len(title) + 6, 44)
        top    = "╔" + "═" * (box_w - 2) + "╗\n"
        mid    = "║  " + title.center(box_w - 4) + "  ║\n"
        bot    = "╚" + "═" * (box_w - 2) + "╝\n\n"
        self.result_area.insert(tk.END, top, "header")
        self.result_area.insert(tk.END, mid, "header")
        self.result_area.insert(tk.END, bot, "header")
        self.result_area.insert(tk.END, tr["welcome_enter"],  "dim")
        self.result_area.insert(tk.END, tr["welcome_browse"], "dim")
        self.result_area.insert(tk.END, tr["welcome_examples"], "dim")
        for ex in ["  ·  Anti-Mage\n", "  ·  Phantom Assassin\n",
                   "  ·  Crystal Maiden\n", "  ·  Pudge\n"]:
            self.result_area.insert(tk.END, ex, "hero")
        self.result_area.config(state=tk.DISABLED)

    def _open_patch_notes(self):
        PatchNotesModal(self.root, self.T, self.tr, self._patch_version)

    # ── Hero browser ──────────────────────────────────────────────────────────

    def _open_hero_browser(self):
        HeroBrowserModal(self.root, self.T, self.tr,
                         on_select=self._hero_selected_from_browser)

    def _hero_selected_from_browser(self, hero_name):
        if self._placeholder_active:
            self.hero_entry.delete(0, tk.END)
            self.hero_entry.config(fg=self.T["TEXT_PRIMARY"])
            self._placeholder_active = False
        else:
            self.hero_entry.delete(0, tk.END)
        self.hero_entry.insert(0, hero_name)
        self._suggest.hide()
        self._switch_tab("search")
        self.start_search()

    def _search_hero(self, hero):
        """Подставить героя в поле и искать: подсказка, Enter или список героев."""
        self._placeholder_active = False
        self.hero_entry.config(fg=self.T["TEXT_PRIMARY"])
        self.hero_entry.delete(0, tk.END)
        self.hero_entry.insert(0, hero)
        self.start_search()

    # ── Поиск ─────────────────────────────────────────────────────────────────

    def start_search(self):
        hero = self.hero_entry.get()
        if not hero or self._placeholder_active:
            return
        tr = self.tr
        self.search_btn.config(state=tk.DISABLED, text=tr["btn_searching"])
        self._set_status(tr["status_scanning"], self.T["ACCENT3"])
        self.result_area.config(state=tk.NORMAL)
        self.result_area.delete(1.0, tk.END)
        self.result_area.insert(tk.END, tr["loading_msg"], "loading")
        self.result_area.config(state=tk.DISABLED)
        threading.Thread(target=self._bg_fetch, args=(hero,), daemon=True).start()

    def _bg_fetch(self, hero):
        """Сеть и разбор в фоне; исключение довозим до UI как результат."""
        try:
            outcome = fetch_counters(hero, limit=self._limit)
        except DotabuffError as exc:
            outcome = exc
        except Exception as exc:  # непредвиденное — тоже показываем, не глотаем
            outcome = FetchError(str(exc))
        self.root.after(0, self._apply_result, hero, outcome)

    def _apply_result(self, hero, outcome):
        self.result_area.config(state=tk.NORMAL)
        self.result_area.delete(1.0, tk.END)
        self.hero_images = []
        if isinstance(outcome, DotabuffError):
            self._render_error(hero, outcome)
        else:
            self._render_report(outcome)
        self.result_area.config(state=tk.DISABLED)
        try:
            self.search_btn.config(state=tk.NORMAL, text=self.tr["btn_search"])
        except Exception:
            pass

    def _render_error(self, hero, exc):
        tr = self.tr
        if isinstance(exc, HeroNotFound):
            text = tr["err_not_found"].format(hero=hero.strip())
        elif isinstance(exc, ParseError):
            text = tr["err_layout"].format(detail=exc)
        else:
            text = tr["err_network"].format(detail=exc)
        self.result_area.insert(tk.END, text, "error")
        self._set_status(tr["status_failed"], self.T["ACCENT2"])

    def _render_report(self, report):
        tr = self.tr
        if report.degraded:
            self.result_area.insert(tk.END, tr["warn_degraded"], "wr_bad")

        scraper = create_scraper()
        title = report.hero_slug.upper().replace("-", " ")
        rule = "  " + "─" * 46 + "\n"

        for tag, label, rows in (("bad", tr["bad_against"], report.countered_by),
                                 ("good", tr["good_against"], report.counters)):
            self.result_area.insert(tk.END, rule, "divider")
            self.result_area.insert(tk.END, f"  {title}  ◈  {label}\n", tag)
            self.result_area.insert(tk.END, rule, "divider")
            for m in rows:
                self._insert_icon(scraper, m.icon_url)
                self.result_area.insert(tk.END, f" {m.hero:<21}", "hero")
                self.result_area.insert(tk.END, f"  {m.win_rate}\n", "wr_" + tag)
            self.result_area.insert(tk.END, "\n", "divider")

        self._set_status(tr["status_complete"], self.T["ACCENT"])

    def _insert_icon(self, scraper, url, area=None):
        """Иконка героя перед именем; если не загрузилась — просто отступ.

        area задаётся, потому что вывод есть и у поиска, и у драфта.
        """
        area = area or self.result_area
        if url:
            try:
                data = scraper.get(url, timeout=5).content
                img = Image.open(io.BytesIO(data)).resize(
                    (26, 15), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.hero_images.append(photo)
                area.insert(tk.END, "  ")
                area.image_create(tk.END, image=photo)
                return
            except Exception:
                pass
        area.insert(tk.END, "    ")
