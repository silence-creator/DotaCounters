"""Вкладка Captains Mode: доска 24 ходов и подсказки к текущему ходу.

Примесь к DotaApp (app.py): методы работают с его состоянием через self.
Модель — self._cm (draft.CaptainsDraft), общая с оверлеем. Страницы пиков
качает главное окно (_fetch_for) сразу, как пик записан.

Доска устроена как в игре: слева Radiant, справа Dire, в середине номера
ходов; мелкие клетки — баны, крупные — пики. Чей ход с каким номером —
зависит от того, кто начинает (CM_BOARD хранит «первого» и «второго»).
"""

import tkinter as tk

from ..config import update_config
from ..draft import CM_BOARD, CM_ORDER, SIDES
from ..heroes import best_match
from ..meta import MIN_PICK, RANKS
from .hero_browser import HeroBrowserModal
from .role_menu import RolePicker
from .suggestions import HeroSuggestions
from .widgets import EntryBox, ScrollArea, Segmented, button, separator

#: Клетки доски. Все 24 хода должны влезть в окно наименьшей высоты без прокрутки.
BAN_SIZE, PICK_SIZE = (52, 29), (88, 50)
#: Перенос строк в колонках подсказок. Колонка банов в окне 1040 — около 270
#: пикселей: подпись шире колонки обрезалась слева (проверено снимком).
HINT_WRAP = 250


