"""Выпадающий список ролей для драфта: во вкладке и в оверлее."""

import tkinter as tk

from ..draft import ROLE_FILTERS


def role_menu(parent, theme, tr, current, on_change, font=("Courier New", 9, "bold")):
    """Список «Любая, Керри, Саппорт…». on_change(роль или None) — при выборе."""
    T = theme
    options = [(None, tr["role_any"])] + [(role, tr["role_" + role]) for role in ROLE_FILTERS]
    by_label = {label: role for role, label in options}
    var = tk.StringVar(value=dict(options).get(current, tr["role_any"]))
    menu = tk.OptionMenu(parent, var, *[label for _, label in options],
                         command=lambda label: on_change(by_label[label]))
    menu.config(font=font, bg=T["BG_PANEL"], fg=T["ACCENT3"],
                activebackground=T["GLOW"], activeforeground=T["ACCENT"],
                relief="flat", bd=0, highlightthickness=1,
                highlightbackground=T["BORDER"], cursor="hand2", padx=8, pady=2)
    menu["menu"].config(font=(font[0], font[1]), bg=T["BG_PANEL"], fg=T["TEXT_PRIMARY"],
                        activebackground=T["GLOW"], activeforeground=T["ACCENT"], bd=0)
    # Роль общая для вкладки и оверлея: выбранную в одном месте показываем в другом
    menu.show_role = lambda role: var.set(dict(options).get(role, tr["role_any"]))
    return menu
