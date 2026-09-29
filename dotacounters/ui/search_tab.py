"""Вкладка «Контрпики»: против кого герой слабее и сильнее, избранное и недавние.

Примесь к DotaApp (app.py): методы работают с его состоянием через self.

Состояние вывода — self._search_state: («welcome», None), («loading», герой),
(«error», (герой, ошибка)) или («report», герой); по нему _render_search
перерисовывает карточку героя и две колонки. После смены темы или языка
вкладка собирается заново и показывает то же самое.
"""

import threading
import tkinter as tk

from ..config import update_config
from ..dotabuff import DotabuffError, FetchError, HeroNotFound, ParseError, fetch_counters
from ..draft import ROLE_FILTERS, counters_with_role, has_role
from ..heroes import best_match
from ..icons import fetch_icons, portrait_url
from ..positions import positions_of
from ..recent import is_favourite, remember, toggle_favourite
from .dpi import px_size
from .hero_browser import HeroBrowserModal
from .role_menu import RolePicker
from .suggestions import HeroSuggestions
from .widgets import Bar, EntryBox, ScrollArea, button, chip, separator

EXAMPLES = ("Anti-Mage", "Phantom Assassin", "Crystal Maiden", "Pudge")


class SearchTab:

    def _build_search_page(self):
        T, tr, F = self.T, self.tr, self.F
        page = tk.Frame(self._content, bg=T["BG"])
        self._search_page = page
        page.columnconfigure(0, weight=1)
        page.rowconfigure(3, weight=1)

        # ── Поиск и роль ──
        top = tk.Frame(page, bg=T["BG"])
        top.grid(row=0, column=0, sticky="ew", padx=24, pady=(18, 0))
        left = tk.Frame(top, bg=T["BG"])
        left.pack(side=tk.LEFT, anchor="s")
        tk.Label(left, text=tr["hero_label"], font=F["small"], fg=T["TEXT3"],
                 bg=T["BG"]).pack(anchor="w", pady=(0, 5))
        row = tk.Frame(left, bg=T["BG"])
        row.pack(anchor="w")
        self._search_box = EntryBox(row, T, F, placeholder=tr["hero_placeholder"], width=22)
        self._search_box.pack(side=tk.LEFT, fill=tk.Y)
        self.hero_entry = self._search_box.entry
        button(row, T, F, tr["btn_find"], self.start_search, kind="primary").pack(
            side=tk.LEFT, padx=(8, 0), fill=tk.Y)
        button(row, T, F, tr["btn_all_heroes"], self._open_hero_browser).pack(
            side=tk.LEFT, padx=(8, 0), fill=tk.Y)
        self._suggest = HeroSuggestions(page, self.hero_entry, T, F["input"],
                                        on_accept=self._search_hero,
                                        placeholder_active=lambda: self._search_box.showing_placeholder)
        self.hero_entry.bind("<FocusOut>", lambda e: self._suggest.hide_later(), add="+")

        right = tk.Frame(top, bg=T["BG"])
        right.pack(side=tk.LEFT, anchor="s", padx=(24, 0))
        tk.Label(right, text=tr["enemy_role_label"], font=F["small"], fg=T["TEXT3"],
                 bg=T["BG"]).pack(anchor="w", pady=(0, 5))
        self._role_picker = RolePicker(right, T, F, tr, self._search_role, self._set_search_role)
        self._role_picker.pack(anchor="w")

        # ── Избранное и недавние ──
        self._chips = tk.Frame(page, bg=T["BG"])
        self._chips.grid(row=1, column=0, sticky="ew", padx=24, pady=(10, 0))
        self._render_hero_chips()

        # ── Карточка героя ──
        self._card = tk.Frame(page, bg=T["PANEL"], highlightthickness=1,
                              highlightbackground=T["LINE"])
        self._card.grid(row=2, column=0, sticky="ew", padx=24, pady=(14, 0))

        # ── Колонки ──
        self._results = ScrollArea(page, T, self._scrollables)
        self._results.grid(row=3, column=0, sticky="nsew", padx=(24, 8), pady=(12, 0))

        self._search_foot = tk.Label(page, text="", font=F["small"], fg=T["TEXT3"], bg=T["BG"],
                                     anchor="w", justify=tk.LEFT)
        self._search_foot.grid(row=4, column=0, sticky="ew", padx=24, pady=(6, 12))
        self._render_search()
        return page

    # ── Вывод ─────────────────────────────────────────────────────────────────

    def _render_search(self):
        """Перерисовать карточку и колонки по self._search_state."""
        T = self.T
        for frame in (self._card, self._results.inner):
            for w in frame.winfo_children():
                w.destroy()
        self._search_foot.config(text="")
        kind, payload = self._search_state
        if kind == "welcome":
            self._render_welcome()
        elif kind == "loading":
            self._render_card(payload, status=self.tr["loading"], status_fg=T["GOLD"])
        elif kind == "error":
            hero, exc = payload
            self._render_card(hero, status=self._error_text(hero, exc), status_fg=T["BAD"],
                              known=not isinstance(exc, HeroNotFound))
        else:
            self._render_report(payload, self._last_report)
        self._results.to_top()

    def _render_welcome(self):
        T, tr, F = self.T, self.tr, self.F
        box = tk.Frame(self._card, bg=T["PANEL"])
        box.pack(fill=tk.X, padx=18, pady=16)
        tk.Label(box, text=tr["welcome_title"], font=F["h2"], fg=T["TEXT"],
                 bg=T["PANEL"]).pack(anchor="w")
        tk.Label(box, text=tr["welcome_text"], font=F["body"], fg=T["TEXT2"], bg=T["PANEL"],
                 justify=tk.LEFT).pack(anchor="w", pady=(4, 10))
        row = tk.Frame(box, bg=T["PANEL"])
        row.pack(anchor="w")
        for hero in EXAMPLES:
            chip(row, T, F, hero, lambda h=hero: self._search_hero(h), bg=T["PANEL"]).pack(
                side=tk.LEFT, padx=(0, 6))

    def _render_card(self, hero, status="", status_fg=None, report=None, known=True):
        """Карточка героя: портрет, имя, роли; справа — число игр и свежесть данных."""
        T, tr, F = self.T, self.tr, self.F
        inner = tk.Frame(self._card, bg=T["PANEL"])
        inner.pack(fill=tk.X, padx=16, pady=12)
        if known and portrait_url(hero):
            tk.Label(inner, image=self.photo(hero, (112, 63)), bg=T["PANEL"]).pack(side=tk.LEFT)
        text = tk.Frame(inner, bg=T["PANEL"])
        text.pack(side=tk.LEFT, padx=(16 if known else 0, 0), fill=tk.X, expand=True)
        tk.Label(text, text=hero, font=F["h1"], fg=T["TEXT"], bg=T["PANEL"]).pack(anchor="w")
        # Позиции — светлее, роли Valve за ними — серее: «Тройка · Четвёрка   Инициатор · …»
        line = tk.Frame(text, bg=T["PANEL"])
        line.pack(anchor="w", pady=(2, 0))
        positions = [tr["role_" + p] for p in positions_of(hero)] if known else []
        roles = [tr["role_" + r] for r in ROLE_FILTERS if has_role(hero, r)] if known else []
        if positions:
            tk.Label(line, text=" · ".join(positions), font=F["body_b"], fg=T["TEXT"],
                     bg=T["PANEL"]).pack(side=tk.LEFT, padx=(0, 14))
        if roles:
            tk.Label(line, text=" · ".join(roles), font=F["body"], fg=T["TEXT2"],
                     bg=T["PANEL"]).pack(side=tk.LEFT)
        if status:
            tk.Label(text, text=status, font=F["body"], fg=status_fg or T["TEXT2"], bg=T["PANEL"],
                     justify=tk.LEFT, wraplength=620).pack(anchor="w", pady=(4, 0))
        if report is None:
            return
        side = tk.Frame(inner, bg=T["PANEL"])
        side.pack(side=tk.RIGHT, anchor="e")
        # Каждая игра героя входит в сумму по парам пять раз — по разу на врага
        games = sum(m.matches or 0 for m in report.matchups) // 5
        if games:
            tk.Label(side, text=tr["games_for"].format(games=self._count_text(games),
                                                       period=self._period_text()),
                     font=F["body"], fg=T["TEXT2"], bg=T["PANEL"]).pack(anchor="e")
        fresh = tr["saved_ago"].format(age=self._age_text(report.cached_age)) \
            if report.cached_age is not None else tr["fresh"]
        tk.Label(side, text="%s · %s" % (fresh, self._patch_version), font=F["small"],
                 fg=T["TEXT3"], bg=T["PANEL"]).pack(anchor="e", pady=(2, 6))
        buttons = tk.Frame(side, bg=T["PANEL"])
        buttons.pack(anchor="e")
        fav = is_favourite(self._favourites, hero)
        self._copy_status = tk.Label(buttons, text="", font=F["small"], fg=T["GOLD"],
                                     bg=T["PANEL"])
        self._copy_status.pack(side=tk.LEFT, padx=(0, 8))
        button(buttons, T, F, "★ " + tr["fav_on"] if fav else "☆ " + tr["fav_off"],
               lambda: self._toggle_favourite(hero), kind="link", font="small_b",
               bg=T["PANEL"]).pack(side=tk.LEFT)
        button(buttons, T, F, tr["copy_btn"], self._copy_report, kind="link", font="small_b",
               bg=T["PANEL"]).pack(side=tk.LEFT, padx=(8, 0))

    def _render_report(self, hero, report):
        T, tr, F = self.T, self.tr, self.F
        self._render_card(hero, report=report)
        weak, strong = report.countered_by, report.counters
        warnings = []
        if report.degraded:
            warnings.append(tr["warn_degraded"])
        if self._search_role:
            if report.matchups:
                weak, strong = counters_with_role(report, self._search_role, self._limit)
            else:
                warnings.append(tr["role_no_table"])
        area = self._results.inner
        for text in warnings:
            tk.Label(area, text=text, font=F["body"], fg=T["BAD"], bg=T["BG"], justify=tk.LEFT,
                     anchor="w").pack(fill=tk.X, pady=(0, 8))
        cols = tk.Frame(area, bg=T["BG"])
        cols.pack(fill=tk.BOTH, expand=True)
        cols.columnconfigure((0, 1), weight=1, uniform="col")
        scale = max([4.0] + [abs(m.advantage_value or 0) for m in weak + strong])
        role = (" · " + tr["role_" + self._search_role]) if self._search_role else ""
        for col, (rows, color, title, caption) in enumerate((
                (weak, T["BAD"], tr["weak_against"].format(hero=hero), tr["adv_enemy"]),
                (strong, T["GOOD"], tr["strong_against"].format(hero=hero),
                 tr["adv_hero"].format(hero=hero)))):
            box = tk.Frame(cols, bg=T["BG"])
            box.grid(row=0, column=col, sticky="nsew", padx=(0, 24) if col == 0 else (0, 0))
            head = tk.Frame(box, bg=T["BG"])
            head.pack(fill=tk.X, pady=(0, 6))
            tk.Label(head, text=title, font=F["h2"], fg=color, bg=T["BG"]).pack(side=tk.LEFT)
            tk.Label(head, text=caption + role, font=F["small"], fg=T["TEXT3"],
                     bg=T["BG"]).pack(side=tk.RIGHT)
            if not rows:
                tk.Label(box, text=tr["nothing_here"], font=F["body"], fg=T["TEXT3"],
                         bg=T["BG"]).pack(anchor="w", pady=8)
            for m in rows:
                self._matchup_row(box, hero, m, color, scale)
        self._search_foot.config(text=tr["adv_footnote"])

    def _matchup_row(self, parent, hero, m, color, scale):
        """Строка соперника: портрет, имя, преимущество с полосой, винрейт и матчи."""
        T, tr, F = self.T, self.tr, self.F
        separator(parent, T)
        row = tk.Frame(parent, bg=T["BG"])
        row.pack(fill=tk.X, pady=7)
        tk.Label(row, image=self.photo(m.hero, (64, 36)), bg=T["BG"]).pack(side=tk.LEFT)
        body = tk.Frame(row, bg=T["BG"])
        body.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(12, 0))
        top = tk.Frame(body, bg=T["BG"])
        top.pack(fill=tk.X)
        tk.Label(top, text=m.hero, font=F["name"], fg=T["TEXT"], bg=T["BG"]).pack(side=tk.LEFT)
        value = m.advantage_value or 0.0
        tk.Label(top, text=self._signed(abs(value)), font=F["value"], fg=color,
                 bg=T["BG"]).pack(side=tk.RIGHT)
        Bar(body, T, abs(value) / scale, color).pack(fill=tk.X, pady=(3, 3))
        meta = tr["row_meta"].format(hero=hero, wr=self._percent(m.win_rate),
                                     n=self._count_text(m.matches)) if m.matches else \
            tr["row_meta_wr"].format(hero=hero, wr=self._percent(m.win_rate))
        tk.Label(body, text=meta, font=F["small"], fg=T["TEXT3"], bg=T["BG"]).pack(anchor="w")

    def _error_text(self, hero, exc):
        tr = self.tr
        if isinstance(exc, HeroNotFound):
            return tr["err_not_found"].format(hero=hero.strip())
        if isinstance(exc, ParseError):
            return tr["err_layout"].format(detail=exc)
        return tr["err_network"].format(detail=exc)

    def _copy_report(self):
        """Текст вывода в буфер обмена — как на экране, без картинок."""
        kind, hero = self._search_state
        report = self._last_report
        if kind != "report" or report is None:
            return
        tr = self.tr
        weak, strong = report.countered_by, report.counters
        if self._search_role and report.matchups:
            weak, strong = counters_with_role(report, self._search_role, self._limit)
        lines = []
        for title, rows in ((tr["weak_against"].format(hero=hero), weak),
                            (tr["strong_against"].format(hero=hero), strong)):
            lines.append(title)
            for m in rows:
                lines.append("  %-20s %s  (%s)" % (m.hero, self._signed(abs(m.advantage_value or 0)),
                                                  self._percent(m.win_rate)))
            lines.append("")
        self._copy_text("\n".join(lines).strip(),
                        lambda text: self._copy_status.config(text=text))

    # ── Роль соперников ───────────────────────────────────────────────────────

    def _set_search_role(self, role):
        """Позиция или роль соперников: запомнить и перерисовать последний ответ без сети."""
        self._search_role = role
        update_config(search_role=role)
        picker = getattr(self, "_role_picker", None)
        if picker is not None:
            try:
                picker.set(role)          # выбор мог прийти из оверлея
            except tk.TclError:
                pass
        self._overlay.refresh()
        if self._search_state[0] == "report":
            self._render_search()

    # ── Список героев ─────────────────────────────────────────────────────────

    def _open_hero_browser(self):
        HeroBrowserModal(self.root, self.T, self.tr, on_select=self._hero_selected_from_browser,
                         fonts=self.F)

    def _hero_selected_from_browser(self, hero_name):
        self._switch_tab("search")
        self._search_hero(hero_name)

    # ── Избранное и недавние ──────────────────────────────────────────────────

    def _render_hero_chips(self):
        """Строка с избранными и недавними героями под полем ввода."""
        T, tr, F = self.T, self.tr, self.F
        for w in self._chips.winfo_children():
            w.destroy()
        for label, heroes, fg in ((tr["fav_label"], self._favourites, T["TEXT"]),
                                  (tr["recent_label"], self._history, T["TEXT2"])):
            if not heroes:
                continue
            tk.Label(self._chips, text=label, font=F["small"], fg=T["TEXT3"],
                     bg=T["BG"]).pack(side=tk.LEFT, padx=(0, 8))
            for hero in heroes[:6]:
                chip(self._chips, T, F, hero, lambda h=hero: self._search_hero(h),
                     fg=fg).pack(side=tk.LEFT, padx=(0, 6))
            tk.Frame(self._chips, bg=T["BG"], width=12).pack(side=tk.LEFT)

    def _toggle_favourite(self, hero):
        self._favourites = toggle_favourite(self._favourites, hero)
        update_config(favourites=self._favourites)
        self._render_hero_chips()
        if self._search_state[0] == "report":
            self._render_search()

    def _remember_hero(self, hero):
        self._history = remember(self._history, hero)
        update_config(history=self._history)
        try:
            self._render_hero_chips()
        except tk.TclError:
            pass

    def _search_hero(self, hero):
        """Подставить героя в поле и искать: подсказка, Enter, «фишка» или список героев."""
        self._search_box.set(hero)
        self.start_search()

    # ── Поиск ─────────────────────────────────────────────────────────────────

    def start_search(self):
        typed = self._search_box.get()
        if not typed.strip():
            return
        # «пудж», «бара» и Enter — ищем того героя, которого показывает
        # подсказка, и подставляем его имя в поле
        hero = best_match(typed)
        if hero != typed:
            self._search_box.set(hero)
        self._suggest.hide()
        self._search_state = ("loading", hero)
        self._render_search()
        self._search_token += 1
        threading.Thread(target=self._bg_fetch, daemon=True,
                         args=(hero, self._search_token, self._fetch_options())).start()

    def _bg_fetch(self, hero, token, options):
        """Сеть и разбор в фоне; исключение довозим до UI как результат."""
        try:
            outcome = fetch_counters(hero, limit=self._limit, cache=self._pages, **options)
        except DotabuffError as exc:
            outcome = exc
        except Exception as exc:  # непредвиденное — тоже показываем, не глотаем
            outcome = FetchError(str(exc))
        if not isinstance(outcome, DotabuffError):
            # Портреты — здесь, в фоне: иначе первый показ ждал бы сеть
            heroes = [m.hero for m in outcome.countered_by + outcome.counters]
            if self._search_role and outcome.matchups:
                weak, strong = counters_with_role(outcome, self._search_role, self._limit)
                heroes += [m.hero for m in weak + strong]
            fetch_icons([portrait_url(h) for h in heroes], box=px_size((64, 36)))
            fetch_icons([portrait_url(hero)], box=px_size((112, 63)))
        self.root.after(0, self._apply_result, hero, outcome, token)

    def _apply_result(self, hero, outcome, token=None):
        if token is not None and token != self._search_token:
            return  # пока качалось, спросили другого героя или сменили период
        if isinstance(outcome, DotabuffError):
            self._search_state = ("error", (hero, outcome))
        else:
            self._last_report = outcome        # смена роли перерисует без сети
            self._last_hero = hero             # смена периода спросит его заново
            self._search_state = ("report", hero)
            self._remember_hero(hero)
        try:
            self._render_search()
        except tk.TclError:
            pass                               # вкладку как раз пересобирают
