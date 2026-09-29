"""Выбор позиции или роли: «фишки» позиций 1–5 и меню «Ещё ▾» с ролями Valve.

Позиции — по статистике линий Dotabuff (positions.py), роли — по разметке
Valve (draft.ROLE_FILTERS). Используется в поиске и в обоих драфтах.
"""

import tkinter as tk

from ..draft import ROLE_FILTERS
from ..positions import POSITIONS
from .widgets import ChipRow

#: Что стоит «фишками»; роли Valve — в меню «Ещё». Керри Valve в меню нет:
#: его заменяет позиция 1 с той же подписью.
MAIN_ROLES = POSITIONS
_MORE = "__more__"


class RolePicker(tk.Frame):
    """Любая / основные роли / «Ещё ▾». on_change(роль или None) — при выборе."""

    def __init__(self, parent, T, F, tr, current, on_change, bg=None, main=MAIN_ROLES):
        bg = bg or T["BG"]
        super().__init__(parent, bg=bg)
        self.T, self.F, self.tr, self._on_change, self.main = T, F, tr, on_change, main
        self.extra = [r for r in ROLE_FILTERS if r not in main and r != "carry"]
        self.value = current
        self.chips = ChipRow(self, T, F, [(None, tr["role_any"])] +
                             [(r, tr["role_" + r]) for r in main],
                             self._chip_value(current), self._pick, bg=bg)
        self.chips.pack(side=tk.LEFT)
        self.more = tk.Menubutton(self, font=F["small_b"], relief="flat", bd=0, padx=10, pady=3,
                                  cursor="hand2", highlightthickness=1,
                                  activebackground=T["SELECTED"], activeforeground=T["TEXT"])
        menu = tk.Menu(self.more, tearoff=0, bg=T["PANEL"], fg=T["TEXT"],
                       activebackground=T["SELECTED"], activeforeground=T["TEXT"],
                       font=F["body"], bd=0)
        for role in self.extra:
            menu.add_command(label=tr["role_" + role], command=lambda r=role: self._pick(r))
        self.more["menu"] = menu
        self.more.pack(side=tk.LEFT)
        self.set(current)

    def _chip_value(self, role):
        return role if role is None or role in self.main else _MORE

    def _pick(self, role):
        if role == _MORE or role == self.value:
            return
        self.set(role)
        self._on_change(role)

    def set(self, role):
        """Показать выбранную роль, не вызывая on_change."""
        T, tr = self.T, self.tr
        self.value = role
        self.chips.set(self._chip_value(role))
        on = role in self.extra
        self.more.config(text=(tr["role_" + role] if on else tr["role_more"]) + " ▾",
                         bg=T["GOLD_BG"] if on else self["bg"],
                         fg=T["TEXT"] if on else T["TEXT2"],
                         highlightbackground=T["GOLD"] if on else T["LINE"])
