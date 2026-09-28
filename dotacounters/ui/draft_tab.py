"""Вкладка «Драфт» (All Pick): враги, своя команда, баны и подбор пика.

Примесь к DotaApp (app.py): методы работают с его состоянием через self.
Состав — self._board (draft.DraftBoard), общий с оверлеем. Страницы врагов
качает главное окно (_fetch_for) сразу при добавлении врага.
"""

import tkinter as tk

from ..draft import GROUPS
from ..heroes import best_match
from .hero_browser import HeroBrowserModal
from .role_menu import RolePicker
from .suggestions import HeroSuggestions
from .widgets import EntryBox, ScrollArea, Segmented, button

#: Сколько ячеек показывать в списках, пока они не заполнены.
_SLOTS = {"enemies": 5, "allies": 4}


class DraftTab:

    def _build_draft_page(self):
        T, tr, F = self.T, self.tr, self.F
        page = tk.Frame(self._content, bg=T["BG"])
        self._draft_page = page
        page.columnconfigure(1, weight=1)
        page.rowconfigure(0, weight=1)

        # ── Слева: ввод и состав ──
        aside_area = ScrollArea(page, T, self._scrollables)
        aside_area.grid(row=0, column=0, sticky="nsw", padx=(24, 0), pady=(18, 12))
        aside_area.canvas.config(width=300)
        aside = aside_area.inner
        tk.Label(aside, text=tr["draft_add"], font=F["small"], fg=T["TEXT3"],
                 bg=T["BG"]).pack(anchor="w", pady=(0, 5))
        self._draft_box = EntryBox(aside, T, F, placeholder=tr["name_placeholder"], width=26)
        self._draft_box.pack(fill=tk.X)
        self.draft_entry = self._draft_box.entry
        self._draft_suggest = HeroSuggestions(
            page, self.draft_entry, T, F["input"], on_accept=self._add_draft_hero,
            placeholder_active=lambda: self._draft_box.showing_placeholder)
        self.draft_entry.bind("<FocusOut>", lambda e: self._draft_suggest.hide_later(), add="+")
        targets = tk.Frame(aside, bg=T["BG"])
        targets.pack(fill=tk.X, pady=(6, 0))
        self._group_seg = Segmented(targets, T, F, [(g, tr["draft_to_" + g]) for g in GROUPS],
                                    self._draft_group, self._set_draft_group, font="small_b", padx=9)
        self._group_seg.pack(side=tk.LEFT)
        button(targets, T, F, "⊞", lambda: HeroBrowserModal(
            self.root, T, tr, on_select=self._add_draft_hero, fonts=F),
            font="body_b").pack(side=tk.RIGHT)
        self._lineup = tk.Frame(aside, bg=T["BG"])
        self._lineup.pack(fill=tk.X, pady=(10, 0))

        # ── Справа: подсказки ──
        right = tk.Frame(page, bg=T["BG"])
        right.grid(row=0, column=1, sticky="nsew", padx=(24, 8), pady=(18, 12))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        bar = tk.Frame(right, bg=T["BG"])
        bar.grid(row=0, column=0, sticky="ew", padx=(0, 16))
        tk.Label(bar, text=tr["role_label"], font=F["small"], fg=T["TEXT3"],
                 bg=T["BG"]).pack(side=tk.LEFT, padx=(0, 8))
        self._draft_roles = RolePicker(bar, T, F, tr, self._board.role, self._set_draft_role)
        self._draft_roles.pack(side=tk.LEFT)
        self._draft_retry = button(bar, T, F, tr["draft_retry"], self.start_draft, kind="link",
                                   font="small_b")
        self._draft_results = ScrollArea(right, T, self._scrollables)
        self._draft_results.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self._draft_status = tk.Label(right, text="", font=F["small"], fg=T["TEXT3"], bg=T["BG"],
                                      anchor="w", justify=tk.LEFT)
        self._draft_status.grid(row=2, column=0, sticky="ew", pady=(6, 0))

        self._render_lineup()
        self._render_draft()
        return page

    # ── Состав ────────────────────────────────────────────────────────────────

    def _render_lineup(self):
        T, tr, F = self.T, self.tr, self.F
        box = self._lineup
        for w in box.winfo_children():
            w.destroy()
        board = self._board
        colors = {"enemies": T["BAD"], "allies": T["GOOD"], "bans": T["TEXT2"]}
        for group in GROUPS:
            heroes = board.groups[group]
            head = tk.Frame(box, bg=T["BG"])
            head.pack(fill=tk.X, pady=(12 if group != "enemies" else 0, 6))
            tk.Label(head, text=tr["draft_row_" + group], font=F["h2"], fg=colors[group],
                     bg=T["BG"]).pack(side=tk.LEFT)
            count = "%d / %d" % (len(heroes), board.limit_of(group)) if group in _SLOTS \
                else str(len(heroes))
            tk.Label(head, text=count, font=F["small"], fg=T["TEXT3"], bg=T["BG"]).pack(side=tk.RIGHT)
            if group == "bans":
                self._render_bans(box, heroes)
                continue
            for hero in heroes:
                self._lineup_slot(box, hero, group)
            if len(heroes) < _SLOTS[group]:
                empty = tk.Frame(box, bg=T["BG"], highlightthickness=1, highlightbackground=T["LINE"],
                                 height=46)
                empty.pack(fill=tk.X, pady=(0, 6))
                empty.pack_propagate(False)
                tk.Label(empty, text=tr["draft_next_" + group], font=F["body"], fg=T["TEXT4"],
                         bg=T["BG"]).pack(side=tk.LEFT, padx=14)

    def _lineup_slot(self, parent, hero, group):
        T, F, board = self.T, self.F, self._board
        slot = tk.Frame(parent, bg=T["PANEL"], highlightthickness=1, highlightbackground=T["LINE"])
        slot.pack(fill=tk.X, pady=(0, 6))
        tk.Label(slot, image=self.photo(hero, (64, 36)), bg=T["PANEL"]).pack(side=tk.LEFT, padx=4,
                                                                            pady=4)
        tk.Label(slot, text=hero, font=F["name"], fg=T["TEXT"], bg=T["PANEL"]).pack(side=tk.LEFT,
                                                                                    padx=(6, 0))
        if hero in board.loading:
            tk.Label(slot, text="…", font=F["body"], fg=T["GOLD"], bg=T["PANEL"]).pack(side=tk.LEFT,
                                                                                    padx=6)
        elif hero in board.failed:
            tk.Label(slot, text="!", font=F["body_b"], fg=T["BAD"], bg=T["PANEL"]).pack(side=tk.LEFT,
                                                                                     padx=6)
        button(slot, T, F, "×", lambda h=hero: self._remove_draft_hero(h), kind="link",
               font="h2", bg=T["PANEL"]).pack(side=tk.RIGHT, padx=4)

    def _render_bans(self, parent, heroes):
        T, tr, F = self.T, self.tr, self.F
        if not heroes:
            tk.Label(parent, text=tr["draft_no_bans"], font=F["small"], fg=T["TEXT4"],
                     bg=T["BG"]).pack(anchor="w")
            return
        grid = tk.Frame(parent, bg=T["BG"])
        grid.pack(anchor="w")
        for i, hero in enumerate(heroes):
            cell = tk.Label(grid, image=self.photo(hero, (64, 36), "ban"), bg=T["BG"], cursor="hand2")
            cell.grid(row=i // 4, column=i % 4, padx=(0, 6), pady=(0, 6))
            cell.bind("<Button-1>", lambda e, h=hero: self._remove_draft_hero(h))
        tk.Label(parent, text=tr["draft_ban_hint"], font=F["small"], fg=T["TEXT4"],
                 bg=T["BG"]).pack(anchor="w")

    # ── Подсказки ─────────────────────────────────────────────────────────────

    def _render_draft(self):
        """Вывод подбора по тому, что уже скачано."""
        T, tr, F, board = self.T, self.tr, self.F, self._board
        area = self._draft_results.inner
        for w in area.winfo_children():
            w.destroy()
        self._draft_status.config(text="")
        if board.failed and any(h in board.failed for h in board.enemies):
            self._draft_retry.pack(side=tk.RIGHT)
        else:
            self._draft_retry.pack_forget()

        notes = []
        for hero in board.enemies:
            if hero in board.failed:
                notes.append((tr["draft_failed"].format(hero=hero, detail=board.failed[hero]),
                              T["BAD"]))
        loading = [hero for hero in board.enemies if hero in board.loading]
        if loading:
            notes.append((tr["draft_missing"].format(heroes=", ".join(loading)), T["GOLD"]))

        if not board.enemies:
            tk.Label(area, text=tr["draft_empty_title"], font=F["h2"], fg=T["TEXT"],
                     bg=T["BG"]).pack(anchor="w")
            tk.Label(area, text=tr["draft_empty_text"], font=F["body"], fg=T["TEXT2"], bg=T["BG"],
                     justify=tk.LEFT, wraplength=560).pack(anchor="w", pady=(4, 0))
            return
        result = board.analyse(limit=self._limit)
        if result and result.skipped:
            notes.append((tr["draft_skipped"].format(heroes=", ".join(result.skipped)), T["BAD"]))
        for text, color in notes:
            tk.Label(area, text=text.strip(), font=F["body"], fg=color, bg=T["BG"],
                     justify=tk.LEFT, wraplength=620).pack(anchor="w", pady=(0, 6))
        if not result or not result.picks:
            if result is not None:
                tk.Label(area, text=tr["draft_nothing"].strip(), font=F["body"], fg=T["BAD"],
                         bg=T["BG"]).pack(anchor="w")
            return

        title = tk.Frame(area, bg=T["BG"])
        title.pack(fill=tk.X, pady=(0, 8))
        tk.Label(title, text=tr["draft_pick_title"], font=F["h2"], fg=T["TEXT"],
                 bg=T["BG"]).pack(side=tk.LEFT)
        tk.Label(title, text=tr["draft_against"].format(heroes=", ".join(result.enemies)) + " · "
                 + self._period_text(), font=F["body"], fg=T["TEXT3"], bg=T["BG"]).pack(
                     side=tk.LEFT, padx=(8, 0))
        self._pick_table(area, result)

        tk.Label(area, text=tr["draft_avoid_title"], font=F["h2"], fg=T["TEXT"],
                 bg=T["BG"]).pack(anchor="w", pady=(18, 8))
        cards = tk.Frame(area, bg=T["BG"])
        cards.pack(fill=tk.X)
        for i, pick in enumerate(result.avoid):
            card = tk.Frame(cards, bg=T["BG"])
            card.grid(row=i // 6, column=i % 6, sticky="nw", padx=(0, 12), pady=(0, 10))
            tk.Label(card, image=self.photo(pick.hero, (96, 54)), bg=T["BG"]).pack(anchor="w")
            tk.Label(card, text=pick.hero, font=F["small_b"], fg=T["TEXT"], bg=T["BG"]).pack(
                anchor="w", pady=(4, 0))
            tk.Label(card, text=self._signed(pick.total), font=F["value"], fg=T["BAD"],
                     bg=T["BG"]).pack(anchor="w")
        self._draft_status.config(text=tr["draft_footnote2"])

    def _pick_table(self, parent, result):
        """«Брать»: герой, сумма, вклад против каждого врага, матчей в редкой паре."""
        T, tr, F = self.T, self.tr, self.F
        table = tk.Frame(parent, bg=T["BG"])
        table.pack(fill=tk.X)
        enemies = result.enemies
        table.columnconfigure(0, weight=1)
        heads = [tk.Label(table, text=tr["col_hero"], font=F["small_b"], fg=T["TEXT3"], bg=T["BG"]),
                 tk.Label(table, text=tr["col_sum"], font=F["small_b"], fg=T["TEXT3"], bg=T["BG"])]
        for enemy in enemies:
            heads.append(tk.Label(table, image=self.photo(enemy, (40, 22)), bg=T["BG"]))
        heads.append(tk.Label(table, text=tr["col_matches"], font=F["small_b"], fg=T["TEXT3"],
                              bg=T["BG"]))
        for col, w in enumerate(heads):
            w.grid(row=0, column=col, sticky="w" if col == 0 else "e", padx=(0, 0 if col == 0 else 14),
                   pady=(0, 6))
        for i, pick in enumerate(result.picks):
            r = 1 + i * 2
            tk.Frame(table, bg=T["LINE_SOFT"], height=1).grid(row=r, column=0,
                                                              columnspan=len(heads), sticky="ew")
            who = tk.Frame(table, bg=T["BG"])
            who.grid(row=r + 1, column=0, sticky="w", pady=6)
            tk.Label(who, image=self.photo(pick.hero, (56, 32)), bg=T["BG"]).pack(side=tk.LEFT)
            tk.Label(who, text=pick.hero, font=F["name"], fg=T["TEXT"], bg=T["BG"]).pack(
                side=tk.LEFT, padx=(10, 0))
            tk.Label(table, text=self._signed(pick.total), font=F["value"], fg=T["GOOD"],
                     bg=T["BG"]).grid(row=r + 1, column=1, sticky="e", padx=(0, 14))
            for j, enemy in enumerate(enemies):
                value = pick.per_enemy.get(enemy)
                tk.Label(table, text=self._signed(value) if value is not None else "—",
                         font=F["body"], fg=T["TEXT2"], bg=T["BG"]).grid(
                             row=r + 1, column=2 + j, sticky="e", padx=(0, 14))
            tk.Label(table, text=self._count_text(pick.matches), font=F["body"], fg=T["TEXT3"],
                     bg=T["BG"]).grid(row=r + 1, column=2 + len(enemies), sticky="e", padx=(0, 14))

    # ── Действия ──────────────────────────────────────────────────────────────

    def _set_draft_group(self, group):
        """Выбрать список, в который пойдёт следующий набранный герой."""
        self._draft_group = group
        self._group_seg.set(group)
        self.draft_entry.focus_set()

    def _set_draft_role(self, role):
        self._board.role = role
        self._draft_changed(fetch=False)

    def _add_draft_hero(self, hero):
        """Добавить героя в выбранный список: имя приводится к известному герою."""
        name = best_match(hero)
        self._draft_box.clear()
        if not name:
            return
        tr, T, group = self.tr, self.T, self._draft_group
        outcome = self._board.add(group, name)
        if outcome == "dup":
            message, color = tr["draft_dup"].format(hero=name), T["TEXT2"]
        elif outcome == "full":
            message = tr["draft_full_group"].format(max=self._board.limit_of(group))
            color = T["BAD"]
        elif outcome == "moved":
            message = tr["draft_moved"].format(hero=name, group=tr["draft_row_" + group])
            color = T["GOLD"]
        else:
            message, color = "", T["TEXT3"]
        if outcome in ("added", "moved"):
            self._draft_changed()
        self._switch_tab("draft")
        if message:
            self._draft_status.config(text=message, fg=color)

    def _remove_draft_hero(self, hero):
        self._board.remove(hero)
        self._draft_changed()

    def _draft_changed(self, fetch=True):
        """Состав изменился — во вкладке или в оверлее: докачать и перерисовать всё."""
        if fetch:
            self._fetch_for(self._board)
        try:
            self._draft_roles.set(self._board.role)
            self._render_lineup()
            self._render_draft()
        except (tk.TclError, AttributeError):
            pass  # вкладку как раз пересобирают
        self._overlay.refresh()

    def start_draft(self):
        """«Повторить»: снова скачать страницы, что не загрузились."""
        self._fetch_for(self._board, retry=True)
        self._draft_changed(fetch=False)
