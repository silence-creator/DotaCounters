"""Общие виджеты нового интерфейса: кнопки, сегменты, «фишки», поле ввода,
прокрутка, полоса преимущества.

Tk не рисует скругления у рамок, поэтому кнопки и «фишки» прямоугольные с
тонкой рамкой, а скруглены только картинки (icons.rounded).
"""

import tkinter as tk
from tkinter import ttk


def button(parent, T, F, text, command, kind="ghost", font="button", **kw):
    """Кнопка: primary — золотая, ghost — вторичная с рамкой, link — без фона."""
    bg = kw.pop("bg", None)
    if kind == "primary":
        opts = dict(bg=T["GOLD"], fg=T["ON_GOLD"], activebackground=T["GOLD"],
                    activeforeground=T["ON_GOLD"], highlightthickness=0, padx=16, pady=6)
    elif kind == "link":
        opts = dict(bg=bg or T["BG"], fg=T["TEXT2"], activebackground=bg or T["BG"],
                    activeforeground=T["TEXT"], highlightthickness=0, padx=4, pady=2)
    else:
        opts = dict(bg=T["RAISED"], fg=T["TEXT"], activebackground=T["SELECTED"],
                    activeforeground=T["TEXT"], highlightthickness=1,
                    highlightbackground=T["LINE"], highlightcolor=T["LINE"], padx=12, pady=4)
    opts.update(kw)
    btn = tk.Button(parent, text=text, command=command, font=F[font], relief="flat", bd=0,
                    cursor="hand2", **opts)
    if kind == "link":
        btn.bind("<Enter>", lambda e: btn.config(fg=T["TEXT"]))
        btn.bind("<Leave>", lambda e: btn.config(fg=T["TEXT2"]))
    return btn


class Segmented(tk.Frame):
    """Переключатель из нескольких вариантов; выбранный подсвечен.

    options — [(значение, подпись)]; on_change(значение) — при выборе.
    """

    def __init__(self, parent, T, F, options, value, on_change, font="button", padx=11):
        super().__init__(parent, bg=T["LINE"], padx=1, pady=1)
        self.T, self.value, self._on_change = T, value, on_change
        self.buttons = {}
        for i, (key, label) in enumerate(options):
            btn = tk.Button(self, text=label, font=F[font], relief="flat", bd=0,
                            highlightthickness=0, padx=padx, pady=3, cursor="hand2",
                            command=lambda k=key: self._pick(k))
            btn.pack(side=tk.LEFT, padx=(1 if i else 0, 0), fill=tk.Y)
            self.buttons[key] = btn
        self.set(value)

    def _pick(self, key):
        if key != self.value:
            self.set(key)
            self._on_change(key)

    def set(self, value):
        T = self.T
        self.value = value
        for key, btn in self.buttons.items():
            on = key == value
            btn.config(bg=T["SELECTED"] if on else T["BG"], fg=T["TEXT"] if on else T["TEXT2"],
                       activebackground=T["SELECTED"], activeforeground=T["TEXT"])


class ChipRow(tk.Frame):
    """Ряд «фишек» с одной выбранной — например, роли соперников."""

    def __init__(self, parent, T, F, options, value, on_change, bg=None, font="small_b"):
        super().__init__(parent, bg=bg or T["BG"])
        self.T, self.value, self._on_change = T, value, on_change
        self.chips = {}
        for key, label in options:
            chip = tk.Button(self, text=label, font=F[font], relief="flat", bd=0, padx=10, pady=3,
                             cursor="hand2", highlightthickness=1,
                             command=lambda k=key: self._pick(k))
            chip.pack(side=tk.LEFT, padx=(0, 6))
            self.chips[key] = chip
        self.set(value)

    def _pick(self, key):
        if key != self.value:
            self.set(key)
            self._on_change(key)

    def set(self, value):
        T = self.T
        self.value = value
        for key, chip in self.chips.items():
            on = key == value
            chip.config(bg=T["GOLD_BG"] if on else T["BG"], fg=T["TEXT"] if on else T["TEXT2"],
                        activebackground=T["GOLD_BG"], activeforeground=T["TEXT"],
                        highlightbackground=T["GOLD"] if on else T["LINE"],
                        highlightcolor=T["GOLD"] if on else T["LINE"])


