"""Выпадающие подсказки под полем ввода имени героя.

Один и тот же виджет используют поиск и драфт, поэтому что делать с выбранным
героем решает вызывающий: он передаёт on_accept.
"""

import tkinter as tk

from ..heroes import suggest


class HeroSuggestions:
    """Список подсказок под полем ввода.

    on_accept(имя) вызывается по Enter или щелчку. Если подсказка не выбрана,
    приходит то, что набрано в поле, — поиск ищет это как есть.
    """

    def __init__(self, page, entry, theme, font, on_accept, placeholder_active=None):
        self.entry, self.page, self.T = entry, page, theme
        self.on_accept = on_accept
        self._placeholder = placeholder_active or (lambda: False)
        self.visible = False

        self.box = tk.Listbox(
            page, font=font, activestyle="none", exportselection=False,
            bg=theme["BG_PANEL"], fg=theme["TEXT_PRIMARY"],
            selectbackground=theme["GLOW"], selectforeground=theme["ACCENT"],
            relief="flat", bd=0, highlightthickness=1,
            highlightbackground=theme["ACCENT"], highlightcolor=theme["ACCENT"])
        self.box.bind("<Button-1>", self._on_click)
        self.box.bind("<Return>", lambda e: self._accept())
        self.box.bind("<Escape>", lambda e: self.hide())

        entry.bind("<KeyRelease>", self._on_key)
        entry.bind("<Down>", lambda e: self._move(1))
        entry.bind("<Up>", lambda e: self._move(-1))
        entry.bind("<Return>", self._on_return)
        entry.bind("<Escape>", lambda e: self.hide())

    # ── Показ и скрытие ───────────────────────────────────────────────────────

    def update(self):
        matches = suggest(self.entry.get())
        typed = self.entry.get().strip().lower()
        if not matches or [m.lower() for m in matches] == [typed]:
            self.hide()
            return
        self.box.delete(0, tk.END)
        for hero in matches:
            self.box.insert(tk.END, "  " + hero)
        self.box.config(height=len(matches))
        entry, page = self.entry, self.page
        self.box.place(x=entry.winfo_rootx() - page.winfo_rootx(),
                       y=entry.winfo_rooty() - page.winfo_rooty() + entry.winfo_height() + 2,
                       width=entry.winfo_width())
        self.box.lift()
        self.visible = True

    def hide(self):
        if not self.visible:
            return
        try:
            self.box.place_forget()
        except tk.TclError:
            pass  # интерфейс пересобрали
        self.visible = False

    def hide_later(self, delay=200):
        """Скрыть с задержкой: щелчок по подсказке сперва уводит фокус из поля."""
        self.box.after(delay, self.hide)

    # ── Клавиши и мышь ────────────────────────────────────────────────────────

    def _on_key(self, event):
        if event.keysym in ("Up", "Down", "Return", "Escape", "Tab"):
            return
        if self._placeholder():
            self.hide()
        else:
            self.update()

    def _move(self, step):
        """Стрелки перебирают подсказки; первое нажатие вниз открывает список."""
        if not self.visible:
            if step > 0 and not self._placeholder():
                self.update()
            return "break"
        current = self.box.curselection()
        index = (current[0] + step) if current else (0 if step > 0 else self.box.size() - 1)
        index = max(0, min(index, self.box.size() - 1))
        self.box.selection_clear(0, tk.END)
        self.box.selection_set(index)
        self.box.activate(index)
        self.box.see(index)
        return "break"

    def _selected(self):
        current = self.box.curselection()
        return self.box.get(current[0]).strip() if current else None

    def _accept(self, hero=None):
        hero = hero or self._selected()
        if not hero:
            return False
        self.hide()
        self.on_accept(hero)
        return True

    def _on_click(self, event):
        self._accept(self.box.get(self.box.nearest(event.y)).strip())
        return "break"

    def _on_return(self, event):
        """Enter: выбранная подсказка, иначе то, что набрано руками."""
        if not (self.visible and self._accept()):
            self.hide()
            typed = self.entry.get().strip()
            if typed:
                self.on_accept(typed)
        return "break"
