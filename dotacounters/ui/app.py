"""Главное окно: каркас, шапка, вкладки, тема, язык, оверлей, период, портреты.

Сами вкладки — в search_tab, draft_tab, cm_tab, settings_tab: это примеси
к DotaApp, их методы работают с его состоянием через self. updates_tab —
плашка о новой версии и установка обновления.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

from .. import updates
from ..config import cache_dir, load_config, update_config
from ..dotabuff import (DEFAULT_LIMIT, DEFAULT_PERIOD, MAX_LIMIT, PERIODS, DotabuffError,
                        FetchError, fetch_many, period_param)
from ..draft import FILTERS, CaptainsDraft, DraftBoard
from ..heroes import ALL_HEROES, resolve
from ..hotkey import DEFAULT_HOTKEY, GlobalHotkey, format_hotkey, parse_hotkey
from ..i18n import I18N
from ..icons import banned, fetch_icons, load_icon, portrait_url, rounded
from ..net import create_scraper
from ..numbers import short_count
from ..pagecache import PageCache
from ..meta import RANKS, fetch_meta
from ..patches import FALLBACK_PATCH, fetch_current_patch
from ..positions import positions_of
from ..recent import MAX_FAVOURITES, MAX_HISTORY, clean_list, sane_geometry
from ..themes import THEMES, theme_key
from . import dpi
from .cm_tab import CaptainsTab
from .draft_tab import DraftTab
from .evaluation_view import EvaluationView
from .overlay import Overlay
from .patch_notes import PatchNotesModal
from .screen_watch import ScreenWatch
from .search_tab import SearchTab
from .settings_tab import SettingsTab
from .style import make_fonts
from .updates_tab import UpdatesTab
from .widgets import Segmented, button
from .winapi import set_title_bar_color

#: Размер окна по умолчанию и наименьший. Уже 1040 не помещаются шапка и
#: правая колонка Captains Mode с фильтром позиций, ниже 700 — доска из
#: 24 ходов (проверено снимками; в 2.0 минимум был 940×640 и всё это обрезал).
WINDOW = (1040, 720)
MIN_WINDOW = (1040, 700)

TABS = ("search", "draft", "cm", "settings")


class DotaApp(SearchTab, DraftTab, CaptainsTab, EvaluationView, SettingsTab, UpdatesTab,
              ScreenWatch):
    """Главное окно. Состояние общее для вкладок; вкладки — примеси."""

    def __init__(self, root):
        self.root = root
        dpi.install(root)      # пиксели макета -> экранные при 125–200%
        self.root.title("DotaCounters")
        self.root.geometry("%dx%d" % dpi.px_size(WINDOW))
        self.root.resizable(True, True)
        self.root.minsize(*dpi.px_size(MIN_WINDOW))

        cfg = load_config()
        self._theme_key = theme_key(cfg.get("theme"))
        self._lang      = cfg.get("lang", "en") if cfg.get("lang") in I18N else "en"
        self._limit     = self._clamp_limit(cfg.get("limit", DEFAULT_LIMIT))
        # Старые имена из прежних версий («Pango») приводятся к нынешним
        self._history    = clean_list(self._known_names(cfg.get("history")), MAX_HISTORY)
        self._favourites = clean_list(self._known_names(cfg.get("favourites")), MAX_FAVOURITES)
        self.T  = THEMES[self._theme_key]
        self.tr = I18N[self._lang]
        self.F  = make_fonts(root)

        self._patch_version = "…"
        self._active_tab    = "search"
        # Страницы Dotabuff на сутки — в cache/pages рядом с программой
        folder = cache_dir()
        self._pages = PageCache(os.path.join(folder, "pages") if folder else None)
        # Период статистики — один на все вкладки и оверлей, запоминается
        period = cfg.get("period")
        self._period = period if period in PERIODS else DEFAULT_PERIOD
        # Драфты: All Pick — общий со вкладкой и оверлеем; Captains Mode — тоже
        self._board = DraftBoard()
        self._cm    = CaptainsDraft()
        # Фильтры позиции или роли и «под свободные позиции» — запоминаются
        self._board.role = self._known_filter(cfg.get("draft_role"))
        self._cm.role    = self._known_filter(cfg.get("cm_role"))
        self._board.fill = self._cm.fill = cfg.get("fill_positions", True) is not False
        self._cm.rank = cfg.get("meta_rank") if cfg.get("meta_rank") in RANKS else "all"
        self._draft_group   = "enemies"      # куда пойдёт набранный герой
        self._draft_scraper = None           # одна сессия на все запросы драфтов
        self._draft_lock    = threading.Lock()
        self._photos        = {}             # (герой, ширина, высота, вариант) -> PhotoImage
        self._update        = None           # dotacounters.updates.Update, когда есть
        self._update_btn    = None
        self._update_status = None
        self._hotkey_note   = None           # (текст, цвет) после смены клавиши
        self._search_role   = self._known_filter(cfg.get("search_role"))
        self._last_report   = None           # последний найденный отчёт поиска
        self._last_hero     = None
        self._search_token  = 0              # отбросить устаревший ответ поиска
        self._search_state  = ("welcome", None)
        self._draft_view    = "picks"        # «Подбор» или «Оценка драфта» — в Драфте
        self._cm_view       = "picks"        # и в Captains Mode
        updates.cleanup_old()                # хвост от прошлого обновления

        # Оверлей и его клавиша живут всё время работы программы, а не
        # пересобираются вместе с интерфейсом.
        self._hotkey_text = self._hotkey_setting(cfg.get("overlay_hotkey"))
        self._overlay = Overlay(self, position=cfg.get("overlay_pos"))
        self._hotkey = GlobalHotkey(self._hotkey_text,
                                    lambda: self.root.after(0, self._overlay.toggle))
        self._hotkey_ok = self._hotkey.start()
        # Считывание драфта с экрана игры (screen_watch.py)
        self._init_screen(cfg)

        self._apply_theme_styles()
        self._build_ui()
        set_title_bar_color(self.root)

        # Значок в заголовке — у всех окон программы (-default), включая оверлей и
        # модальные. В .exe он лежит во временной папке распаковки (sys._MEIPASS),
        # из исходников — в корне проекта; текущая папка тут ни при чём.
        base = getattr(sys, "_MEIPASS", None) or os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        try:
            self._icon = tk.PhotoImage(file=os.path.join(base, "icon.png"))
            self.root.tk.call("wm", "iconphoto", self.root._w, "-default", self._icon)
        except tk.TclError:
            pass

        self._restore_geometry(cfg.get("window"))
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        threading.Thread(target=self._load_patch, daemon=True).start()
        threading.Thread(target=self._prefetch_portraits, daemon=True).start()
        self._start_update_check()

    # ── Размер и положение окна ───────────────────────────────────────────────

    def _restore_geometry(self, saved):
        """Вернуть окно туда, где его закрыли, если место есть и размер не меньше нового
        минимума: окно прежних версий было 760×860, новый интерфейс в него не влезает."""
        geometry = sane_geometry(saved, self.root.winfo_screenwidth(),
                                 self.root.winfo_screenheight(),
                                 min_width=dpi.px(MIN_WINDOW[0]),
                                 min_height=dpi.px(MIN_WINDOW[1]))
        if geometry:
            self.root.geometry(geometry)

    def _on_close(self):
        """Запомнить геометрию и закрыться."""
        self._hotkey.stop()
        self._watch_on = False
        try:
            if self.root.state() == "normal":   # у развёрнутого окна размер чужой
                update_config(window=self.root.winfo_geometry())
        except Exception:
            pass
        self.root.destroy()

    # ── Стиль ─────────────────────────────────────────────────────────────────

    def _apply_theme_styles(self):
        T = self.T
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=T["BG"])
        # Тонкая полоса без стрелок: только ползунок на фоне. В clam ширину задаёт arrowsize.
        for name in ("Dark.Vertical.TScrollbar", "HB.Vertical.TScrollbar"):
            style.layout(name, [("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
                ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])
            style.configure(name, background=T["LINE"], troughcolor=T["BG"],
                            bordercolor=T["BG"], darkcolor=T["LINE"], lightcolor=T["LINE"],
                            gripcount=0, relief="flat", borderwidth=0, arrowsize=dpi.px(8))
            style.map(name, background=[("active", T["TEXT4"]), ("disabled", T["BG"])],
                      darkcolor=[("active", T["TEXT4"])], lightcolor=[("active", T["TEXT4"])])

    # ── Портреты ──────────────────────────────────────────────────────────────

    def photo(self, hero, size, variant=None):
        """Портрет героя нужного размера как PhotoImage. Кешируется навсегда.

        variant="ban" — серый перечёркнутый. Картинка без ссылки из Python
        исчезает с экрана, поэтому ссылки держит этот словарь. Если портрет
        не скачался — прозрачная заглушка того же размера, раскладка не прыгает.
        """
        key = (hero, size[0], size[1], variant)
        if key in self._photos:
            return self._photos[key]
        url = portrait_url(hero)
        box = dpi.px_size(size)   # портрет рисуется в настоящих пикселях — без размытия
        img = load_icon(url, box=box) if url else None
        if img is None:
            img = Image.new("RGBA", box, (0, 0, 0, 0))
            photo = ImageTk.PhotoImage(img)
            return photo            # заглушку не кешируем — вдруг скачается позже
        if variant == "ban":
            img = banned(img)
        img = rounded(img, dpi.px(3 if size[1] <= 36 else 5))
        photo = ImageTk.PhotoImage(img)
        self._photos[key] = photo
        return photo

    def _prefetch_portraits(self):
        """Скачать портреты всех героев в дисковый кеш — один раз, в фоне.

        Около 6 МБ при первом запуске; дальше все портреты берутся с диска
        мгновенно, и ни один вывод не ждёт сеть.
        """
        urls = [portrait_url(hero) for hero in ALL_HEROES]
        try:
            fetch_icons(urls, box=dpi.px_size((64, 36)), workers=6)
        except Exception:
            pass

    # ── Каркас ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Окно оверлея тоже потомок root, но его пересобирает сам оверлей и с
        # сохранением содержимого — здесь его не трогаем.
        for w in self.root.winfo_children():
            if w is not self._overlay.win:
                w.destroy()
        # Полотна, которые должно прокручивать колесо. Список пересобирается
        # вместе с интерфейсом: прежние виджеты только что уничтожены.
        self._scrollables = []
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.root.bind(seq, self._on_wheel)

        T = self.T
        self.root.configure(bg=T["BG"])
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        self._build_header()
        self._build_update_banner(self.root)

        self._content = tk.Frame(self.root, bg=T["BG"])
        self._content.grid(row=2, column=0, sticky="nsew")
        self._content.columnconfigure(0, weight=1)
        self._content.rowconfigure(0, weight=1)

        self._pages_by_tab = {
            "search": self._build_search_page(),
            "draft": self._build_draft_page(),
            "cm": self._build_cm_page(),
            "settings": self._build_settings_page(),
        }
        self._switch_tab(self._active_tab)

    def _build_header(self):
        T, tr, F = self.T, self.tr, self.F
        bar = tk.Frame(self.root, bg=T["TOPBAR"], height=52)
        bar.grid(row=0, column=0, sticky="ew")
        bar.pack_propagate(False)
        tk.Frame(self.root, bg=T["LINE"], height=1).grid(row=0, column=0, sticky="sew")

        tk.Label(bar, text="DotaCounters", font=F["brand"], fg=T["TEXT"],
                 bg=T["TOPBAR"]).pack(side=tk.LEFT, padx=(20, 0))
        # Номер патча рядом с названием — ссылка на его изменения
        self._patch_btn = button(bar, T, F, self._patch_text(), self._open_patch_notes,
                                 kind="link", font="small", bg=T["TOPBAR"], padx=6)
        self._patch_btn.pack(side=tk.LEFT, padx=(2, 12), pady=(4, 0))

        self._tab_widgets = {}
        for key in TABS:
            cell = tk.Frame(bar, bg=T["TOPBAR"], cursor="hand2")
            cell.pack(side=tk.LEFT, fill=tk.Y)
            label = tk.Label(cell, text=tr["tab_" + key], font=F["tab"], bg=T["TOPBAR"],
                             padx=13, cursor="hand2")
            label.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            line = tk.Frame(cell, height=2, bg=T["TOPBAR"])
            line.pack(side=tk.BOTTOM, fill=tk.X)
            for w in (cell, label):
                w.bind("<Button-1>", lambda e, k=key: self._switch_tab(k))
            label.bind("<Enter>", lambda e, k=key: self._hover_tab(k, True))
            label.bind("<Leave>", lambda e, k=key: self._hover_tab(k, False))
            self._tab_widgets[key] = (label, line)

        # Справа налево: оверлей, период. Клавиша оверлея — в «Настройках» и в
        # подвале оверлея; здесь только предупреждение, если её заняла другая программа.
        right = tk.Frame(bar, bg=T["TOPBAR"])
        right.pack(side=tk.RIGHT, padx=(0, 20))
        if not self._hotkey_ok:
            tk.Label(right, text=tr["ov_key_busy"].format(key=format_hotkey(self._hotkey_text)),
                     font=F["tiny"], bg=T["TOPBAR"], fg=T["BAD"]).pack(side=tk.RIGHT, padx=(6, 0))
        button(right, T, F, tr["ov_btn"], self._overlay_button).pack(side=tk.RIGHT)

        period = tk.Frame(bar, bg=T["TOPBAR"])
        period.pack(side=tk.RIGHT, padx=(0, 16))
        tk.Label(period, text=tr["period_label"], font=F["small"], fg=T["TEXT3"],
                 bg=T["TOPBAR"]).pack(side=tk.LEFT, padx=(0, 8))
        self._period_seg = Segmented(period, T, F, self._period_options(), self._period,
                                     self._set_period, font="small_b", padx=10)
        self._period_seg.pack(side=tk.LEFT)

    def _period_options(self):
        tr = self.tr
        param = period_param("patch", self._pages.patch)
        patch = tr["period_patch_n"].format(patch=param.split("_", 1)[1]) if param \
            else tr["period_patch"]
        return [("week", tr["period_week"]), ("month", tr["period_month"]), ("patch", patch)]

    def _patch_text(self):
        return self._patch_version

    def _hover_tab(self, key, inside):
        if key != self._active_tab:
            label, _ = self._tab_widgets[key]
            label.config(fg=self.T["TEXT"] if inside else self.T["TEXT2"])

    def _switch_tab(self, key):
        T = self.T
        self._active_tab = key
        for k, (label, line) in self._tab_widgets.items():
            on = k == key
            label.config(fg=T["TEXT"] if on else T["TEXT2"])
            line.config(bg=T["GOLD"] if on else T["TOPBAR"])
        for name, page in self._pages_by_tab.items():
            if name == key:
                page.grid(row=0, column=0, sticky="nsew")
            else:
                page.grid_remove()

    def _on_wheel(self, event):
        """Прокрутить полотно, внутри которого оказался курсор.

        Привязка висит на окне, потому что события колеса от вложенных
        виджетов до самого полотна не доходят.
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

    # ── Настройки, общие для вкладок ──────────────────────────────────────────

    @staticmethod
    def _known_names(values):
        if not isinstance(values, list):
            return values
        return [resolve(v) if isinstance(v, str) else v for v in values]

    @staticmethod
    def _known_filter(value):
        """Фильтр позиции или роли из конфига; незнакомый (руками вписанный) — никакого."""
        return value if value in FILTERS else None

    @staticmethod
    def _hotkey_setting(value):
        """Клавиша из конфига, если она разбирается; иначе стандартная."""
        try:
            parse_hotkey(value)
            return value
        except ValueError:
            return DEFAULT_HOTKEY

    @staticmethod
    def _clamp_limit(value):
        """Привести значение к допустимому диапазону 1..MAX_LIMIT."""
        try:
            n = int(value)
        except (TypeError, ValueError):
            n = DEFAULT_LIMIT
        return max(1, min(n, MAX_LIMIT))

    def _overlay_button(self):
        """Кнопка в главном окне: показать или спрятать, без перехвата фокуса."""
        if self._overlay.visible:
            self._overlay.hide()
        else:
            self._overlay.show()

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
        update_config(theme=self._theme_key, lang=self._lang, limit=self._limit)

    def _rebuild(self):
        self._apply_theme_styles()
        self._build_ui()
        set_title_bar_color(self.root)
        self._overlay.restyle()

    # ── Патч ──────────────────────────────────────────────────────────────────

    def _load_patch(self):
        version = fetch_current_patch()
        self._patch_version = version
        if version != FALLBACK_PATCH:
            self._pages.patch = version    # страницы прошлого патча устарели
        self.root.after(0, self._apply_patch, version)

    def _apply_patch(self, version):
        try:
            self._patch_btn.config(text=self._patch_text())
            for key, label in self._period_options():
                self._period_seg.buttons[key].config(text=label)
        except (tk.TclError, AttributeError):
            pass

    def _open_patch_notes(self):
        PatchNotesModal(self.root, self.T, self.tr, self._patch_version, self.F)

    # ── Период статистики ─────────────────────────────────────────────────────

    def _fetch_options(self):
        """Период и патч для запросов к Dotabuff — одни у вкладок и оверлея.

        Патч — только настоящий: запасной номер кеш не выставляет, и тогда
        «весь патч» превращается в месяц (period_param).
        """
        return {"period": self._period, "patch": self._pages.patch}

    def _period_text(self):
        """«за месяц», «за неделю», «за патч 7.41» — для подписей."""
        param = period_param(self._period, self._pages.patch)
        if not param:
            return self.tr["for_month"]
        if param == "week":
            return self.tr["for_week"]
        return self.tr["for_patch"].format(patch=param.split("_", 1)[1])

    def _set_period(self, period):
        """Сменить период: поиск спрашивает героя заново, драфты перекачивают страницы."""
        if period == self._period:
            return
        self._period = period
        update_config(period=period)
        self._period_seg.set(period)
        for model in (self._board, self._cm):
            model.reports.clear()
            model.failed.clear()
        self._draft_changed()
        self._cm_changed()
        if self._last_hero:
            self._search_hero(self._last_hero)

    # ── Страницы для драфтов ──────────────────────────────────────────────────

    def _fetch_for(self, model, retry=False):
        """Докачать страницы, которых не хватает модели драфта (All Pick или CM)."""
        todo = model.missing(retry=retry)
        if not todo:
            return
        model.loading.update(todo)
        threading.Thread(target=self._bg_pages, daemon=True,
                         args=(model, todo, self._fetch_options())).start()

    def _bg_pages(self, model, heroes, options):
        """Одна сессия на все запросы драфтов; по одному потоку за раз."""
        with self._draft_lock:
            if self._draft_scraper is None:
                self._draft_scraper = create_scraper()
            reports, failed = fetch_many(heroes, limit=self._limit, scraper=self._draft_scraper,
                                         cache=self._pages, **options)
        self.root.after(0, self._pages_loaded, model, reports, failed, options)

    def _fetch_meta(self, retry=False):
        """Мета для банов первой фазы Captains Mode — один раз, по требованию.

        Качается той же сессией и под тем же замком, что страницы драфтов;
        из кеша страниц — без сети. Не загрузилась — сама не повторяется.
        """
        cm = self._cm
        if cm.meta is not None or cm.meta_loading or (cm.meta_error and not retry):
            return
        cm.meta_loading, cm.meta_error = True, None

        def work():
            meta, error = None, None
            with self._draft_lock:
                if self._draft_scraper is None:
                    self._draft_scraper = create_scraper()
                try:
                    meta = fetch_meta(self._draft_scraper, cache=self._pages)
                except DotabuffError as exc:
                    error = exc
                except Exception as exc:        # сеть, разбор — всё показать словами
                    error = FetchError(str(exc))
            self.root.after(0, self._meta_loaded, meta, error)
        threading.Thread(target=work, daemon=True).start()

    def _meta_loaded(self, meta, error):
        cm = self._cm
        cm.meta_loading = False
        cm.meta, cm.meta_error = meta, error
        self._cm_changed(fetch=False)

    def _set_meta_rank(self, rank):
        self._cm.rank = rank
        update_config(meta_rank=rank)
        self._cm_changed(fetch=False)

    def _pages_loaded(self, model, reports, failed, options):
        if options != self._fetch_options():
            # Пока качалось, сменили период: эти страницы уже не те. Снять
            # пометку загрузки и докачать за новый период.
            for hero in list(reports) + [hero for hero, _ in failed]:
                model.loading.discard(hero)
            self._fetch_for(model)
            return
        for hero, report in reports.items():
            model.store(hero, report=report)
        for hero, exc in failed:
            model.store(hero, error=exc)
        if model is self._board:
            self._draft_changed(fetch=False)
        else:
            self._cm_changed(fetch=False)

    # ── Подписи ───────────────────────────────────────────────────────────────

    def _count_text(self, matches):
        """«48к» — число матчей коротко, на языке интерфейса."""
        tr = self.tr
        return short_count(matches, tr["count_k"], tr["count_m"], tr["count_decimal"])

    def _age_text(self, seconds):
        """«3 ч», «15 мин» — сколько назад страница скачана."""
        minutes = int(seconds // 60)
        if minutes < 60:
            return self.tr["age_min"].format(n=max(1, minutes))
        return self.tr["age_hours"].format(n=minutes // 60)

    def _signed(self, value):
        """+3,80 / −2,48 — знак настоящим минусом, дробь — по языку."""
        text = "%.2f" % abs(value)
        text = text.replace(".", self.tr["count_decimal"])
        return ("+" if value >= 0 else "−") + text

    # ── Позиции ───────────────────────────────────────────────────────────────

    def _positions_text(self, positions):
        """("pos2", "pos3") -> «Мид · Тройка»."""
        return " · ".join(self.tr["role_" + p] for p in positions)

    def _hero_positions(self, hero):
        """Позиции героя подписью: «Мид · Тройка»."""
        return self._positions_text(positions_of(hero))

    def _fill_line(self, parent, model, wrap=None, theirs=False):
        """Строка над подсказками: под какие свободные позиции они подобраны, и
        ссылка-переключатель «показать всех» / «только свободные». theirs —
        позиции противника (баны Captains Mode), иначе своей команды. Пока
        героев нет или фильтр выбран явно, строки нет. wrap — ширина узкой
        колонки: текст переносится, а ссылка встаёт под ним."""
        T, tr, F = self.T, self.tr, self.F
        needed = model.their_needed() if theirs else model.needed()
        if model.role is not None or not needed:
            return
        line = tk.Frame(parent, bg=T["BG"])
        line.pack(fill=tk.X, pady=(0, 8))
        if model.fill:
            text = (tr["fill_theirs"] if theirs else tr["fill_on"]).format(
                positions=self._positions_text(needed))
            link = tr["fill_all"]
        else:
            text, link = tr["fill_off"], tr["fill_only"]
        side = tk.TOP if wrap else tk.LEFT
        tk.Label(line, text=text, font=F["small"], fg=T["GOLD"] if model.fill else T["TEXT3"],
                 bg=T["BG"], justify=tk.LEFT, wraplength=wrap or 0).pack(side=side, anchor="w")
        button(line, T, F, link, lambda: self._set_fill(not model.fill), kind="link",
               font="small_b").pack(side=side, anchor="w", padx=(0 if wrap else 8, 0))

    def _set_fill(self, on):
        """Подбирать под свободные позиции — общий выключатель обоих драфтов."""
        self._board.fill = self._cm.fill = on
        update_config(fill_positions=on)
        self._draft_changed(fetch=False)
        self._cm_changed(fetch=False)

    def _percent(self, win_rate):
        """«54.29%» со страницы -> «54,3%» по языку."""
        try:
            value = float(str(win_rate).rstrip("%"))
        except ValueError:
            return str(win_rate)
        return ("%.1f%%" % value).replace(".", self.tr["count_decimal"])

    def _copy_text(self, text, status_cb=None):
        """Положить текст в буфер обмена."""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        if status_cb:
            status_cb(self.tr["copied"])
