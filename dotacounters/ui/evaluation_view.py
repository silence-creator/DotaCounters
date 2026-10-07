"""Вывод оценки драфта (evaluate.py) — общий для вкладок «Драфт» и «Captains Mode».

Примесь к DotaApp (app.py): методы работают с его состоянием через self.
"""

import tkinter as tk

from ..evaluate import evaluate
from .widgets import Segmented, separator

#: Перенос текста в оценке: узкая колонка Captains Mode — около 500 пикселей.
EVAL_WRAP = 480


class EvaluationView:

    def _render_evaluation(self, parent, ours, theirs, reports, names, loading=()):
        """Оценка драфта ours против theirs. names — (подпись нашей команды, их).
        loading — чьи страницы ещё качаются."""
        T, tr, F, cm = self.T, self.tr, self.F, self._cm
        if not ours or not theirs:
            tk.Label(parent, text=tr["eval_empty"], font=F["body"], fg=T["TEXT2"], bg=T["BG"],
                     justify=tk.LEFT, wraplength=EVAL_WRAP).pack(anchor="w")
            return
        if cm.meta is None:
            self._fetch_meta()             # мета — для строки о винрейтах; оценка её не ждёт
        result = evaluate(ours, theirs, reports, meta=cm.meta, rank=cm.rank)
        our_name, their_name = names

        # ── Итог ──
        good = result.score >= 0
        leader = our_name if good else their_name
        tk.Label(parent, text=tr["eval_score"].format(team=leader,
                                                      value=self._signed(abs(result.score))),
                 font=F["h1"], fg=T["GOOD"] if good else T["BAD"], bg=T["BG"],
                 justify=tk.LEFT, wraplength=EVAL_WRAP).pack(anchor="w")
        tk.Label(parent, text=tr["eval_score_why"].format(n=len(result.pairs)), font=F["small"],
                 fg=T["TEXT3"], bg=T["BG"], justify=tk.LEFT, wraplength=EVAL_WRAP).pack(
                     anchor="w", pady=(2, 0))
        if result.meta:
            tk.Label(parent, text=tr["eval_meta"].format(
                rank=tr["rank_short_" + cm.rank], ours=self._percent(result.meta[0]),
                theirs=self._percent(result.meta[1])), font=F["small"], fg=T["TEXT2"],
                bg=T["BG"], justify=tk.LEFT, wraplength=EVAL_WRAP).pack(anchor="w", pady=(2, 0))
        waiting = [h for h in loading if h in ours or h in theirs]
        if waiting:
            tk.Label(parent, text=tr["draft_missing"].format(heroes=", ".join(waiting)),
                     font=F["small"], fg=T["GOLD"], bg=T["BG"], justify=tk.LEFT,
                     wraplength=EVAL_WRAP).pack(anchor="w", pady=(2, 0))
        elif result.unknown:
            tk.Label(parent, text=tr["eval_unknown"].format(heroes=", ".join(result.unknown)),
                     font=F["small"], fg=T["BAD"], bg=T["BG"], justify=tk.LEFT,
                     wraplength=EVAL_WRAP).pack(anchor="w", pady=(2, 0))

        self._eval_matrix(parent, result)

        # ── Главные пары ──
        cols = tk.Frame(parent, bg=T["BG"])
        cols.pack(fill=tk.X, pady=(14, 0))
        cols.columnconfigure((0, 1), weight=1, uniform="pairs")
        for col, (title, pairs, color) in enumerate(((tr["eval_best"], result.best(), T["GOOD"]),
                                                     (tr["eval_worst"], result.worst(), T["BAD"]))):
            box = tk.Frame(cols, bg=T["BG"])
            box.grid(row=0, column=col, sticky="nw", padx=(0, 16) if col == 0 else 0)
            tk.Label(box, text=title, font=F["h2"], fg=T["TEXT"], bg=T["BG"]).pack(anchor="w")
            if not pairs:
                tk.Label(box, text=tr["eval_no_pairs"], font=F["small"], fg=T["TEXT3"],
                         bg=T["BG"]).pack(anchor="w", pady=(4, 0))
            for pair in pairs:
                row = tk.Frame(box, bg=T["BG"])
                row.pack(fill=tk.X, pady=(4, 0))
                tk.Label(row, text="%s → %s" % (pair.ours, pair.theirs), font=F["body"],
                         fg=T["TEXT"], bg=T["BG"]).pack(side=tk.LEFT)
                tk.Label(row, text=self._signed(pair.value), font=F["body_b"], fg=color,
                         bg=T["BG"]).pack(side=tk.RIGHT, padx=(10, 0))

        # ── Линии ──
        if result.lanes:
            tk.Label(parent, text=tr["eval_lanes"], font=F["h2"], fg=T["TEXT"], bg=T["BG"]).pack(
                anchor="w", pady=(14, 0))
            for lane in result.lanes:
                separator(parent, T)
                row = tk.Frame(parent, bg=T["BG"])
                row.pack(fill=tk.X, pady=5)
                tk.Label(row, text=self._signed(lane.value), font=F["value"], bg=T["BG"],
                         fg=T["GOOD"] if lane.value >= 0 else T["BAD"]).pack(side=tk.RIGHT)
                text = tk.Frame(row, bg=T["BG"])
                text.pack(side=tk.LEFT, fill=tk.X, expand=True)
                tk.Label(text, text=tr["lane_" + lane.lane], font=F["name"], fg=T["TEXT"],
                         bg=T["BG"]).pack(anchor="w")
                tk.Label(text, text=tr["eval_lane_vs"].format(ours=", ".join(lane.ours),
                                                              theirs=", ".join(lane.theirs)),
                         font=F["small"], fg=T["TEXT3"], bg=T["BG"], justify=tk.LEFT,
                         wraplength=EVAL_WRAP - 80).pack(anchor="w")
        tk.Label(parent, text=tr["eval_footnote"], font=F["small"], fg=T["TEXT3"], bg=T["BG"],
                 justify=tk.LEFT, wraplength=EVAL_WRAP).pack(anchor="w", pady=(14, 0))

    def _eval_matrix(self, parent, result):
        """Таблица «каждый против каждого»: строки — наши, столбцы — их, справа сумма."""
        T, tr, F = self.T, self.tr, self.F
        table = tk.Frame(parent, bg=T["BG"])
        table.pack(anchor="w", pady=(12, 0))
        tk.Label(table, text="", bg=T["BG"]).grid(row=0, column=0)
        for j, hero in enumerate(result.theirs):
            tk.Label(table, image=self.photo(hero, (40, 22)), bg=T["BG"]).grid(
                row=0, column=1 + j, padx=4, pady=(0, 4))
        tk.Label(table, text=tr["col_sum"], font=F["small_b"], fg=T["TEXT3"], bg=T["BG"]).grid(
            row=0, column=1 + len(result.theirs), padx=(10, 0), sticky="e")
        for i, ours in enumerate(result.ours):
            who = tk.Frame(table, bg=T["BG"])
            who.grid(row=1 + i, column=0, sticky="w", pady=2)
            tk.Label(who, image=self.photo(ours, (40, 22)), bg=T["BG"]).pack(side=tk.LEFT)
            tk.Label(who, text=ours, font=F["small_b"], fg=T["TEXT"], bg=T["BG"]).pack(
                side=tk.LEFT, padx=(6, 8))
            for j, theirs in enumerate(result.theirs):
                value = result.value(ours, theirs)
                if value is None:
                    text, fg = "—", T["TEXT4"]
                else:
                    text = self._signed(value)
                    fg = T["GOOD"] if value >= 1 else T["BAD"] if value <= -1 else T["TEXT2"]
                tk.Label(table, text=text, font=F["small"], fg=fg, bg=T["BG"]).grid(
                    row=1 + i, column=1 + j, padx=4, sticky="e")
            total = result.hero_total(ours)
            tk.Label(table, text=self._signed(total), font=F["small_b"], bg=T["BG"],
                     fg=T["GOOD"] if total >= 0 else T["BAD"]).grid(
                         row=1 + i, column=1 + len(result.theirs), padx=(10, 0), sticky="e")

    def _view_switch(self, parent, value, on_change):
        """«Подбор | Оценка драфта» над подсказками."""
        T, tr, F = self.T, self.tr, self.F
        row = tk.Frame(parent, bg=T["BG"])
        row.pack(fill=tk.X, pady=(0, 12))
        Segmented(row, T, F, [("picks", tr["view_picks"]), ("eval", tr["view_eval"])], value,
                  on_change, font="small_b", padx=10).pack(side=tk.LEFT)