class CaptainsTab:

    def _build_cm_page(self):
        T, tr, F = self.T, self.tr, self.F
        page = tk.Frame(self._content, bg=T["BG"])
        self._cm_page = page
        page.columnconfigure(1, weight=1)
        page.rowconfigure(0, weight=1)

        self._cm_board_frame = tk.Frame(page, bg=T["TOPBAR"], highlightthickness=1,
                                        highlightbackground=T["LINE"])
        self._cm_board_frame.grid(row=0, column=0, sticky="nw", padx=(24, 0), pady=(18, 12))

        right = tk.Frame(page, bg=T["BG"])
        right.grid(row=0, column=1, sticky="nsew", padx=(28, 8), pady=(18, 12))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(3, weight=1)

        head = tk.Frame(right, bg=T["BG"])
        head.grid(row=0, column=0, sticky="ew", padx=(0, 16))
        self._cm_turn = tk.Frame(head, bg=T["BG"])
        self._cm_turn.pack(side=tk.LEFT, anchor="n")
        sides = tk.Frame(head, bg=T["BG"])
        sides.pack(side=tk.RIGHT, anchor="n")
        for label, value, handler, attr in ((tr["cm_we_play"], self._cm.ours, self._set_cm_ours,
                                             "_cm_ours_seg"),
                                            (tr["cm_first"], self._cm.first, self._set_cm_first,
                                             "_cm_first_seg")):
            line = tk.Frame(sides, bg=T["BG"])
            line.pack(anchor="e", pady=(0, 6))
            tk.Label(line, text=label, font=F["small"], fg=T["TEXT3"], bg=T["BG"]).pack(
                side=tk.LEFT, padx=(0, 8))
            seg = Segmented(line, T, F, [(s, tr["side_" + s]) for s in SIDES], value, handler,
                            font="small_b", padx=10)
            seg.pack(side=tk.LEFT)
            setattr(self, attr, seg)

        entry_row = tk.Frame(right, bg=T["BG"])
        entry_row.grid(row=1, column=0, sticky="ew", pady=(12, 0), padx=(0, 16))
        self._cm_entry_label = tk.Label(entry_row, text="", font=F["small"], fg=T["TEXT3"],
                                        bg=T["BG"])
        self._cm_entry_label.pack(anchor="w", pady=(0, 5))
        line = tk.Frame(entry_row, bg=T["BG"])
        line.pack(fill=tk.X)
        self._cm_box = EntryBox(line, T, F, placeholder=tr["name_placeholder"])
        self._cm_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._cm_suggest = HeroSuggestions(right, self._cm_box.entry, T, F["input"],
                                           on_accept=self._cm_play,
                                           placeholder_active=lambda: self._cm_box.showing_placeholder)
        self._cm_box.entry.bind("<FocusOut>", lambda e: self._cm_suggest.hide_later(), add="+")
        button(line, T, F, "⊞", lambda: HeroBrowserModal(
            self.root, T, tr, on_select=self._cm_play, fonts=F), font="body_b").pack(
                side=tk.LEFT, padx=(8, 0), fill=tk.Y)
        button(line, T, F, tr["cm_undo"], self._cm_undo).pack(side=tk.LEFT, padx=(8, 0), fill=tk.Y)
        button(line, T, F, tr["cm_reset"], self._cm_reset, kind="link").pack(side=tk.LEFT,
                                                                             padx=(8, 0))
        self._cm_message = tk.Label(entry_row, text="", font=F["small"], fg=T["TEXT3"], bg=T["BG"])
        self._cm_message.pack(anchor="w", pady=(4, 0))

        roles = tk.Frame(right, bg=T["BG"])
        roles.grid(row=2, column=0, sticky="ew", pady=(4, 0))
        tk.Label(roles, text=tr["role_label"], font=F["small"], fg=T["TEXT3"], bg=T["BG"]).pack(
            side=tk.LEFT, padx=(0, 8))
        self._cm_roles = RolePicker(roles, T, F, tr, self._cm.role, self._set_cm_role)
        self._cm_roles.pack(side=tk.LEFT)

        self._cm_hints = ScrollArea(right, T, self._scrollables)
        self._cm_hints.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        self._cm_foot = tk.Label(right, text=tr["cm_footnote"], font=F["small"], fg=T["TEXT3"],
                                 bg=T["BG"], anchor="w", justify=tk.LEFT, wraplength=620)
        self._cm_foot.grid(row=4, column=0, sticky="ew", pady=(6, 0))

        self._render_cm()
        return page

    # ── Доска ─────────────────────────────────────────────────────────────────

    def _render_cm(self):
        self._render_cm_board()
        self._render_cm_turn()
        self._render_cm_hints()

    def _render_cm_board(self):
        T, tr, F, cm = self.T, self.tr, self.F, self._cm
        board = self._cm_board_frame
        for w in board.winfo_children():
            w.destroy()
        inner = tk.Frame(board, bg=T["TOPBAR"])
        inner.pack(padx=14, pady=10)
        inner.columnconfigure(0, minsize=132)
        inner.columnconfigure(2, minsize=132)
        current = cm.current
        # Шапка: стороны и счётчик ходов
        for col, side in ((0, "radiant"), (2, "dire")):
            text = tr["side_" + side].upper() + (tr["cm_you"] if side == cm.ours else "")
            tk.Label(inner, text=text, font=F["h2"], bg=T["TOPBAR"],
                     fg=T["RADIANT"] if side == "radiant" else T["DIRE"]).grid(
                         row=0, column=col, sticky="e" if col == 0 else "w", pady=(0, 8))
        done = len(CM_ORDER) if current is None else current
        tk.Label(inner, text="%d / %d" % (done, len(CM_ORDER)), font=F["small_b"], fg=T["TEXT2"],
                 bg=T["TOPBAR"]).grid(row=0, column=1, pady=(0, 8))
        for r, (kind, n_first, n_second) in enumerate(CM_BOARD, start=1):
            left, right = (n_first, n_second) if cm.first == "radiant" else (n_second, n_first)
            size = BAN_SIZE if kind == "ban" else PICK_SIZE
            for col, number in ((0, left), (2, right)):
                cell = self._cm_slot(inner, kind, number, size)
                cell.grid(row=r, column=col, sticky="e" if col == 0 else "w", pady=2)
            nums = tk.Frame(inner, bg=T["TOPBAR"])
            nums.grid(row=r, column=1, padx=8)
            for number, side in ((left, "l"), (right, "r")):
                self._cm_number(nums, number, side, current)

    def _cm_slot(self, parent, kind, number, size):
        """Клетка хода: сделан (портрет), текущий (золотая рамка), будущий или пустая."""
        T, tr, F, cm = self.T, self.tr, self.F, self._cm
        w, h = size
        if number is None:
            return tk.Frame(parent, bg=T["TOPBAR"], width=w, height=h)
        index = number - 1
        hero = cm.heroes[index]
        if hero:
            return tk.Label(parent, image=self.photo(hero, size, "ban" if kind == "ban" else None),
                            bg=T["TOPBAR"], bd=0)
        current = index == cm.current
        cell = tk.Frame(parent, width=w, height=h, highlightthickness=2 if current else 1,
                        bg=T["GOLD_BG"] if current else T["SLOT"],
                        highlightbackground=T["GOLD"] if current else T["LINE"])
        cell.pack_propagate(False)
        if current:
            tk.Label(cell, text=tr["cm_" + kind], font=F["small_b"],
                     fg=T["GOLD"], bg=T["GOLD_BG"]).pack(expand=True)
        return cell

    def _cm_number(self, parent, number, side, current):
        """Номер хода с чёрточкой в сторону того, кто ходит. Номера строки — рядом,
        левый и правый; без номера — пустое место той же ширины."""
        T, F = self.T, self.F
        if number is None:
            fg, bg, tick = T["TOPBAR"], T["TOPBAR"], T["TOPBAR"]
        elif current is not None and number - 1 == current:
            fg, bg, tick = T["ON_GOLD"], T["GOLD"], T["GOLD"]
        elif current is None or number - 1 < current:
            fg, bg, tick = T["TEXT4"], T["TOPBAR"], T["LINE"]
        else:
            fg, bg, tick = T["TEXT2"], T["TOPBAR"], T["LINE"]
        line = tk.Frame(parent, bg=tick, width=10, height=1)
        label = tk.Label(parent, text=str(number or ""), font=F["small_b"], fg=fg, bg=bg, width=2)
        if side == "l":
            line.pack(side=tk.LEFT)
            label.pack(side=tk.LEFT, padx=(2, 3))
        else:
            label.pack(side=tk.LEFT, padx=(3, 2))
            line.pack(side=tk.LEFT)

    # ── Текущий ход и подсказки ───────────────────────────────────────────────

    def _turn_words(self, index):
        """«Ваш бан» / «Пик Dire»."""
        tr, cm = self.tr, self._cm
        side, kind = cm.side(index), cm.kind(index)
        if side == cm.ours:
            return tr["cm_your_" + kind]
        return tr["cm_their_" + kind].format(side=tr["side_" + side])

    def _render_cm_turn(self):
        T, tr, F, cm = self.T, self.tr, self.F, self._cm
        for w in self._cm_turn.winfo_children():
            w.destroy()
        index = cm.current
        if index is None:
            tk.Label(self._cm_turn, text=tr["cm_done"], font=F["big"], fg=T["TEXT"],
                     bg=T["BG"]).pack(anchor="w")
            self._cm_entry_label.config(text=tr["cm_done_hint"])
            return
        kind, phase = cm.phase(index)
        ours = cm.side(index) == cm.ours
        tk.Label(self._cm_turn, text=tr["cm_step"].format(n=index + 1, total=len(CM_ORDER),
                                                          phase=tr["cm_phase_" + kind].format(n=phase)),
                 font=F["small"], fg=T["TEXT3"], bg=T["BG"]).pack(anchor="w")
        tk.Label(self._cm_turn, text=self._turn_words(index), font=F["big"],
                 fg=T["GOLD"] if ours else T["TEXT"], bg=T["BG"]).pack(anchor="w")
        # «ваш бан (10), бан Dire (12)»: строчная только первая буква — имя стороны остаётся
        upcoming = ", ".join("%s (%d)" % (self._turn_words(i)[:1].lower() + self._turn_words(i)[1:],
                                          i + 1)
                             for i, _, _ in cm.upcoming(3))
        if upcoming:
            tk.Label(self._cm_turn, text=tr["cm_next"].format(steps=upcoming), font=F["body"],
                     fg=T["TEXT2"], bg=T["BG"]).pack(anchor="w", pady=(2, 0))
        self._cm_entry_label.config(text=tr["cm_entry_" + kind].format(n=index + 1))

    def _render_cm_hints(self):
        """Две колонки: баны (до своих пиков — по мете) и пики."""
        T, cm = self.T, self._cm
        area = self._cm_hints.inner
        for w in area.winfo_children():
            w.destroy()
        cols = tk.Frame(area, bg=T["BG"])
        cols.pack(fill=tk.BOTH, expand=True, padx=(0, 16))
        cols.columnconfigure((0, 1), weight=1, uniform="hint")
        bans = tk.Frame(cols, bg=T["BG"])
        bans.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        picks = tk.Frame(cols, bg=T["BG"])
        picks.grid(row=0, column=1, sticky="nsew")
        if cm.bans_by_meta:
            self._render_cm_meta_bans(bans)
        else:
            self._render_cm_counter_hints(bans, "ban")
        self._render_cm_counter_hints(picks, "pick")

    def _cm_hint_status(self, box, heroes):
        """Под заголовком колонки: какие страницы ещё качаются, какие не загрузились."""
        T, tr, F, cm = self.T, self.tr, self.F, self._cm
        loading = [h for h in heroes if h in cm.loading]
        failed = [h for h in heroes if h in cm.failed]
        if loading:
            tk.Label(box, text=tr["draft_missing"].format(heroes=", ".join(loading)).strip(),
                     font=F["small"], fg=T["GOLD"], bg=T["BG"]).pack(anchor="w")
        if failed:
            tk.Label(box, text=tr["cm_failed"].format(heroes=", ".join(failed)),
                     font=F["small"], fg=T["BAD"], bg=T["BG"]).pack(anchor="w")
            button(box, T, F, tr["draft_retry"], lambda: self._cm_changed(retry=True),
                   kind="link", font="small_b").pack(anchor="w")

    def _render_cm_counter_hints(self, box, kind):
        """Контрпики: баны — против наших пиков, пики — против их пиков. Обе колонки
        — под свободные позиции: баны — противника, пики — свои."""
        T, tr, F, cm = self.T, self.tr, self.F, self._cm
        if kind == "ban":
            heroes, result = cm.picks(cm.ours), cm.ban_suggestions(self._limit)
            title, color = tr["cm_ban_title"], T["BAD"]
            caption = tr["cm_ban_why"].format(heroes=", ".join(heroes))
        else:
            heroes, result = cm.picks(cm.theirs), cm.pick_suggestions(self._limit)
            next_pick = cm.next_pick(cm.ours)
            title = tr["cm_pick_at"].format(n=next_pick + 1) if next_pick is not None \
                else tr["cm_pick_title"]
            color = T["GOOD"]
            caption = tr["cm_pick_why"].format(heroes=", ".join(heroes)) if heroes \
                else tr["cm_pick_empty"]
        tk.Label(box, text=title, font=F["h2"], fg=T["TEXT"], bg=T["BG"]).pack(anchor="w")
        tk.Label(box, text=caption, font=F["small"], fg=T["TEXT3"], bg=T["BG"],
                 justify=tk.LEFT, wraplength=HINT_WRAP).pack(anchor="w", pady=(2, 8))
        if result is not None:
            self._fill_line(box, cm, wrap=HINT_WRAP, theirs=kind == "ban")
        self._cm_hint_status(box, heroes)
        if result is None:
            return
        if not result.picks:
            tk.Label(box, text=tr["draft_nothing"].strip(), font=F["small"], fg=T["TEXT3"],
                     bg=T["BG"], justify=tk.LEFT, wraplength=HINT_WRAP).pack(anchor="w")
        for pick in result.picks:
            # «Мид · Тройка · 72к матчей»: что матчей — в самой редкой паре, сказано в подвале
            self._cm_hint_row(box, pick.hero, self._signed(pick.total), color,
                              tr["cm_hint_games"].format(n=self._count_text(pick.matches)))

    def _render_cm_meta_bans(self, box):
        """Баны до своих пиков — по мете: сильнейшие по винрейту в выбранном ранге."""
        T, tr, F, cm = self.T, self.tr, self.F, self._cm
        head = tk.Frame(box, bg=T["BG"])
        head.pack(fill=tk.X)
        tk.Label(head, text=tr["cm_ban_title"], font=F["h2"], fg=T["TEXT"], bg=T["BG"]).pack(
            side=tk.LEFT)
        self._rank_menu(head).pack(side=tk.RIGHT)
        tk.Label(box, text=tr["meta_why"].format(pick=int(MIN_PICK)), font=F["small"],
                 fg=T["TEXT3"], bg=T["BG"], justify=tk.LEFT, wraplength=HINT_WRAP).pack(
                     anchor="w", pady=(2, 8))
        result = cm.meta_bans(self._limit)
        if result is None:
            self._fetch_meta()
            if cm.meta_error is not None:
                tk.Label(box, text=tr["meta_failed"].format(detail=cm.meta_error), font=F["small"],
                         fg=T["BAD"], bg=T["BG"], justify=tk.LEFT, wraplength=HINT_WRAP).pack(anchor="w")
                button(box, T, F, tr["draft_retry"], lambda: self._fetch_meta(retry=True),
                       kind="link", font="small_b").pack(anchor="w")
            else:
                tk.Label(box, text=tr["loading"], font=F["small"], fg=T["GOLD"],
                         bg=T["BG"]).pack(anchor="w")
            return
        self._fill_line(box, cm, wrap=HINT_WRAP, theirs=True)
        for row in result:
            self._cm_hint_row(box, row.hero, self._percent(row.win), T["BAD"],
                              tr["meta_pick"].format(pick=self._percent(row.pick)))

    def _rank_menu(self, parent):
        """«Ранг: Legend ▾» — группа рангов меты; выбор запоминается."""
        T, tr, F, cm = self.T, self.tr, self.F, self._cm
        more = tk.Menubutton(parent, text=tr["rank_short_" + cm.rank] + " ▾", font=F["small_b"],
                             relief="flat", bd=0, padx=8, pady=2, cursor="hand2",
                             highlightthickness=1, highlightbackground=T["LINE"],
                             bg=T["BG"], fg=T["TEXT2"], activebackground=T["SELECTED"],
                             activeforeground=T["TEXT"])
        menu = tk.Menu(more, tearoff=0, bg=T["PANEL"], fg=T["TEXT"], font=F["body"], bd=0,
                       activebackground=T["SELECTED"], activeforeground=T["TEXT"])
        for rank in RANKS:
            menu.add_command(label=tr["rank_" + rank], command=lambda r=rank: self._set_meta_rank(r))
        more["menu"] = menu
        return more

    def _cm_hint_row(self, parent, hero, value, color, detail):
        """Строка подсказки: портрет, имя и число; под именем — позиции и пояснение."""
        T, F = self.T, self.F
        separator(parent, T)
        row = tk.Frame(parent, bg=T["BG"])
        row.pack(fill=tk.X, pady=6)
        tk.Label(row, image=self.photo(hero, (56, 32)), bg=T["BG"]).pack(side=tk.LEFT)
        body = tk.Frame(row, bg=T["BG"])
        body.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        top = tk.Frame(body, bg=T["BG"])
        top.pack(fill=tk.X)
        tk.Label(top, text=hero, font=F["name"], fg=T["TEXT"], bg=T["BG"]).pack(side=tk.LEFT)
        tk.Label(top, text=value, font=F["value"], fg=color, bg=T["BG"]).pack(side=tk.RIGHT)
        meta = [self._hero_positions(hero), detail]
        # Три позиции и пояснение в узкую колонку не влезают — переносится
        tk.Label(body, text=" · ".join(m for m in meta if m), font=F["small"], fg=T["TEXT3"],
                 bg=T["BG"], justify=tk.LEFT, wraplength=HINT_WRAP - 70).pack(anchor="w")

    # ── Действия ──────────────────────────────────────────────────────────────

    def _cm_play(self, typed):
        """Записать героя на текущий ход."""
        hero = best_match(typed)
        self._cm_box.clear()
        if not hero:
            return
        tr, T = self.tr, self.T
        outcome = self._cm.play(hero)
        self._switch_tab("cm")
        if outcome == "taken":
            self._cm_message.config(text=tr["cm_taken"].format(hero=hero), fg=T["BAD"])
            return
        if outcome == "done":
            self._cm_message.config(text=tr["cm_done_hint"], fg=T["TEXT3"])
            return
        self._cm_message.config(text="")
        self._cm_changed()

    def _cm_undo(self):
        hero = self._cm.undo()
        self._cm_message.config(text=self.tr["cm_undone"].format(hero=hero) if hero else "",
                                fg=self.T["TEXT3"])
        self._cm_changed(fetch=False)

    def _cm_reset(self):
        self._cm.reset()
        self._cm_message.config(text="")
        self._cm_changed(fetch=False)

    def _set_cm_ours(self, side):
        self._cm.ours = side
        self._cm_changed(fetch=False)

    def _set_cm_first(self, side):
        self._cm.first = side
        self._cm_changed(fetch=False)

    def _set_cm_role(self, role):
        self._cm.role = role
        update_config(cm_role=role)
        self._cm_changed(fetch=False)

    def _cm_changed(self, fetch=True, retry=False):
        """Драфт изменился — во вкладке или в оверлее: докачать и перерисовать."""
        if fetch or retry:
            self._fetch_for(self._cm, retry=retry)
        try:
            self._cm_ours_seg.set(self._cm.ours)
            self._cm_first_seg.set(self._cm.first)
            self._cm_roles.set(self._cm.role)
            self._render_cm()
        except (tk.TclError, AttributeError):
            pass  # вкладку как раз пересобирают
        self._overlay.refresh()
