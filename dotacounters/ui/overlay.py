"""Оверлей: узкое окно поверх игры с поиском контрпиков и драфтом.

Работает, когда Dota запущена в окне или «в окне без рамки». Поверх
полноэкранного исключительного режима Windows чужие окна не показывает.

Окно без рамки: перетаскивается за шапку, Esc прячет. Показывается и
прячется глобальной клавишей (hotkey.py) или кнопкой в главном окне.

Состав драфта общий с вкладкой «Драфт» главного окна (draft.DraftBoard):
героя, добавленного здесь, видно там, и наоборот. Страницы врагов качает
главное окно — оверлей только сообщает ему об изменении состава.
"""

import threading
import tkinter as tk
from tkinter import font as tkfont

from PIL import ImageTk

from ..dotabuff import DotabuffError, FetchError, HeroNotFound, ParseError, fetch_counters
from ..draft import GROUPS
from ..heroes import best_match
from ..icons import HERO_ICON_BOX, load_icon
from ..net import create_scraper
from ..recent import sane_position
from .role_menu import role_menu
from .suggestions import HeroSuggestions
from .winapi import bring_to_front

WIDTH, HEIGHT = 340, 600
FONT = "Courier New"


class Overlay:
    """Окно создаётся при первом показе и дальше только прячется."""

    def __init__(self, root, theme, tr, limit, hotkey_label, board,
                 on_draft_change, position=None, on_move=None, on_search=None,
                 pages=None):
        self.root = root
        self.board = board                   # общий состав драфта
        self._pages = pages                  # кеш страниц Dotabuff, общий с главным окном
        self._on_draft_change = on_draft_change  # главное окно докачает и перерисует
        self.T, self.tr = theme, tr
        self._limit = limit                  # функция: сколько строк показывать
        self.hotkey_label = hotkey_label
        self._position = position
        self._on_move = on_move              # сохранить место окна
        self._on_search = on_search          # запомнить героя в недавних
        self.win = None

        self.mode = "counters"               # counters | draft
        self._counters = None                # (герой, отчёт или ошибка) или None
        self._counters_loading = None        # герой, чья страница качается
        self._group = "enemies"              # куда пойдёт набранный в драфте герой
        self._images = []
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
        self.entry.select_range(0, tk.END)

    def restyle(self, theme, tr):
        """Тема или язык сменились — пересобрать окно, сохранив содержимое."""
        self.T, self.tr = theme, tr
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

    # ── Окно ──────────────────────────────────────────────────────────────────

    def _build(self):
        T, tr = self.T, self.tr
        win = tk.Toplevel(self.root)
        self.win = win
        win.title("DotaCounters Overlay")     # заголовка не видно, но по нему окно находят
        win.overrideredirect(True)            # без рамки и заголовка
        # Непрозрачное: сквозь полупрозрачное окно текст позади ложился прямо
        # на поле ввода и мешал читать.
        win.attributes("-topmost", True)
        win.configure(bg=T["ACCENT"])         # тонкая рамка цветом акцента
        win.geometry("%dx%d%s" % (WIDTH, HEIGHT, self._start_position()))
        win.bind("<Escape>", lambda e: self.hide())

        body = tk.Frame(win, bg=T["BG_DARK"])
        body.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self._body = body

        # Шапка — за неё окно и таскают
        head = tk.Frame(body, bg=T["BG_PANEL"], cursor="fleur")
        head.pack(fill=tk.X)
        title = tk.Label(head, text="◈ DOTACOUNTERS", font=(FONT, 9, "bold"),
                         fg=T["ACCENT"], bg=T["BG_PANEL"], cursor="fleur")
        title.pack(side=tk.LEFT, padx=10, pady=6)
        tk.Button(head, text="✕", font=(FONT, 9, "bold"), bg=T["BG_PANEL"], fg=T["TEXT_DIM"],
                  activebackground=T["BG_PANEL"], activeforeground=T["ACCENT2"],
                  relief="flat", bd=0, padx=10, cursor="hand2",
                  command=self.hide).pack(side=tk.RIGHT)
        for widget in (head, title):
            widget.bind("<ButtonPress-1>", self._drag_start)
            widget.bind("<B1-Motion>", self._drag)
            widget.bind("<ButtonRelease-1>", self._drag_end)

        # Режимы
        modes = tk.Frame(body, bg=T["BG_DARK"])
        modes.pack(fill=tk.X, padx=10, pady=(10, 6))
        self._mode_btns = {}
        for key, label in (("counters", tr["ov_counters"]), ("draft", tr["ov_draft"])):
            btn = tk.Button(modes, text=label, font=(FONT, 9, "bold"), relief="flat", bd=0,
                            padx=10, pady=4, cursor="hand2",
                            command=lambda k=key: self._set_mode(k))
            btn.pack(side=tk.LEFT, padx=(0, 6))
            self._mode_btns[key] = btn
        self._clear_btn = tk.Button(modes, text=tr["ov_clear"], font=(FONT, 8, "bold"),
                                    bg=T["BG_DARK"], fg=T["TEXT_DIM"],
                                    activebackground=T["BG_DARK"], activeforeground=T["ACCENT2"],
                                    relief="flat", bd=0, cursor="hand2", command=self._clear)

        # Драфт: куда пойдёт герой и роль. Контейнер упакован всегда, а строка в
        # нём — только в режиме драфта: иначе pack поставил бы её в самый конец.
        box = tk.Frame(body, bg=T["BG_DARK"])
        box.pack(fill=tk.X, padx=10)
        self._draft_row = tk.Frame(box, bg=T["BG_DARK"])
        self._group_btns = {}
        for group in GROUPS:
            btn = tk.Button(self._draft_row, text=tr["ov_group_" + group], font=(FONT, 8, "bold"),
                            relief="flat", bd=0, padx=8, pady=2, cursor="hand2",
                            command=lambda g=group: self._set_group(g))
            btn.pack(side=tk.LEFT, padx=(0, 4))
            self._group_btns[group] = btn
        self._role_menu = role_menu(self._draft_row, T, tr, self.board.role, self._set_role,
                                    font=(FONT, 8, "bold"))
        self._role_menu.pack(side=tk.RIGHT)
        self._set_group(self._group, focus=False)   # поля ввода ещё нет

        self._hint = tk.Label(body, text="", font=(FONT, 8), fg=T["TEXT_DIM"], bg=T["BG_DARK"])
        self._hint.pack(anchor="w", padx=10)

        frame = tk.Frame(body, bg=T["ACCENT"], padx=1, pady=1)
        frame.pack(fill=tk.X, padx=10, pady=(2, 8))
        self.entry = tk.Entry(frame, font=(FONT, 12), bg=T["BG_PANEL"], fg=T["TEXT_PRIMARY"],
                              insertbackground=T["ACCENT"], relief="flat", bd=5,
                              highlightthickness=0)
        self.entry.pack(fill=tk.X)
        self._suggest = HeroSuggestions(body, self.entry, T, (FONT, 11), on_accept=self._accept)
        # Esc сперва закрывает подсказки и только потом прячет окно
        self.entry.bind("<Escape>", self._on_escape)
        self.entry.bind("<FocusOut>", lambda e: self._suggest.hide_later())

        self._status = tk.Label(body, text="", font=(FONT, 8, "bold"), anchor="w",
                                fg=T["TEXT_DIM"], bg=T["BG_DARK"])
        self._status.pack(fill=tk.X, padx=10)

        # Подвал пакуется раньше вывода: у окна жёсткий размер, и pack при
        # нехватке места урезает то, что упаковано последним.
        tk.Label(body, text=tr["ov_footer"].format(key=self.hotkey_label),
                 font=(FONT, 7), fg=T["TEXT_MUTED"], bg=T["BG_DARK"]).pack(
                     side=tk.BOTTOM, pady=(0, 6))

        self.area = tk.Text(body, wrap=tk.WORD, font=(FONT, 10), bg=T["BG_CARD"],
                            fg=T["TEXT_PRIMARY"], relief="flat", bd=0, padx=8, pady=8,
                            spacing2=2, highlightthickness=1, width=1, height=1,
                            highlightbackground=T["BORDER"], cursor="arrow")
        self.area.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 6))
        for tag, colour in (("bad", T["ACCENT2"]), ("good", T["ACCENT"]),
                            ("title", T["ACCENT3"]), ("hero", T["TEXT_PRIMARY"]),
                            ("dim", T["TEXT_DIM"]), ("error", T["ACCENT2"]),
                            ("enemy", T["ACCENT3"])):
            self.area.tag_config(tag, foreground=colour)
        for tag in ("bad", "good", "title"):
            self.area.tag_config(tag, font=(FONT, 10, "bold"))
        self.area.tag_config("enemy", background=T["BG_PANEL"])
        self.area.tag_config("ally", foreground=T["ACCENT"], background=T["BG_PANEL"])
        self.area.tag_config("ban", foreground=T["TEXT_DIM"], background=T["BG_PANEL"],
                             overstrike=True)

        self._set_mode(self.mode)

    def _start_position(self):
        pos = sane_position(self._position, self.root.winfo_screenwidth(),
                            self.root.winfo_screenheight(), WIDTH, HEIGHT)
        if pos:
            return pos
        # По умолчанию — справа сверху, где в Dota меньше всего важного
        return "+%d+%d" % (max(0, self.root.winfo_screenwidth() - WIDTH - 40), 120)

    def _drag_start(self, event):
        self._drag_from = (event.x_root - self.win.winfo_x(), event.y_root - self.win.winfo_y())

    def _drag(self, event):
        dx, dy = self._drag_from
        self.win.geometry("+%d+%d" % (event.x_root - dx, event.y_root - dy))

    def _drag_end(self, event):
        self._position = "+%d+%d" % (self.win.winfo_x(), self.win.winfo_y())
        if self._on_move:
            self._on_move(self._position)

    def _on_escape(self, event):
        if self._suggest.visible:
            self._suggest.hide()
        else:
            self.hide()
        return "break"

    # ── Режимы и ввод ─────────────────────────────────────────────────────────

    def _set_mode(self, mode):
        T = self.T
        self.mode = mode
        for key, btn in self._mode_btns.items():
            active = key == mode
            btn.config(bg=T["ACCENT"] if active else T["BG_PANEL"],
                       fg=T["BG_DARK"] if active else T["TEXT_DIM"],
                       activebackground=T["ACCENT"], activeforeground=T["BG_DARK"])
        if mode == "draft":
            self._clear_btn.pack(side=tk.RIGHT)
            self._draft_row.pack(fill=tk.X, pady=(0, 6))
        else:
            self._clear_btn.pack_forget()
            self._draft_row.pack_forget()
        self._hint.config(text=self.tr["ov_hint_draft" if mode == "draft" else "ov_hint_counters"])
        self._set_status("")
        self._render()
        if self.visible:
            self.entry.focus_set()

    def _accept(self, typed):
        hero = best_match(typed)
        self.entry.delete(0, tk.END)
        if not hero:
            return
        if self.mode == "draft":
            self._add_to_board(hero)
        else:
            self._search(hero)

    def _set_status(self, text, colour=None):
        if self._alive():
            self._status.config(text=text, fg=colour or self.T["TEXT_DIM"])

    def _set_group(self, group, focus=True):
        T = self.T
        self._group = group
        for key, btn in self._group_btns.items():
            active = key == group
            btn.config(bg=T["ACCENT3"] if active else T["BG_PANEL"],
                       fg=T["BG_DARK"] if active else T["TEXT_DIM"],
                       activebackground=T["ACCENT3"], activeforeground=T["BG_DARK"])
        if focus and self.visible:
            self.entry.focus_set()

    def _set_role(self, role):
        self.board.role = role
        self._on_draft_change()

    def _clear(self):
        self.board.clear()
        self._set_status("")
        self._on_draft_change()

    def refresh(self):
        """Состав или загрузка изменились — перерисовать, если окно есть."""
        if self._alive():
            self._role_menu.show_role(self.board.role)
            if self.mode == "draft":
                self._render()

    # ── Сеть ──────────────────────────────────────────────────────────────────

    def _fetch(self, hero):
        """Страница героя через общую сессию; ошибка возвращается как результат."""
        with self._net_lock:
            if self._scraper is None:
                self._scraper = create_scraper()
            try:
                return fetch_counters(hero, scraper=self._scraper, limit=self._limit(),
                                      cache=self._pages)
            except DotabuffError as exc:
                return exc
            except Exception as exc:
                return FetchError(str(exc))

    @staticmethod
    def _warm_icons(rows):
        """Иконки грузятся в фоне, чтобы вывод потом не ждал сеть."""
        for row in rows:
            if row.icon_url:
                load_icon(row.icon_url, box=HERO_ICON_BOX)

    def _search(self, hero):
        self._token += 1
        token = self._token
        self._counters_loading = hero
        self._set_status(self.tr["ov_loading"], self.T["ACCENT3"])
        self._render()

        def work():
            outcome = self._fetch(hero)
            if not isinstance(outcome, DotabuffError):
                self._warm_icons(outcome.countered_by + outcome.counters)
            self.root.after(0, self._searched, token, hero, outcome)
        threading.Thread(target=work, daemon=True).start()

    def _searched(self, token, hero, outcome):
        if token != self._token:
            return  # пока качалось, успели спросить другого героя
        self._counters_loading = None
        self._counters = (hero, outcome)
        self._set_status("")
        if not isinstance(outcome, DotabuffError) and self._on_search:
            self._on_search(hero)
        self._render()

    def _add_to_board(self, hero):
        """Герой — в выбранный список общего состава. Страницу докачает главное окно."""
        tr, T, group = self.tr, self.T, self._group
        outcome = self.board.add(group, hero)
        if outcome == "dup":
            self._set_status(tr["draft_dup"].format(hero=hero))
        elif outcome == "full":
            self._set_status(tr["draft_full_group"].format(max=self.board.limit_of(group)),
                             T["ACCENT2"])
        elif outcome == "moved":
            self._set_status(tr["draft_moved"].format(hero=hero, group=tr["draft_row_" + group]),
                             T["ACCENT3"])
        else:
            self._set_status("")
        if outcome in ("added", "moved"):
            self._on_draft_change()

    def _remove_from_board(self, hero):
        self.board.remove(hero)
        self._on_draft_change()

    # ── Вывод ─────────────────────────────────────────────────────────────────

    def _render(self):
        if not self._alive():
            return
        area = self.area
        area.config(state=tk.NORMAL)
        area.delete("1.0", tk.END)
        self._images = []
        if self.mode == "draft":
            self._render_draft()
        else:
            self._render_counters()
        area.config(state=tk.DISABLED)

    def _row(self, icon_url, hero, value, tag):
        area = self.area
        img = load_icon(icon_url, box=HERO_ICON_BOX) if icon_url else None
        if img is not None:
            photo = ImageTk.PhotoImage(img)
            self._images.append(photo)
            area.image_create(tk.END, image=photo, padx=2)
        else:
            area.insert(tk.END, "    ")
        area.insert(tk.END, " %-18s" % hero[:18], "hero")
        area.insert(tk.END, "%8s\n" % value, tag)

    def _error_text(self, hero, exc):
        tr = self.tr
        if isinstance(exc, HeroNotFound):
            return tr["ov_not_found"].format(hero=hero)
        if isinstance(exc, ParseError):
            return tr["ov_layout"]
        return tr["ov_network"]

    def _render_counters(self):
        area, tr = self.area, self.tr
        if self._counters_loading:
            area.insert(tk.END, self._counters_loading.upper() + "\n", "title")
            area.insert(tk.END, tr["ov_loading"] + "\n", "dim")
            return
        if not self._counters:
            area.insert(tk.END, tr["ov_hint_counters"] + "\n", "dim")
            return
        hero, outcome = self._counters
        if isinstance(outcome, DotabuffError):
            area.insert(tk.END, self._error_text(hero, outcome) + "\n", "error")
            return
        area.insert(tk.END, hero.upper() + "\n", "title")
        for tag, label, rows in (("bad", tr["bad_against"], outcome.countered_by),
                                 ("good", tr["good_against"], outcome.counters)):
            area.insert(tk.END, "\n" + label + "\n", tag)
            for m in rows:
                self._row(m.icon_url, m.hero, m.win_rate, tag)

    def _render_draft(self):
        area, tr, board = self.area, self.tr, self.board
        if not any(board.groups.values()):
            area.insert(tk.END, tr["ov_draft_empty"] + "\n", "dim")
            return

        # Состав — «фишки» в строку: враги, союзники, баны; щелчок убирает героя.
        # Переносим сами, по ширине: поле переносило бы по пробелу внутри имени,
        # и «Crystal Maiden» разваливался на две строки.
        measure = tkfont.Font(font=(FONT, 10)).measure
        room = area.winfo_width() - 24
        if room < 100:
            room = WIDTH - 44          # окно ещё не разложено — берём по размеру
        used, n = 0, 0
        for group, style in (("enemies", "enemy"), ("allies", "ally"), ("bans", "ban")):
            for hero in board.groups[group]:
                tag = "chip_%d" % n
                n += 1
                if hero in board.loading:
                    mark = "⟳"
                elif hero in board.failed:
                    mark = "!"
                else:
                    mark = "✕"
                text = " %s %s " % (mark, hero)
                width = measure(text + " ")
                if used and used + width > room:
                    area.insert(tk.END, "\n")
                    used = 0
                used += width
                area.insert(tk.END, text, (style, tag))
                area.tag_bind(tag, "<Button-1>", lambda e, h=hero: self._remove_from_board(h))
                area.tag_bind(tag, "<Enter>", lambda e: self.area.config(cursor="hand2"))
                area.tag_bind(tag, "<Leave>", lambda e: self.area.config(cursor="arrow"))
                area.insert(tk.END, " ")
        area.insert(tk.END, "\n")

        for hero in board.enemies:
            if hero in board.failed:
                area.insert(tk.END, tr["ov_failed"].format(hero=hero) + "\n", "error")

        result = board.analyse(limit=self._limit())
        if result is None:
            if board.loading:
                area.insert(tk.END, "\n" + tr["ov_loading"] + "\n", "dim")
            return
        if not result.picks:
            area.insert(tk.END, "\n" + tr["ov_nothing"] + "\n", "error")
            return
        for tag, label, rows in (("good", tr["ov_pick"], result.picks),
                                 ("bad", tr["ov_avoid"], result.avoid)):
            area.insert(tk.END, "\n" + label + "\n", tag)
            for pick in rows:
                self._row(pick.icon_url, pick.hero, "%+.2f%%" % pick.total, tag)
        if board.loading:
            area.insert(tk.END, "\n" + tr["ov_loading"] + "\n", "dim")
