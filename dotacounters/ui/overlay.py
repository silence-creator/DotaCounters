"""Оверлей: узкое окно поверх игры — контрпики, All Pick и Captains Mode.

Работает, когда Dota запущена в окне или «в окне без рамки». Поверх
полноэкранного исключительного режима Windows чужие окна не показывает.

Окно без рамки: перетаскивается за шапку, Esc прячет. Показывается и
прячется глобальной клавишей (hotkey.py) или кнопкой в главном окне.

Данные общие с главным окном: состав All Pick (app._board), драфт Captains
Mode (app._cm), кеш страниц и период. Страницы драфтов качает главное окно —
оверлей сообщает ему об изменении (_draft_changed / _cm_changed) и получает
refresh(). Поиск контрпиков ходит своей сессией.
"""

import threading
import tkinter as tk

from ..dotabuff import DotabuffError, FetchError, HeroNotFound, ParseError, fetch_counters
from ..draft import CM_ORDER, GROUPS, SIDES
from ..heroes import best_match
from ..hotkey import format_hotkey
from ..recent import sane_position
from .dpi import px
from .suggestions import HeroSuggestions
from .widgets import EntryBox, ScrollArea, Segmented, button, separator
from .winapi import bring_to_front

WIDTH, HEIGHT = 340, 620
ROWS = 6                     # строк в списках оверлея — дальше не влезает