def chip(parent, T, F, text, command, bg=None, fg=None, font="small_b"):
    """Одиночная «фишка»-кнопка: избранное, недавние, герой в составе."""
    return tk.Button(parent, text=text, font=F[font], relief="flat", bd=0, padx=9, pady=2,
                     cursor="hand2", bg=bg or T["BG"], fg=fg or T["TEXT2"],
                     activebackground=T["SELECTED"], activeforeground=T["TEXT"],
                     highlightthickness=1, highlightbackground=T["LINE"],
                     highlightcolor=T["LINE"], command=command)


class EntryBox(tk.Frame):
    """Поле ввода в рамке: рамка золотая, пока поле в фокусе. Есть подсказка-заглушка."""

    def __init__(self, parent, T, F, placeholder="", font="input", width=None):
        super().__init__(parent, bg=T["LINE"], padx=1, pady=1)
        self.T, self.placeholder = T, placeholder
        self.entry = tk.Entry(self, font=F[font], bg=T["PANEL"], fg=T["TEXT"],
                              insertbackground=T["GOLD"], relief="flat", bd=7,
                              highlightthickness=0, disabledbackground=T["PANEL"])
        if width:
            self.entry.config(width=width)
        self.entry.pack(fill=tk.BOTH, expand=True)
        self.showing_placeholder = False
        self.entry.bind("<FocusIn>", self._focus_in, add="+")
        self.entry.bind("<FocusOut>", self._focus_out, add="+")
        self._show_placeholder()

    def _show_placeholder(self):
        if self.placeholder and not self.entry.get():
            self.showing_placeholder = True
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=self.T["TEXT3"])

    def _focus_in(self, event=None):
        self.config(bg=self.T["GOLD"])
        if self.showing_placeholder:
            self.showing_placeholder = False
            self.entry.delete(0, tk.END)
            self.entry.config(fg=self.T["TEXT"])

    def _focus_out(self, event=None):
        self.config(bg=self.T["LINE"])
        self._show_placeholder()

    def get(self) -> str:
        return "" if self.showing_placeholder else self.entry.get()

    def set(self, text: str):
        self.showing_placeholder = False
        self.entry.config(fg=self.T["TEXT"])
        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)
        if not text and self.focus_get() is not self.entry:
            self._show_placeholder()

    def clear(self):
        self.set("")


class ScrollArea(tk.Frame):
    """Прокручиваемая колонка: полотно, полоса прокрутки и внутренняя рамка inner.

    Полотно регистрируется в scrollables — колесо мыши находит его по курсору.
    """

    def __init__(self, parent, T, scrollables, bg=None):
        bg = bg or T["BG"]
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, bd=0, highlightthickness=0)
        self.bar = ttk.Scrollbar(self, orient="vertical", style="Dark.Vertical.TScrollbar",
                                 command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self._bar_set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.bar.grid(row=0, column=1, sticky="ns")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>",
                        lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfig(self._window, width=e.width))
        scrollables.append(self.canvas)

    def _bar_set(self, first, last):
        # Полоса прокрутки — только когда есть что прокручивать
        if float(first) <= 0.0 and float(last) >= 1.0:
            self.bar.grid_remove()
        else:
            self.bar.grid()
        self.bar.set(first, last)

    def to_top(self):
        self.canvas.yview_moveto(0)


class Bar(tk.Frame):
    """Полоса величины преимущества: доля fraction от ширины, цвет color."""

    def __init__(self, parent, T, fraction, color, height=4):
        super().__init__(parent, bg=T["LINE_SOFT"], height=height)
        fill = tk.Frame(self, bg=color, height=height)
        fill.place(x=0, y=0, relheight=1, relwidth=max(0.02, min(1.0, fraction)))


def separator(parent, T, color=None, pady=0):
    line = tk.Frame(parent, bg=color or T["LINE_SOFT"], height=1)
    line.pack(fill=tk.X, pady=pady)
    return line
