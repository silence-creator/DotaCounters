import tkinter as tk
from tkinter import ttk
import cloudscraper
from bs4 import BeautifulSoup
import threading
from PIL import Image, ImageTk
import io
import ctypes
import json
import os
import re

# ═══════════════════════════════════════════════════════════════════════════════
# THEMES
# ═══════════════════════════════════════════════════════════════════════════════

THEMES = {
    "cyber": {
        "name_en": "Cyber Dark",
        "name_ru": "Кибер Тёмный",
        "BG_DARK":      "#0a0c10",
        "BG_CARD":      "#0f1318",
        "BG_PANEL":     "#131820",
        "BORDER":       "#1e2a38",
        "ACCENT":       "#00d4ff",
        "ACCENT2":      "#ff3a5c",
        "ACCENT3":      "#ffc94a",
        "TEXT_PRIMARY": "#e8edf5",
        "TEXT_DIM":     "#5a6a80",
        "TEXT_MUTED":   "#2e3d52",
        "SCROLLBAR_BG": "#050708",
        "GLOW":         "#003d4d",
    },
    "blood": {
        "name_en": "Blood Red",
        "name_ru": "Кровавый",
        "BG_DARK":      "#0d0608",
        "BG_CARD":      "#130a0c",
        "BG_PANEL":     "#1a0c0f",
        "BORDER":       "#3a1a20",
        "ACCENT":       "#ff3a5c",
        "ACCENT2":      "#ff8c00",
        "ACCENT3":      "#ffc94a",
        "TEXT_PRIMARY": "#f5e8ea",
        "TEXT_DIM":     "#7a4a52",
        "TEXT_MUTED":   "#3d1e24",
        "SCROLLBAR_BG": "#080304",
        "GLOW":         "#4d0010",
    },
    "matrix": {
        "name_en": "Matrix Green",
        "name_ru": "Матрица",
        "BG_DARK":      "#010d01",
        "BG_CARD":      "#041204",
        "BG_PANEL":     "#061806",
        "BORDER":       "#0f3a0f",
        "ACCENT":       "#00ff41",
        "ACCENT2":      "#39ff14",
        "ACCENT3":      "#7fff00",
        "TEXT_PRIMARY": "#ccffcc",
        "TEXT_DIM":     "#2a6a2a",
        "TEXT_MUTED":   "#0f3a0f",
        "SCROLLBAR_BG": "#010801",
        "GLOW":         "#003300",
    },
    "gold": {
        "name_en": "Ancient Gold",
        "name_ru": "Золото Древних",
        "BG_DARK":      "#0d0a04",
        "BG_CARD":      "#130f06",
        "BG_PANEL":     "#1a1408",
        "BORDER":       "#3a2e10",
        "ACCENT":       "#ffc94a",
        "ACCENT2":      "#ff8c00",
        "ACCENT3":      "#00d4ff",
        "TEXT_PRIMARY": "#f5eecc",
        "TEXT_DIM":     "#7a6a30",
        "TEXT_MUTED":   "#3d3418",
        "SCROLLBAR_BG": "#080600",
        "GLOW":         "#4d3a00",
    },
    "ghost": {
        "name_en": "Ghost White",
        "name_ru": "Призрак",
        "BG_DARK":      "#f0f2f5",
        "BG_CARD":      "#e8eaed",
        "BG_PANEL":     "#dde0e5",
        "BORDER":       "#b0bac8",
        "ACCENT":       "#0066cc",
        "ACCENT2":      "#cc0033",
        "ACCENT3":      "#cc7700",
        "TEXT_PRIMARY": "#0a0c10",
        "TEXT_DIM":     "#5a6a80",
        "TEXT_MUTED":   "#8899aa",
        "SCROLLBAR_BG": "#c8cdd5",
        "GLOW":         "#cce5ff",
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# TRANSLATIONS
# ═══════════════════════════════════════════════════════════════════════════════

I18N = {
    "en": {
        "app_subtitle":      "C O U N T E R  I N T E L L I G E N C E  S Y S T E M  v 1 . 0",
        "tab_search":        "SEARCH",
        "tab_settings":      "SETTINGS",
        "tab_updates":       "UPDATES",
        "hero_name_label":   "HERO NAME",
        "btn_heroes":        "⊞  HEROES",
        "btn_search":        "⟩  SEARCH",
        "btn_searching":     "  SEARCHING…",
        "placeholder":       "e.g.  Pudge",
        "status_await":      "AWAITING INPUT",
        "status_scanning":   "SCANNING NETWORK…",
        "status_complete":   "ANALYSIS COMPLETE",
        "output_header":     "  ANALYSIS OUTPUT",
        "output_source":     "DOTABUFF.COM  ",
        "footer_hint":       "[ ENTER ] search  ·  [ ⊞ HEROES ] browse all heroes  ·  images enabled",
        "welcome_title":     "COUNTER INTELLIGENCE v1.0",
        "welcome_enter":     "  Enter a hero name above to begin analysis.\n",
        "welcome_browse":    "  Or click ⊞ HEROES to browse all heroes.\n\n",
        "welcome_examples":  "  Examples:\n",
        "loading_msg":       "\n  ⟳  Downloading hero profiles...\n",
        "bad_against":       "BAD AGAINST",
        "good_against":      "GOOD AGAINST",
        "no_tables":         "  ✕  No tables found.\n",
        # Hero browser
        "hb_title":          "HERO BROWSER",
        "hb_sorted":         "heroes  ·  sorted A → Z",
        "hb_search_ph":      "  Search hero…",
        "hb_showing":        "Showing",
        "hb_of":             "of",
        "hb_heroes":         "heroes",
        "hb_no_match":       "\n  No heroes match your search.\n",
        # Settings
        "set_title":         "SETTINGS",
        "set_subtitle":      "Customize your experience",
        "set_theme_head":    "THEME",
        "set_theme_sub":     "Select interface color scheme",
        "set_lang_head":     "LANGUAGE  /  ЯЗЫК",
        "set_lang_sub":      "Select interface language",
        "set_lang_en":       "English",
        "set_lang_ru":       "Русский",
        "set_about_head":    "ABOUT",
        "set_ver":           "Version",
        "set_ver_val":       "1.0",
        "set_author":        "Author",
        "set_author_val":    "KIRILL ZALESKIY",
        "set_data":          "Data source",
        "set_data_val":      "dotabuff.com",
        "set_patch":         "Patch API",
        "set_patch_val":     "dota2.com/datafeed",
        "set_built":         "Built with",
        "set_built_val":     "Python · tkinter · cloudscraper · BeautifulSoup",
        "set_desc":          "A lightweight desktop tool for Dota 2 counter-pick analysis.\nParses live data from Dotabuff and displays hero matchup statistics\nfor the current patch.",
        # Updates
        "upd_title":         "UPDATES",
        "upd_subtitle":      "Program update history",
        "upd_text":          "v1.0\nFirst public release. Counter-pick search via Dotabuff with hero icons and win rates, a built-in hero browser with live search, an in-app reader for the current Dota 2 patch notes, five colour themes and an English/Russian interface. Settings persist between sessions.",
    },
    "ru": {
        "app_subtitle":      "С И С Т Е М А  А Н А Л И З А  К О Н Т Е Р П И К О В  v 1 . 0",
        "tab_search":        "ПОИСК",
        "tab_settings":      "НАСТРОЙКИ",
        "tab_updates":       "ОБНОВЛЕНИЯ",
        "hero_name_label":   "ИМЯ ГЕРОЯ",
        "btn_heroes":        "⊞  ГЕРОИ",
        "btn_search":        "⟩  ПОИСК",
        "btn_searching":     "  ПОИСК…",
        "placeholder":       "напр.  Pudge",
        "status_await":      "ОЖИДАНИЕ ВВОДА",
        "status_scanning":   "СКАНИРОВАНИЕ СЕТИ…",
        "status_complete":   "АНАЛИЗ ЗАВЕРШЁН",
        "output_header":     "  ВЫВОД АНАЛИЗА",
        "output_source":     "DOTABUFF.COM  ",
        "footer_hint":       "[ ENTER ] поиск  ·  [ ⊞ ГЕРОИ ] все герои  ·  изображения включены",
        "welcome_title":     "АНАЛИЗ КОНТРПИКОВ v1.0",
        "welcome_enter":     "  Введите имя героя для начала анализа.\n",
        "welcome_browse":    "  Или нажмите ⊞ ГЕРОИ для просмотра списка.\n\n",
        "welcome_examples":  "  Примеры:\n",
        "loading_msg":       "\n  ⟳  Загрузка данных о героях...\n",
        "bad_against":       "СЛАБЕЕ ПРОТИВ",
        "good_against":      "СИЛЬНЕЕ ПРОТИВ",
        "no_tables":         "  ✕  Таблицы не найдены.\n",
        # Hero browser
        "hb_title":          "СПИСОК ГЕРОЕВ",
        "hb_sorted":         "героев  ·  по алфавиту",
        "hb_search_ph":      "  Поиск героя…",
        "hb_showing":        "Показано",
        "hb_of":             "из",
        "hb_heroes":         "героев",
        "hb_no_match":       "\n  Герои не найдены.\n",
        # Settings
        "set_title":         "НАСТРОЙКИ",
        "set_subtitle":      "Персонализация интерфейса",
        "set_theme_head":    "ТЕМА",
        "set_theme_sub":     "Выберите цветовую схему интерфейса",
        "set_lang_head":     "ЯЗЫК  /  LANGUAGE",
        "set_lang_sub":      "Выберите язык интерфейса",
        "set_lang_en":       "English",
        "set_lang_ru":       "Русский",
        "set_about_head":    "О ПРОГРАММЕ",
        "set_ver":           "Версия",
        "set_ver_val":       "1.0",
        "set_author":        "Автор",
        "set_author_val":    "КИРИЛЛ ЗАЛЕСКИЙ",
        "set_data":          "Источник данных",
        "set_data_val":      "dotabuff.com",
        "set_patch":         "API патчей",
        "set_patch_val":     "dota2.com/datafeed",
        "set_built":         "Технологии",
        "set_built_val":     "Python · tkinter · cloudscraper · BeautifulSoup",
        "set_desc":          "Лёгкий десктопный инструмент для анализа контер-пиков в Dota 2.\nПолучает актуальные данные с Dotabuff и отображает статистику\nматчапов для текущего патча.",
        # Updates
        "upd_title":         "ОБНОВЛЕНИЯ",
        "upd_subtitle":      "История обновлений программы",
        "upd_text":          "v1.0\nПервый публичный релиз. Поиск контрпиков через Dotabuff с иконками героев и винрейтами, встроенный список героев с живым поиском, просмотр патчноутов текущего патча Dota 2 прямо в программе, пять цветовых тем и интерфейс на русском и английском. Настройки сохраняются между запусками.",
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG PERSISTENCE
# ═══════════════════════════════════════════════════════════════════════════════

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dota_config.json")

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"theme": "cyber", "lang": "en"}

def save_config(cfg: dict):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# ALL HEROES
# ═══════════════════════════════════════════════════════════════════════════════

ALL_HEROES = sorted([
    "Abaddon", "Alchemist", "Ancient Apparition", "Anti-Mage", "Arc Warden",
    "Axe", "Bane", "Batrider", "Beastmaster", "Bloodseeker",
    "Bounty Hunter", "Brewmaster", "Bristleback", "Broodmother", "Centaur Warrunner",
    "Chaos Knight", "Chen", "Clinkz", "Clockwerk", "Crystal Maiden",
    "Dark Seer", "Dark Willow", "Dawnbreaker", "Dazzle", "Death Prophet",
    "Disruptor", "Doom", "Dragon Knight", "Drow Ranger", "Earth Spirit",
    "Earthshaker", "Elder Titan", "Ember Spirit", "Enchantress", "Enigma",
    "Faceless Void", "Grimstroke", "Gyrocopter", "Hoodwink", "Huskar",
    "Invoker", "Io", "Jakiro", "Juggernaut", "Keeper of the Light",
    "Kez", "Kunkka", "Legion Commander", "Leshrac", "Lich",
    "Lifestealer", "Lina", "Lion", "Lone Druid", "Luna",
    "Lycan", "Magnus", "Marci", "Mars", "Medusa",
    "Meepo", "Mirana", "Monkey King", "Morphling", "Muerta",
    "Naga Siren", "Nature's Prophet", "Necrophos", "Night Stalker", "Nyx Assassin",
    "Ogre Magi", "Omniknight", "Oracle", "Outworld Destroyer", "Pango",
    "Phantom Assassin", "Phantom Lancer", "Phoenix", "Primal Beast", "Puck",
    "Pudge", "Pugna", "Queen of Pain", "Razor", "Riki",
    "Ringmaster", "Rubick", "Sand King", "Shadow Demon", "Shadow Fiend",
    "Shadow Shaman", "Silencer", "Skywrath Mage", "Slardar", "Slark",
    "Snapfire", "Sniper", "Spectre", "Spirit Breaker", "Storm Spirit",
    "Sven", "Techies", "Templar Assassin", "Terrorblade", "Tidehunter",
    "Timbersaw", "Tinker", "Tiny", "Treant Protector", "Troll Warlord",
    "Tusk", "Underlord", "Undying", "Ursa", "Vengeful Spirit",
    "Venomancer", "Viper", "Visage", "Void Spirit", "Warlock",
    "Weaver", "Wind Ranger", "Winter Wyvern", "Witch Doctor", "Wraith King",
    "Zeus",
])

# ═══════════════════════════════════════════════════════════════════════════════
# WINDOWS TITLE BAR
# ═══════════════════════════════════════════════════════════════════════════════

def set_title_bar_color(root):
    try:
        root.update()
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
        get_parent = ctypes.windll.user32.GetParent
        hwnd = get_parent(root.winfo_id())
        value = ctypes.c_int(2)
        set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                             ctypes.byref(value), ctypes.sizeof(value))
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# PATCH FETCH
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_current_patch():
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )
    # Source 1: Valve JSON API
    try:
        url = "https://www.dota2.com/datafeed/patchnoteslist?language=english"
        resp = scraper.get(url, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            patches = data.get("patches") or data.get("patch_notes") or []
            if patches:
                newest = patches[-1]
                number = (
                    newest.get("patch_number")
                    or newest.get("patch_name")
                    or newest.get("version")
                    or ""
                )
                m = re.search(r'7\.\d+[a-z]?', str(number))
                if m:
                    return m.group(0)
    except Exception:
        pass
    # Source 2: Dotabuff page
    try:
        resp = scraper.get(
            "https://www.dotabuff.com/heroes/anti-mage/counters", timeout=10
        )
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup.find_all(string=re.compile(r'(?i)patch')):
                m = re.search(r'7\.\d+[a-z]?', tag)
                if m:
                    return m.group(0)
            m = re.search(r'7\.\d+[a-z]?', resp.text)
            if m:
                return m.group(0)
    except Exception:
        pass
    return "7.41b"


# ═══════════════════════════════════════════════════════════════════════════════
# HERO BROWSER MODAL
# ═══════════════════════════════════════════════════════════════════════════════

class HeroBrowserModal(tk.Toplevel):
    def __init__(self, parent, theme: dict, tr: dict, on_select=None):
        super().__init__(parent)
        self.T = theme
        self.tr = tr
        self.on_select = on_select

        self.title(tr["hb_title"])
        self.configure(bg=self.T["BG_DARK"])
        self.resizable(True, True)
        self.minsize(520, 560)
        self.geometry("620x660")
        self.transient(parent)
        self.grab_set()
        self._center(parent)
        set_title_bar_color(self)
        self._build()
        self.focus_set()

    def _center(self, parent):
        parent.update_idletasks()
        px = parent.winfo_x() + parent.winfo_width() // 2
        py = parent.winfo_y() + parent.winfo_height() // 2
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px - w // 2}+{py - h // 2}")

    def _build(self):
        T, tr = self.T, self.tr
        self.columnconfigure(0, weight=1)

        # Header
        hdr = tk.Frame(self, bg=T["BG_DARK"])
        hdr.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 0))
        tk.Frame(hdr, bg=T["ACCENT"], width=4).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left = tk.Frame(hdr, bg=T["BG_DARK"])
        left.pack(side=tk.LEFT)
        tk.Label(left, text=tr["hb_title"],
                 font=("Courier New", 18, "bold"),
                 fg=T["ACCENT"], bg=T["BG_DARK"]).pack(anchor="w")
        tk.Label(left, text=f"  {len(ALL_HEROES)} {tr['hb_sorted']}",
                 font=("Courier New", 9), fg=T["TEXT_DIM"], bg=T["BG_DARK"]).pack(anchor="w")

        close_btn = tk.Button(hdr, text="✕", font=("Courier New", 12, "bold"),
                              bg=T["BG_DARK"], fg=T["TEXT_DIM"],
                              activebackground=T["BG_DARK"], activeforeground=T["ACCENT2"],
                              relief="flat", bd=0, cursor="hand2", command=self.destroy)
        close_btn.pack(side=tk.RIGHT, padx=(0, 4))
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=T["ACCENT2"]))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=T["TEXT_DIM"]))

        tk.Frame(self, bg=T["BORDER"], height=1).grid(row=1, column=0, sticky="ew", padx=16, pady=(10, 0))

        # Search
        sf = tk.Frame(self, bg=T["BG_DARK"])
        sf.grid(row=2, column=0, sticky="ew", padx=16, pady=(10, 6))
        sf.columnconfigure(0, weight=1)
        eb = tk.Frame(sf, bg=T["BORDER"], padx=1, pady=1)
        eb.grid(row=0, column=0, sticky="ew")
        ei = tk.Frame(eb, bg=T["BG_PANEL"])
        ei.pack(fill=tk.BOTH)
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search)
        self._filter_entry = tk.Entry(ei, textvariable=self._search_var,
                                      font=("Courier New", 11),
                                      bg=T["BG_PANEL"], fg=T["TEXT_PRIMARY"],
                                      insertbackground=T["ACCENT"],
                                      relief="flat", bd=5, highlightthickness=0)
        self._filter_entry.pack(fill=tk.X)
        self._filter_entry.bind("<FocusIn>",  self._search_focus_in)
        self._filter_entry.bind("<FocusOut>", self._search_focus_out)
        self._filter_entry.bind("<Escape>",   lambda e: self.destroy())
        self._search_placeholder = True
        self._set_search_placeholder()

        # List
        lf = tk.Frame(self, bg=T["BG_DARK"])
        lf.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 14))
        self.rowconfigure(3, weight=1)
        lf.columnconfigure(0, weight=1)
        lf.rowconfigure(0, weight=1)
        card = tk.Frame(lf, bg=T["BG_CARD"], highlightbackground=T["BORDER"], highlightthickness=1)
        card.grid(row=0, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure("HB.Vertical.TScrollbar",
                        background=T["SCROLLBAR_BG"], troughcolor=T["SCROLLBAR_BG"],
                        bordercolor=T["SCROLLBAR_BG"], darkcolor=T["SCROLLBAR_BG"],
                        lightcolor=T["SCROLLBAR_BG"], arrowcolor=T["TEXT_DIM"],
                        relief="flat", borderwidth=0)
        style.map("HB.Vertical.TScrollbar",
                  background=[("active", T["BG_PANEL"]), ("disabled", T["SCROLLBAR_BG"])],
                  arrowcolor=[("active", T["ACCENT"])])

        self._canvas = tk.Canvas(card, bg=T["BG_CARD"], bd=0, highlightthickness=0)
        self._canvas.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(card, orient="vertical", style="HB.Vertical.TScrollbar",
                           command=self._canvas.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self._canvas.configure(yscrollcommand=sb.set)
        self._inner = tk.Frame(self._canvas, bg=T["BG_CARD"])
        self._canvas_window = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._inner.bind("<Configure>", lambda e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(
            self._canvas_window, width=e.width))
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self._canvas.bind(seq, self._on_mousewheel)
            self._inner.bind(seq, self._on_mousewheel)

        self._count_label = tk.Label(self, text=f"{tr['hb_showing']} {len(ALL_HEROES)} {tr['hb_heroes']}",
                                     font=("Courier New", 8), fg=T["TEXT_MUTED"], bg=T["BG_DARK"])
        self._count_label.grid(row=4, column=0, sticky="w", padx=18, pady=(0, 6))
        self._render_heroes(ALL_HEROES)

    def _set_search_placeholder(self):
        self._filter_entry.delete(0, tk.END)
        self._filter_entry.insert(0, self.tr["hb_search_ph"])
        self._filter_entry.config(fg=self.T["TEXT_DIM"])
        self._search_placeholder = True

    def _search_focus_in(self, event):
        if self._search_placeholder:
            self._filter_entry.delete(0, tk.END)
            self._filter_entry.config(fg=self.T["TEXT_PRIMARY"])
            self._search_placeholder = False

    def _search_focus_out(self, event):
        if not self._filter_entry.get():
            self._set_search_placeholder()

    def _on_search(self, *args):
        if self._search_placeholder:
            return
        query = self._search_var.get().strip().lower()
        filtered = [h for h in ALL_HEROES if query in h.lower()] if query else ALL_HEROES
        self._render_heroes(filtered)
        tr = self.tr
        self._count_label.config(
            text=f"{tr['hb_showing']} {len(filtered)} {tr['hb_of']} {len(ALL_HEROES)} {tr['hb_heroes']}"
        )

    def _render_heroes(self, heroes):
        T, tr = self.T, self.tr
        for w in self._inner.winfo_children():
            w.destroy()
        if not heroes:
            tk.Label(self._inner, text=tr["hb_no_match"],
                     font=("Courier New", 10), fg=T["TEXT_DIM"],
                     bg=T["BG_CARD"]).pack(anchor="w", padx=14)
            self._canvas.yview_moveto(0)
            return
        groups: dict[str, list[str]] = {}
        for hero in heroes:
            groups.setdefault(hero[0].upper(), []).append(hero)
        COLS = 3
        for letter in sorted(groups.keys()):
            lf = tk.Frame(self._inner, bg=T["BG_CARD"])
            lf.pack(fill=tk.X, padx=10, pady=(10, 2))
            tk.Label(lf, text=f" {letter} ", font=("Courier New", 10, "bold"),
                     fg=T["ACCENT3"], bg=T["BG_PANEL"], padx=6, pady=1).pack(side=tk.LEFT)
            tk.Frame(lf, bg=T["BORDER"], height=1).pack(
                side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0), pady=6)
            gf = tk.Frame(self._inner, bg=T["BG_CARD"])
            gf.pack(fill=tk.X, padx=10, pady=(0, 4))
            for i, hero in enumerate(groups[letter]):
                btn = tk.Button(gf, text=hero, font=("Courier New", 10),
                                bg=T["BG_PANEL"], fg=T["TEXT_PRIMARY"],
                                activebackground=T["GLOW"], activeforeground=T["ACCENT"],
                                relief="flat", bd=0, padx=10, pady=5, anchor="w",
                                cursor="hand2", command=lambda h=hero: self._select_hero(h))
                btn.grid(row=i // COLS, column=i % COLS, sticky="ew", padx=2, pady=1)
                btn.bind("<Enter>", lambda e, b=btn: b.config(fg=T["ACCENT"], bg=T["GLOW"]))
                btn.bind("<Leave>", lambda e, b=btn: b.config(fg=T["TEXT_PRIMARY"], bg=T["BG_PANEL"]))
            for c in range(COLS):
                gf.columnconfigure(c, weight=1, uniform="hcol")
        self._canvas.update_idletasks()
        self._canvas.yview_moveto(0)

    def _select_hero(self, hero_name):
        if self.on_select:
            self.on_select(hero_name)
        self.destroy()

    def _on_mousewheel(self, event):
        if event.num == 4:
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self._canvas.yview_scroll(1, "units")
        else:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

# ═══════════════════════════════════════════════════════════════════════════════
# PATCH NOTES MODAL
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_patch_notes(patch_version: str) -> list[dict]:
    """
    Загружает список изменений патча через Valve JSON API.
    Возвращает формат для вашего GUI: [{"title": str, "notes": [str, ...]}, ...]
    """
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )

    try:
        # Убираем лишние точки, если пользователь ввел "7.35."
        patch_version = patch_version.strip().strip('.')

        # Step 1: Resolve the exact internal version key from the patch list.
        # Valve's patchnotes API uses a specific key (e.g. "7.41b" or "7.41_2")
        # that may differ from the display name. We look it up first.
        resolved_version = patch_version
        try:
            list_url = "https://www.dota2.com/datafeed/patchnoteslist?language=english"
            list_resp = scraper.get(list_url, timeout=10)
            if list_resp.status_code == 200:
                list_data = list_resp.json()
                patches = list_data.get("patches") or list_data.get("patch_notes") or []
                # Build a map of display-name → internal key
                # Each patch entry typically has "patch_number" and optionally a
                # separate "patch_name" or "version" field used as the API key.
                for p in reversed(patches):  # newest first
                    # The internal key used by the /patchnotes endpoint
                    internal_key = (
                        p.get("patch_name")
                        or p.get("version")
                        or p.get("patch_number")
                        or ""
                    )
                    display_name = (
                        p.get("patch_number")
                        or p.get("patch_name")
                        or p.get("version")
                        or ""
                    )
                    # Match either by display name or by internal key
                    m_internal = re.search(r'7\.\d+[a-z]?', str(internal_key))
                    m_display  = re.search(r'7\.\d+[a-z]?', str(display_name))
                    matched_display  = m_display.group(0)  if m_display  else ""
                    matched_internal = m_internal.group(0) if m_internal else ""
                    if matched_display == patch_version or matched_internal == patch_version:
                        resolved_version = str(internal_key).strip()
                        break
                else:
                    # Fallback: try the last patch in the list
                    if patches:
                        last = patches[-1]
                        resolved_version = str(
                            last.get("patch_name")
                            or last.get("version")
                            or last.get("patch_number")
                            or patch_version
                        ).strip()
        except Exception:
            pass  # Keep resolved_version = patch_version if lookup fails

        url = f"https://www.dota2.com/datafeed/patchnotes?version={resolved_version}&language=english"

        resp = scraper.get(url, timeout=12)
        if resp.status_code != 200:
            return []

        data = resp.json()

        # Valve sometimes wraps everything under a "result" or "patch" key
        if not any(k in data for k in ("generic_notes", "items", "heroes")):
            for wrapper_key in ("result", "patch", "data", "notes"):
                if isinstance(data.get(wrapper_key), dict):
                    data = data[wrapper_key]
                    break

        sections = []

        # 1. GENERAL (Это СПИСОК в JSON Valve)
        generic = data.get("generic_notes")
        if isinstance(generic, list) and generic:
            notes = []
            for entry in generic:
                note = entry.get("note") or entry.get("text")
                if note: notes.append(note.strip())
            if notes:
                sections.append({"title": "GENERAL", "notes": notes})

        # 2. ITEMS (Это СЛОВАРЬ в JSON Valve)
        items_data = data.get("items")
        if isinstance(items_data, dict):
            item_notes = []
            for item_key, item_info in items_data.items():
                # Проверяем, что item_info - это словарь, а не список
                if isinstance(item_info, dict):
                    changes = item_info.get("ability_notes") or item_info.get("notes") or []
                    for ch in changes:
                        note = ch.get("note") or ch.get("text")
                        if note:
                            name = item_key.replace('item_', '').replace('_', ' ').upper()
                            item_notes.append(f"{name}: {note.strip()}")
            if item_notes:
                sections.append({"title": "ITEMS", "notes": item_notes})

        # 3. HEROES (Это СЛОВАРЬ в JSON Valve)
        heroes_data = data.get("heroes")
        if isinstance(heroes_data, dict):
            for hero_key, hero_info in heroes_data.items():
                if not isinstance(hero_info, dict): continue
                
                hero_display = hero_key.replace("npc_dota_hero_", "").replace("_", " ").upper()
                current_hero_notes = []

                # Заметки героя
                h_notes = hero_info.get("hero_notes") or []
                for entry in h_notes:
                    note = entry.get("note") or entry.get("text")
                    if note: current_hero_notes.append(note.strip())

                # Способности героя
                abilities = hero_info.get("abilities") or {}
                if isinstance(abilities, dict):
                    for ab_key, ab_info in abilities.items():
                        if not isinstance(ab_info, dict): continue
                        ab_notes = ab_info.get("ability_notes") or []
                        ab_name = ab_key.replace("_", " ").title()
                        for entry in ab_notes:
                            note = entry.get("note") or entry.get("text")
                            if note: current_hero_notes.append(f"[{ab_name}] {note.strip()}")

                if current_hero_notes:
                    sections.append({"title": hero_display, "notes": current_hero_notes})

        return sections

    except Exception as e:
        print(f"Критическая ошибка парсинга: {e}")
        return []


class PatchNotesModal(tk.Toplevel):
    def __init__(self, parent, theme: dict, tr: dict, patch_version: str):
        super().__init__(parent)
        self.T = theme
        self.tr = tr
        self.patch_version = patch_version

        self.title(f"Patch {patch_version} Notes")
        self.configure(bg=theme["BG_DARK"])
        self.resizable(True, True)
        self.minsize(560, 500)
        self.geometry("720x760")
        self.transient(parent)
        self.grab_set()
        self._center(parent)
        set_title_bar_color(self)
        self._build()
        self.focus_set()

        # Запускаем загрузку в фоне
        threading.Thread(target=self._load_notes, daemon=True).start()

    def _center(self, parent):
        parent.update_idletasks()
        px = parent.winfo_x() + parent.winfo_width() // 2
        py = parent.winfo_y() + parent.winfo_height() // 2
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px - w // 2}+{py - h // 2}")

    def _build(self):
        T = self.T
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        # ── Заголовок ─────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=T["BG_DARK"])
        hdr.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 0))
        tk.Frame(hdr, bg=T["ACCENT"], width=4).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left = tk.Frame(hdr, bg=T["BG_DARK"])
        left.pack(side=tk.LEFT)
        tk.Label(left, text=f"PATCH  {self.patch_version}",
                 font=("Courier New", 18, "bold"),
                 fg=T["ACCENT"], bg=T["BG_DARK"]).pack(anchor="w")
        tk.Label(left, text="  dota2.com  ·  patch notes",
                 font=("Courier New", 9), fg=T["TEXT_DIM"], bg=T["BG_DARK"]).pack(anchor="w")

        close_btn = tk.Button(hdr, text="✕", font=("Courier New", 12, "bold"),
                              bg=T["BG_DARK"], fg=T["TEXT_DIM"],
                              activebackground=T["BG_DARK"], activeforeground=T["ACCENT2"],
                              relief="flat", bd=0, cursor="hand2", command=self.destroy)
        close_btn.pack(side=tk.RIGHT, padx=(0, 4))
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=T["ACCENT2"]))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=T["TEXT_DIM"]))

        tk.Frame(self, bg=T["BORDER"], height=1).grid(
            row=1, column=0, sticky="ew", padx=16, pady=(10, 0))

        # ── Поиск по заметкам ─────────────────────────────────────────────────
        sf = tk.Frame(self, bg=T["BG_DARK"])
        sf.grid(row=2, column=0, sticky="ew", padx=16, pady=(10, 6))
        sf.columnconfigure(0, weight=1)
        eb = tk.Frame(sf, bg=T["BORDER"], padx=1, pady=1)
        eb.grid(row=0, column=0, sticky="ew")
        ei = tk.Frame(eb, bg=T["BG_PANEL"])
        ei.pack(fill=tk.BOTH)
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search)
        self._filter_entry = tk.Entry(
            ei, textvariable=self._search_var,
            font=("Courier New", 11),
            bg=T["BG_PANEL"], fg=T["TEXT_PRIMARY"],
            insertbackground=T["ACCENT"],
            relief="flat", bd=5, highlightthickness=0)
        self._filter_entry.pack(fill=tk.X)
        self._filter_entry.bind("<FocusIn>",  self._search_focus_in)
        self._filter_entry.bind("<FocusOut>", self._search_focus_out)
        self._filter_entry.bind("<Escape>",   lambda e: self.destroy())
        self._ph_active = True
        self._set_ph()

        # ── Текстовая область ─────────────────────────────────────────────────
        wrap = tk.Frame(self, bg=T["BG_DARK"])
        wrap.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 0))
        wrap.columnconfigure(1, weight=1)
        wrap.rowconfigure(0, weight=1)

        tk.Frame(wrap, bg=T["ACCENT"], width=2).grid(row=0, column=0, sticky="ns")

        card = tk.Frame(wrap, bg=T["BG_CARD"],
                        highlightbackground=T["BORDER"], highlightthickness=1)
        card.grid(row=0, column=1, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=1)

        tf = tk.Frame(card, bg=T["BG_CARD"])
        tf.grid(row=0, column=0, sticky="nsew")
        tf.columnconfigure(0, weight=1)
        tf.rowconfigure(0, weight=1)

        self._text = tk.Text(
            tf, wrap=tk.WORD, font=("Courier New", 10),
            bg=T["BG_CARD"], fg=T["TEXT_PRIMARY"],
            insertbackground=T["ACCENT"],
            selectbackground=T["GLOW"],
            relief="flat", bd=0, padx=14, pady=10, spacing2=3,
            state=tk.DISABLED)
        self._text.grid(row=0, column=0, sticky="nsew")

        style = ttk.Style()
        style.configure("PN.Vertical.TScrollbar",
                        background=T["SCROLLBAR_BG"], troughcolor=T["SCROLLBAR_BG"],
                        bordercolor=T["SCROLLBAR_BG"], darkcolor=T["SCROLLBAR_BG"],
                        lightcolor=T["SCROLLBAR_BG"], arrowcolor=T["TEXT_DIM"],
                        relief="flat", borderwidth=0)
        style.map("PN.Vertical.TScrollbar",
                  background=[("active", T["BG_PANEL"]), ("disabled", T["SCROLLBAR_BG"])],
                  arrowcolor=[("active", T["ACCENT"])])

        sb = ttk.Scrollbar(tf, orient="vertical", style="PN.Vertical.TScrollbar",
                           command=self._text.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self._text.config(yscrollcommand=sb.set)
        self._text.bind("<MouseWheel>", lambda e: None)

        # Теги
        self._text.tag_config("section", foreground=T["ACCENT3"],
                               font=("Courier New", 10, "bold"))
        self._text.tag_config("divider", foreground=T["TEXT_MUTED"])
        self._text.tag_config("note",    foreground=T["TEXT_PRIMARY"])
        self._text.tag_config("loading", foreground=T["ACCENT3"])
        self._text.tag_config("error",   foreground=T["ACCENT2"],
                               font=("Courier New", 10, "bold"))
        self._text.tag_config("match",   foreground=T["ACCENT"],
                               font=("Courier New", 10, "bold"))

        # ── Статус-бар ────────────────────────────────────────────────────────
        self._status_lbl = tk.Label(
            self, text="", font=("Courier New", 8),
            fg=T["TEXT_MUTED"], bg=T["BG_DARK"])
        self._status_lbl.grid(row=4, column=0, sticky="w", padx=18, pady=(4, 8))

        # Показываем загрузку
        self._write_loading()

        # Храним все секции для фильтрации
        self._all_sections: list[dict] = []

    # ── Placeholder ───────────────────────────────────────────────────────────

    def _set_ph(self):
        ph = "  Filter by hero or item…" if self.tr.get("lang") != "ru" else "  Фильтр по герою или предмету…"
        self._filter_entry.delete(0, tk.END)
        self._filter_entry.insert(0, ph)
        self._filter_entry.config(fg=self.T["TEXT_DIM"])
        self._ph_active = True

    def _search_focus_in(self, event):
        if self._ph_active:
            self._filter_entry.delete(0, tk.END)
            self._filter_entry.config(fg=self.T["TEXT_PRIMARY"])
            self._ph_active = False

    def _search_focus_out(self, event):
        if not self._filter_entry.get():
            self._set_ph()

    # ── Загрузка ──────────────────────────────────────────────────────────────

    def _write_loading(self):
        self._text.config(state=tk.NORMAL)
        self._text.delete(1.0, tk.END)
        self._text.insert(tk.END, f"\n  ⟳  Loading patch {self.patch_version} notes...\n", "loading")
        self._text.config(state=tk.DISABLED)

    def _load_notes(self):
        sections = fetch_patch_notes(self.patch_version)
        self.after(0, self._apply_notes, sections)

    def _apply_notes(self, sections: list[dict]):
        self._all_sections = sections
        self._render_sections(sections)

    # ── Рендер ───────────────────────────────────────────────────────────────

    def _render_sections(self, sections: list[dict], query: str = ""):
        T = self.T
        txt = self._text
        txt.config(state=tk.NORMAL)
        txt.delete(1.0, tk.END)

        if not sections:
            txt.insert(tk.END, "\n  ✕  No patch notes available.\n", "error")
            txt.insert(tk.END, f"\n  Patch {self.patch_version} data may not yet be published.\n", "note")
            self._status_lbl.config(text="0 sections")
            txt.config(state=tk.DISABLED)
            return

        total_notes = 0
        for sec in sections:
            # Заголовок секции
            txt.insert(tk.END, "  " + "─" * 50 + "\n", "divider")
            txt.insert(tk.END, f"  ◈  {sec['title']}\n", "section")
            txt.insert(tk.END, "  " + "─" * 50 + "\n", "divider")
            for note in sec["notes"]:
                line = f"  ·  {note}\n"
                if query and query.lower() in note.lower():
                    txt.insert(tk.END, line, "match")
                else:
                    txt.insert(tk.END, line, "note")
                total_notes += 1
            txt.insert(tk.END, "\n")

        self._status_lbl.config(
            text=f"{len(sections)} sections  ·  {total_notes} changes"
        )
        txt.config(state=tk.DISABLED)
        txt.yview_moveto(0)

    # ── Фильтр ────────────────────────────────────────────────────────────────

    def _on_search(self, *args):
        if self._ph_active or not self._all_sections:
            return
        query = self._search_var.get().strip()
        if not query:
            self._render_sections(self._all_sections)
            return
        filtered = []
        for sec in self._all_sections:
            matching = [n for n in sec["notes"] if query.lower() in n.lower()]
            # Также показываем секцию целиком если query совпадает с названием
            if query.lower() in sec["title"].lower():
                filtered.append(sec)
            elif matching:
                filtered.append({"title": sec["title"], "notes": matching})
        self._render_sections(filtered, query=query)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════

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
        self.T          = THEMES[self._theme_key]
        self.tr         = I18N[self._lang]

        self.hero_images       = []
        self._placeholder_active = False
        self._patch_version    = "…"
        self._active_tab       = "search"   # "search" | "settings" | "updates"

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

        T = self.T
        self.root.configure(bg=T["BG_DARK"])
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        outer = tk.Frame(self.root, bg=T["BG_DARK"])
        outer.grid(row=0, column=0, sticky="nsew", padx=16, pady=12)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(3, weight=1)

        self._build_header(outer)
        self._build_tab_bar(outer)
        tk.Frame(outer, bg=T["BORDER"], height=1).grid(row=2, column=0, sticky="ew", pady=(0, 10))

        # Content frame — swapped by tabs
        self._content = tk.Frame(outer, bg=T["BG_DARK"])
        self._content.grid(row=3, column=0, sticky="nsew")
        self._content.columnconfigure(0, weight=1)
        self._content.rowconfigure(0, weight=1)

        self._build_search_page()
        self._build_settings_page()
        self._build_updates_page()
        self._build_footer(outer)

        self._switch_tab(self._active_tab, rebuild=False)

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
        tabs = [("search", tr["tab_search"]), ("settings", tr["tab_settings"]), ("updates", tr["tab_updates"])]
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
        # Show/hide pages
        if key == "search":
            self._search_page.grid(row=0, column=0, sticky="nsew")
            self._settings_page.grid_remove()
            self._updates_page.grid_remove()
        elif key == "settings":
            self._settings_page.grid(row=0, column=0, sticky="nsew")
            self._search_page.grid_remove()
            self._updates_page.grid_remove()
        else:
            self._updates_page.grid(row=0, column=0, sticky="nsew")
            self._search_page.grid_remove()
            self._settings_page.grid_remove()

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
        self.hero_entry.bind("<Return>", lambda e: self.start_search())
        self.hero_entry.bind("<FocusIn>",  self._on_entry_focus)
        self.hero_entry.bind("<FocusOut>", self._on_entry_blur)
        self._show_placeholder()

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
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            canvas.bind(seq, lambda e, c=canvas: c.yview_scroll(
                -1 if e.num == 4 else (1 if e.num == 5 else int(-1 * e.delta / 120)), "units"))

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
        for r, (label, val) in enumerate(rows_info):
            tk.Label(about_card, text=f"  {label}", font=("Courier New", 9, "bold"),
                     fg=T["TEXT_DIM"], bg=T["BG_CARD"],
                     pady=5).grid(row=r, column=0, sticky="w")
            tk.Label(about_card, text=val, font=("Courier New", 9),
                     fg=T["TEXT_PRIMARY"], bg=T["BG_CARD"],
                     pady=5).grid(row=r, column=1, sticky="w", padx=(10, 14))
            if r < len(rows_info) - 1:
                tk.Frame(about_card, bg=T["BORDER"], height=1).grid(
                    row=r, column=0, columnspan=2, sticky="ew", pady=0)

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
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            canvas.bind(seq, lambda e, c=canvas: c.yview_scroll(
                -1 if e.num == 4 else (1 if e.num == 5 else int(-1 * e.delta / 120)), "units"))

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
        text.insert(tk.END, tr["upd_text"])
        text.config(state=tk.DISABLED)

    def _add_section_header(self, parent, row, title, subtitle):
        T = self.T
        f = tk.Frame(parent, bg=T["BG_DARK"])
        f.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 8))
        tk.Label(f, text=title, font=("Courier New", 10, "bold"),
                 fg=T["ACCENT3"], bg=T["BG_DARK"]).pack(side=tk.LEFT)
        if subtitle:
            tk.Label(f, text=f"  —  {subtitle}", font=("Courier New", 9),
                     fg=T["TEXT_MUTED"], bg=T["BG_DARK"]).pack(side=tk.LEFT)
        tk.Frame(parent, bg=T["BORDER"], height=1).grid(
            row=row, column=0, sticky="ew", padx=20, pady=(0, 10))

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

    def _save_prefs(self):
        save_config({"theme": self._theme_key, "lang": self._lang})

    def _rebuild(self):
        self._apply_theme_styles()
        self._build_ui()
        set_title_bar_color(self.root)

    # ── Footer ────────────────────────────────────────────────────────────────

    def _build_footer(self, parent):
        T, tr = self.T, self.tr
        ft = tk.Frame(parent, bg=T["BG_DARK"])
        ft.grid(row=4, column=0, sticky="ew", pady=(6, 0))
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
        self._switch_tab("search")
        self.start_search()

    # ── Scraper ───────────────────────────────────────────────────────────────

    def get_random_scraper(self):
        return cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )

    def fetch_data(self, hero_name):
        hero_slug = hero_name.strip().lower().replace(" ", "-").replace("'", "")
        url = f"https://www.dotabuff.com/heroes/{hero_slug}/counters"
        scraper = self.get_random_scraper()
        try:
            response = scraper.get(url, timeout=10)
            if response.status_code == 200:
                return self.parse_html(response.text, hero_slug)
            return [("error", f"  ✕  HTTP {response.status_code}\n")]
        except Exception as e:
            return [("error", f"  ✕  Error: {str(e)}\n")]

    def parse_html(self, html, hero_slug):
        tr = self.tr
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")
        output = []
        if not tables:
            return [("error", tr["no_tables"])]
        labels = [tr["bad_against"], tr["good_against"]]
        tags   = ["bad", "good"]
        for i, table in enumerate(tables[:2]):
            output.append(("divider", "  " + "─" * 46 + "\n"))
            output.append((tags[i], f"  {hero_slug.upper().replace('-', ' ')}  ◈  {labels[i]}\n"))
            output.append(("divider", "  " + "─" * 46 + "\n"))
            rows = table.find("tbody").find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 4:
                    img_tag  = cols[0].find("img")
                    img_path = img_tag.get("src") if img_tag else None
                    full_url = f"https://www.dotabuff.com{img_path}" if img_path else None
                    name     = cols[1].get_text(strip=True)
                    winrate  = cols[3].get_text(strip=True)
                    output.append(("image", full_url))
                    output.append(("hero",  f" {name:<21}"))
                    output.append(("wr_" + tags[i], f"  {winrate}\n"))
            output.append(("divider", "\n"))
        return output

    # ── Search handler ────────────────────────────────────────────────────────

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
        result = self.fetch_data(hero)
        self.root.after(0, self._apply_result, result)

    def _apply_result(self, result):
        tr = self.tr
        self.result_area.config(state=tk.NORMAL)
        self.result_area.delete(1.0, tk.END)
        self.hero_images = []
        scraper = self.get_random_scraper()
        if isinstance(result, list):
            for tag, data in result:
                if tag == "image":
                    if data:
                        try:
                            img_data = scraper.get(data, timeout=5).content
                            img = Image.open(io.BytesIO(img_data)).resize(
                                (26, 15), Image.Resampling.LANCZOS)
                            photo = ImageTk.PhotoImage(img)
                            self.hero_images.append(photo)
                            self.result_area.insert(tk.END, "  ")
                            self.result_area.image_create(tk.END, image=photo)
                        except Exception:
                            self.result_area.insert(tk.END, "    ")
                    else:
                        self.result_area.insert(tk.END, "    ")
                else:
                    self.result_area.insert(tk.END, data, tag)
            self._set_status(tr["status_complete"], self.T["ACCENT"])
        self.result_area.config(state=tk.DISABLED)
        try:
            self.search_btn.config(state=tk.NORMAL, text=tr["btn_search"])
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    app = DotaApp(root)
    root.mainloop()