class Overlay:
    """Окно создаётся при первом показе и дальше только прячется."""

    def __init__(self, app, position=None):
        self.app = app
        self.root = app.root
        self._position = position
        self.win = None
        self.mode = "counters"               # counters | draft | cm
        self._counters = None                # (герой, отчёт или ошибка) или None
        self._counters_loading = None
        self._group = "enemies"              # куда пойдёт набранный в All Pick герой
        self._token = 0                      # отбросить устаревший ответ поиска
        # Своя сессия для поиска контрпиков — так Cloudflare реже отбивает
        # запросы. По одному за раз: сессия не рассчитана на несколько потоков.
        self._scraper = None
        self._net_lock = threading.Lock()

    # ── Показ и скрытие ───────────────────────────────────────────────────────

    def _alive(self):
        """Есть ли окно. Уничтоженное извне забываем — при показе соберётся заново."""
        if self.win is not None and not self.win.winfo_exists():
            self.win = None
        return self.win is not None

    @property
    def visible(self):
        return self._alive() and self.win.state() != "withdrawn"

    def _focused(self):
        try:
            widget = self.win.focus_get()
        except (KeyError, tk.TclError):
            return False
        return widget is not None and widget.winfo_toplevel() is self.win

    def toggle(self):
        """Клавиша: показать; если показан, но фокус у игры, — забрать фокус; иначе спрятать."""
        if not self.visible:
            self.show()
        elif not self._focused():
            self._focus()
        else:
            self.hide()

    def show(self):
        if not self._alive():
            self._build()
        self.win.deiconify()
        self.win.lift()
        self.win.attributes("-topmost", True)
        self._focus()

    def hide(self):
        if self._alive():
            self._suggest.hide()
            self.win.withdraw()

    def _focus(self):
        self.win.update_idletasks()
        bring_to_front(self.win)
        self.win.focus_force()
        self.entry.focus_set()

    def restyle(self):
        """Тема, язык или клавиша сменились — пересобрать окно, сохранив содержимое."""
        if not self._alive():
            return
        was_visible = self.visible
        self._position = "+%d+%d" % (self.win.winfo_x(), self.win.winfo_y())
        self.win.destroy()
        self.win = None
        self._build()
        if was_visible:
            self.show()
        else:
            self.win.withdraw()

    def refresh(self):
        """Драфт изменился в главном окне или докачались страницы — перерисовать."""
        if self._alive() and self.mode in ("draft", "cm"):
            self._render()

    # ── Окно ──────────────────────────────────────────────────────────────────

    def _build(self):
        app = self.app
        T, tr, F = app.T, app.tr, app.F
        win = tk.Toplevel(self.root)
        self.win = win
        win.title("DotaCounters Overlay")     # заголовка не видно, но по нему окно находят
        win.overrideredirect(True)            # без рамки и заголовка
        # Непрозрачное: сквозь полупрозрачное окно текст позади ложился прямо
        # на поле ввода и мешал читать.
        win.attributes("-topmost", True)
        win.configure(bg=T["LINE"])           # рамка в 1 пиксель
        win.geometry("%dx%d%s" % (px(WIDTH), px(HEIGHT), self._start_position()))
        win.bind("<Escape>", lambda e: self.hide())

        body = tk.Frame(win, bg=T["BG"])
        body.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self._body = body

        # Шапка — за неё окно и таскают
        head = tk.Frame(body, bg=T["TOPBAR"], cursor="fleur", height=34)
        head.pack(fill=tk.X)
        head.pack_propagate(False)
        title = tk.Label(head, text="DotaCounters", font=F["h2"], fg=T["TEXT"], bg=T["TOPBAR"],
                         cursor="fleur")
        title.pack(side=tk.LEFT, padx=(12, 0))
        button(head, T, F, "×", self.hide, kind="link", font="h2", bg=T["TOPBAR"]).pack(
            side=tk.RIGHT, padx=4)
        for widget in (head, title):
            widget.bind("<ButtonPress-1>", self._drag_start)
            widget.bind("<B1-Motion>", self._drag)
            widget.bind("<ButtonRelease-1>", self._drag_end)
        tk.Frame(body, bg=T["LINE"], height=1).pack(fill=tk.X)

        # Подвал пакуется раньше содержимого: у окна жёсткий размер, и pack при
        # нехватке места урезает то, что упаковано последним.
        tk.Label(body, text=tr["ov_footer"].format(key=format_hotkey(app._hotkey_text)),
                 font=F["tiny"], fg=T["TEXT3"], bg=T["BG"]).pack(side=tk.BOTTOM, pady=(0, 6))

        inner = tk.Frame(body, bg=T["BG"])
        inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=(10, 4))
        self._mode_seg = Segmented(inner, T, F, [("counters", tr["ov_counters"]),
                                                 ("draft", tr["ov_draft"]),
                                                 ("cm", tr["ov_cm"])],
                                   self.mode, self._set_mode, font="small_b", padx=8)
        self._mode_seg.pack(fill=tk.X)

        # Строка управления режимом (группа в All Pick) — контейнер упакован
        # всегда, содержимое меняется: иначе pack поставил бы его в конец.
        self._controls = tk.Frame(inner, bg=T["BG"])
        self._controls.pack(fill=tk.X, pady=(8, 0))

        self._hint = tk.Label(inner, text="", font=F["small"], fg=T["TEXT3"], bg=T["BG"])
        self._hint.pack(anchor="w", pady=(8, 3))
        self._box = EntryBox(inner, T, F, font="body")
        self._box.pack(fill=tk.X)
        self.entry = self._box.entry
        self._suggest = HeroSuggestions(inner, self.entry, T, F["body"], on_accept=self._accept)
        # Esc сперва закрывает подсказки и только потом прячет окно
        self.entry.bind("<Escape>", self._on_escape)
        self.entry.bind("<FocusOut>", lambda e: self._suggest.hide_later(), add="+")
        self._status = tk.Label(inner, text="", font=F["small"], fg=T["TEXT3"], bg=T["BG"],
                                anchor="w", justify=tk.LEFT, wraplength=WIDTH - 40)
        self._status.pack(fill=tk.X, pady=(4, 0))

        self._area = ScrollArea(inner, T, app._scrollables)
        self._area.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        # Колесо мыши в оверлее: у окна своя привязка
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            win.bind(seq, app._on_wheel)
        self._set_mode(self.mode)

    def _start_position(self):
        pos = sane_position(self._position, self.root.winfo_screenwidth(),
                            self.root.winfo_screenheight(), px(WIDTH), px(HEIGHT))
        if pos:
            return pos
        # По умолчанию — справа сверху, где в Dota меньше всего важного
        return "+%d+%d" % (max(0, self.root.winfo_screenwidth() - px(WIDTH + 40)), px(120))

    def _drag_start(self, event):
        self._drag_from = (event.x_root - self.win.winfo_x(), event.y_root - self.win.winfo_y())

    def _drag(self, event):
        dx, dy = self._drag_from
        self.win.geometry("+%d+%d" % (event.x_root - dx, event.y_root - dy))

    def _drag_end(self, event):
        self._position = "+%d+%d" % (self.win.winfo_x(), self.win.winfo_y())
        from ..config import update_config
        update_config(overlay_pos=self._position)

    def _on_escape(self, event):
        if self._suggest.visible:
            self._suggest.hide()
        else:
            self.hide()
        return "break"

    # ── Режимы и ввод ─────────────────────────────────────────────────────────

    def _set_mode(self, mode):
        app = self.app
        T, tr, F = app.T, app.tr, app.F
        self.mode = mode
        self._mode_seg.set(mode)
        for w in self._controls.winfo_children():
            w.destroy()
        if mode == "draft":
            Segmented(self._controls, T, F, [(g, tr["ov_group_" + g]) for g in GROUPS],
                      self._group, self._set_group, font="small_b", padx=9).pack(side=tk.LEFT)
            button(self._controls, T, F, tr["ov_clear"], self._clear, kind="link",
                   font="small_b").pack(side=tk.RIGHT)
        elif mode == "cm":
            button(self._controls, T, F, tr["cm_undo"], self._cm_undo, kind="link",
                   font="small_b").pack(side=tk.LEFT)
            button(self._controls, T, F, tr["cm_reset"], self._cm_reset, kind="link",
                   font="small_b").pack(side=tk.RIGHT)
        else:
            tk.Frame(self._controls, bg=T["BG"], height=1).pack()
        self._status.config(text="")
        self._render()
        if self.visible:
            self.entry.focus_set()

    def _set_group(self, group):
        self._group = group
        self.entry.focus_set()

    def _accept(self, typed):
        hero = best_match(typed)
        self._box.clear()
        if not hero:
            return
        if self.mode == "draft":
            self._add_to_board(hero)
        elif self.mode == "cm":
            self._cm_play(hero)
        else:
            self._search(hero)

    def _set_status(self, text, color=None):
        if self._alive():
            self._status.config(text=text, fg=color or self.app.T["TEXT3"])

    # ── Контрпики ─────────────────────────────────────────────────────────────

    def _fetch(self, hero):
        """Страница героя через свою сессию; ошибка возвращается как результат."""
        app = self.app
        with self._net_lock:
            if self._scraper is None:
                from ..net import create_scraper
                self._scraper = create_scraper()
            try:
                return fetch_counters(hero, scraper=self._scraper, limit=app._limit,
                                      cache=app._pages, **app._fetch_options())
            except DotabuffError as exc:
                return exc
            except Exception as exc:
                return FetchError(str(exc))

    def _search(self, hero):
        self._token += 1
        token = self._token
        self._counters_loading = hero
        self._render()

        def work():
            outcome = self._fetch(hero)
            self.root.after(0, self._searched, token, hero, outcome)
        threading.Thread(target=work, daemon=True).start()

    def _searched(self, token, hero, outcome):
        if token != self._token:
            return  # пока качалось, успели спросить другого героя
        self._counters_loading = None
        self._counters = (hero, outcome)
        if not isinstance(outcome, DotabuffError):
            self.app._remember_hero(hero)
        self._render()

    # ── All Pick ──────────────────────────────────────────────────────────────

    def _add_to_board(self, hero):
        """Герой — в выбранный список общего состава. Страницу докачает главное окно."""
        app = self.app
        tr, T, group = app.tr, app.T, self._group
        outcome = app._board.add(group, hero)
        if outcome == "dup":
            self._set_status(tr["draft_dup"].format(hero=hero))
        elif outcome == "full":
            self._set_status(tr["draft_full_group"].format(max=app._board.limit_of(group)),
                             T["BAD"])
        elif outcome == "moved":
            self._set_status(tr["draft_moved"].format(hero=hero, group=tr["draft_row_" + group]),
                             T["GOLD"])
        else:
            self._set_status("")
        if outcome in ("added", "moved"):
            app._draft_changed()

    def _clear(self):
        self.app._board.clear()
        self._set_status("")
        self.app._draft_changed()

    # ── Captains Mode ─────────────────────────────────────────────────────────

    def _cm_play(self, hero):
        app = self.app
        outcome = app._cm.play(hero)
        if outcome == "taken":
            self._set_status(app.tr["cm_taken"].format(hero=hero), app.T["BAD"])
            return
        if outcome == "done":
            self._set_status(app.tr["cm_done_hint"])
            return
        self._set_status("")
        app._cm_changed()

    def _cm_undo(self):
        hero = self.app._cm.undo()
        self._set_status(self.app.tr["cm_undone"].format(hero=hero) if hero else "")
        self.app._cm_changed(fetch=False)

    def _cm_reset(self):
        self.app._cm.reset()
        self._set_status("")
        self.app._cm_changed(fetch=False)

    # ── Вывод ─────────────────────────────────────────────────────────────────

    def _render(self):
        if not self._alive():
            return
        area = self._area.inner
        for w in area.winfo_children():
            w.destroy()
        if self.mode == "draft":
            self._render_draft(area)
        elif self.mode == "cm":
            self._render_cm(area)
        else:
            self._render_counters(area)
        self._area.to_top()

    def _row(self, parent, hero, value, color):
        app = self.app
        T, F = app.T, app.F
        separator(parent, T)
        row = tk.Frame(parent, bg=T["BG"])
        row.pack(fill=tk.X, pady=4)
        tk.Label(row, image=app.photo(hero, (52, 29)), bg=T["BG"]).pack(side=tk.LEFT)
        tk.Label(row, text=hero, font=F["name"], fg=T["TEXT"], bg=T["BG"]).pack(side=tk.LEFT,
                                                                                padx=(10, 0))
        tk.Label(row, text=app._signed(value), font=F["value"], fg=color, bg=T["BG"]).pack(
            side=tk.RIGHT)

    def _heading(self, parent, text, color=None, caption=""):
        app = self.app
        T, F = app.T, app.F
        head = tk.Frame(parent, bg=T["BG"])
        head.pack(fill=tk.X, pady=(10, 4))
        tk.Label(head, text=text, font=F["h2"], fg=color or T["TEXT"], bg=T["BG"]).pack(
            side=tk.LEFT)
        if caption:
            tk.Label(head, text=caption, font=F["small"], fg=T["TEXT3"], bg=T["BG"]).pack(
                side=tk.RIGHT)

    def _render_counters(self, area):
        app = self.app
        T, tr, F = app.T, app.tr, app.F
        self._hint.config(text=tr["ov_hint_counters"])
        if self._counters_loading:
            self._heading(area, self._counters_loading)
            tk.Label(area, text=tr["loading"], font=F["body"], fg=T["GOLD"], bg=T["BG"]).pack(
                anchor="w")
            return
        if not self._counters:
            return
        hero, outcome = self._counters
        if isinstance(outcome, DotabuffError):
            if isinstance(outcome, HeroNotFound):
                text = tr["ov_not_found"].format(hero=hero)
            elif isinstance(outcome, ParseError):
                text = tr["ov_layout"]
            else:
                text = tr["ov_network"]
            tk.Label(area, text=text, font=F["body"], fg=T["BAD"], bg=T["BG"]).pack(anchor="w")
            return
        for rows, color, title in ((outcome.countered_by, T["BAD"],
                                    tr["weak_against"].format(hero=hero)),
                                   (outcome.counters, T["GOOD"],
                                    tr["strong_against"].format(hero=hero))):
            self._heading(area, title, color)
            for m in rows[:ROWS]:
                self._row(area, m.hero, abs(m.advantage_value or 0), color)

    def _lineup_strip(self, parent, heroes, color, label, ban=False, on_click=None):
        """Строка состава: подпись стороны и мини-портреты; щелчок убирает героя."""
        app = self.app
        T, F = app.T, app.F
        line = tk.Frame(parent, bg=T["TOPBAR"])
        line.pack(fill=tk.X, pady=2)
        tk.Label(line, text=label, font=F["small_b"], fg=color, bg=T["TOPBAR"], width=8,
                 anchor="w").pack(side=tk.LEFT, padx=(6, 0))
        size = (30, 17) if ban else (40, 22)
        for hero in heroes:
            cell = tk.Label(line, image=app.photo(hero, size, "ban" if ban else None),
                            bg=T["TOPBAR"], cursor="hand2" if on_click else "")
            cell.pack(side=tk.LEFT, padx=(0, 3), pady=3)
            if on_click:
                cell.bind("<Button-1>", lambda e, h=hero: on_click(h))

    def _render_draft(self, area):
        app = self.app
        T, tr, F, board = app.T, app.tr, app.F, app._board
        self._hint.config(text=tr["ov_hint_draft"])
        if not any(board.groups.values()):
            tk.Label(area, text=tr["ov_draft_empty"], font=F["body"], fg=T["TEXT3"],
                     bg=T["BG"]).pack(anchor="w")
            return
        box = tk.Frame(area, bg=T["TOPBAR"], highlightthickness=1, highlightbackground=T["LINE"])
        box.pack(fill=tk.X)
        remove = lambda h: (board.remove(h), app._draft_changed())  # noqa: E731
        self._lineup_strip(box, board.groups["enemies"], T["BAD"], tr["ov_group_enemies"],
                           on_click=remove)
        if board.groups["allies"]:
            self._lineup_strip(box, board.groups["allies"], T["GOOD"], tr["ov_group_allies"],
                               on_click=remove)
        if board.groups["bans"]:
            self._lineup_strip(box, board.groups["bans"], T["TEXT2"], tr["ov_group_bans"],
                               ban=True, on_click=remove)
        loading = [h for h in board.enemies if h in board.loading]
        failed = [h for h in board.enemies if h in board.failed]
        if loading:
            tk.Label(area, text=tr["loading"], font=F["small"], fg=T["GOLD"], bg=T["BG"]).pack(
                anchor="w", pady=(6, 0))
        for hero in failed:
            tk.Label(area, text=tr["ov_failed"].format(hero=hero), font=F["small"], fg=T["BAD"],
                     bg=T["BG"]).pack(anchor="w")
        result = board.analyse(limit=min(app._limit, ROWS))
        if result is None:
            return
        if not result.picks:
            tk.Label(area, text=tr["ov_nothing"], font=F["small"], fg=T["BAD"], bg=T["BG"]).pack(
                anchor="w", pady=(6, 0))
            return
        self._heading(area, tr["ov_pick"], T["GOOD"])
        for pick in result.picks:
            self._row(area, pick.hero, pick.total, T["GOOD"])
        self._heading(area, tr["ov_avoid"], T["BAD"])
        for pick in result.avoid:
            self._row(area, pick.hero, pick.total, T["BAD"])

    def _render_cm(self, area):
        app = self.app
        T, tr, F, cm = app.T, app.tr, app.F, app._cm
        index = cm.current
        if index is None:
            self._hint.config(text=tr["cm_done_hint"])
            tk.Label(area, text=tr["cm_done"], font=F["h1"], fg=T["TEXT"], bg=T["BG"]).pack(
                anchor="w")
        else:
            kind = cm.kind(index)
            ours = cm.side(index) == cm.ours
            self._hint.config(text=tr["cm_entry_" + kind].format(n=index + 1))
            head = tk.Frame(area, bg=T["BG"])
            head.pack(fill=tk.X)
            tk.Label(head, text=app._turn_words(index), font=F["h1"],
                     fg=T["GOLD"] if ours else T["TEXT"], bg=T["BG"]).pack(side=tk.LEFT)
            tk.Label(head, text=tr["ov_step"].format(n=index + 1, total=len(CM_ORDER)),
                     font=F["small"], fg=T["TEXT3"], bg=T["BG"]).pack(side=tk.RIGHT, anchor="s")
        box = tk.Frame(area, bg=T["TOPBAR"], highlightthickness=1, highlightbackground=T["LINE"])
        box.pack(fill=tk.X, pady=(8, 0))
        for side in SIDES:
            color = T["RADIANT"] if side == "radiant" else T["DIRE"]
            label = tr["side_" + side].upper()
            self._lineup_strip(box, cm.picks(side), color, label)
            if cm.bans(side):
                self._lineup_strip(box, cm.bans(side), T["TEXT3"], "", ban=True)
        # Подсказки к своему ближайшему ходу, начиная с текущего: бан — кого банить,
        # пик — кого брать. Пока ходят они, заранее видно, что делать дальше.
        ahead = [] if index is None else [i for i in range(index, len(CM_ORDER))
                                          if cm.side(i) == cm.ours]
        our_ban = bool(ahead) and cm.kind(ahead[0]) == "ban"
        limit = min(app._limit, ROWS)
        if our_ban:
            result, title, color = cm.ban_suggestions(limit), tr["cm_ban_title"], T["BAD"]
            heroes = cm.picks(cm.ours)
        else:
            result, title, color = cm.pick_suggestions(limit), tr["cm_pick_title"], T["GOOD"]
            heroes = cm.picks(cm.theirs)
        caption = tr["ov_against"].format(heroes=", ".join(heroes)) if heroes else ""
        self._heading(area, title, color, caption)
        if any(h in cm.loading for h in heroes):
            tk.Label(area, text=tr["loading"], font=F["small"], fg=T["GOLD"], bg=T["BG"]).pack(
                anchor="w")
        if result is None:
            tk.Label(area, text=tr["cm_ban_empty"] if our_ban else tr["cm_pick_empty"],
                     font=F["small"], fg=T["TEXT3"], bg=T["BG"], justify=tk.LEFT,
                     wraplength=WIDTH - 50).pack(anchor="w")
            return
        for pick in result.picks:
            self._row(area, pick.hero, pick.total, color)
