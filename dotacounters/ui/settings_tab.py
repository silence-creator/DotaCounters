"""Вкладка «Настройки»: тема, язык, строк в списках, клавиша оверлея, данные,
обновления и история изменений, о программе.

Примесь к DotaApp (app.py): методы работают с его состоянием через self.
"""

import tkinter as tk

from ..config import update_config
from ..dotabuff import MAX_LIMIT
from ..hotkey import HOTKEY_PRESETS, GlobalHotkey, format_hotkey, parse_hotkey
from ..themes import THEMES
from ..version import APP_VERSION
from .widgets import ScrollArea, Segmented, button


class SettingsTab:

    def _build_settings_page(self):
        T, tr, F = self.T, self.tr, self.F
        page = tk.Frame(self._content, bg=T["BG"])
        self._settings_page = page
        page.columnconfigure(0, weight=1)
        page.rowconfigure(0, weight=1)
        area = ScrollArea(page, T, self._scrollables)
        area.grid(row=0, column=0, sticky="nsew", padx=(24, 8), pady=(18, 12))
        box = area.inner

        # ── Вид ──
        self._section(box, tr["set_look"])
        self._setting_row(box, tr["set_theme"], lambda p: Segmented(
            p, T, F, [(k, t["name_" + self._lang]) for k, t in THEMES.items()],
            self._theme_key, self._set_theme))
        self._setting_row(box, tr["set_lang"], lambda p: Segmented(
            p, T, F, [("ru", "Русский"), ("en", "English")], self._lang, self._set_lang))
        self._setting_row(box, tr["set_rows"], self._rows_control, hint=tr["set_rows_hint"])

        # ── Оверлей ──
        self._section(box, tr["set_hotkey_head"])
        self._setting_row(box, tr["set_hotkey"], self._hotkey_control, hint=self._hotkey_hint())

        # ── Данные ──
        self._section(box, tr["set_cache_head"])
        self._cache_label = tk.Label(box, text=tr["set_cache_info"].format(n=self._pages.count()),
                                     font=F["body"], fg=T["TEXT2"], bg=T["BG"], justify=tk.LEFT)
        self._cache_label.pack(anchor="w")
        button(box, T, F, tr["set_cache_clear"], self._clear_page_cache).pack(anchor="w",
                                                                             pady=(8, 0))

        # ── Обновления ──
        self._section(box, tr["upd_title"])
        row = tk.Frame(box, bg=T["BG"])
        row.pack(fill=tk.X)
        tk.Label(row, text=tr["set_version"].format(version=APP_VERSION), font=F["body_b"],
                 fg=T["TEXT"], bg=T["BG"]).pack(side=tk.LEFT)
        button(row, T, F, tr["upd_check_btn"],
               lambda: self._start_update_check(manual=True)).pack(side=tk.LEFT, padx=(14, 0))
        self._update_status = tk.Label(row, text="", font=F["small"], fg=T["TEXT3"], bg=T["BG"])
        self._update_status.pack(side=tk.LEFT, padx=(10, 0))
        self._changelog(box)

        # ── О программе ──
        self._section(box, tr["set_about_head"])
        tk.Label(box, text=tr["set_about_text"], font=F["body"], fg=T["TEXT2"], bg=T["BG"],
                 justify=tk.LEFT, wraplength=820).pack(anchor="w", pady=(0, 20))
        return page

    def _section(self, parent, title):
        T, F = self.T, self.F
        tk.Label(parent, text=title, font=F["h2"], fg=T["TEXT"], bg=T["BG"]).pack(
            anchor="w", pady=(18 if parent.winfo_children() else 0, 4))
        tk.Frame(parent, bg=T["LINE_SOFT"], height=1).pack(fill=tk.X, pady=(0, 10))

    def _setting_row(self, parent, label, make, hint=None):
        """Строка настройки: подпись слева, управление справа, пояснение под ним."""
        T, F = self.T, self.F
        row = tk.Frame(parent, bg=T["BG"])
        row.pack(fill=tk.X, pady=(0, 10))
        tk.Label(row, text=label, font=F["body"], fg=T["TEXT2"], bg=T["BG"], width=22,
                 anchor="w").pack(side=tk.LEFT, anchor="n", pady=(4, 0))
        right = tk.Frame(row, bg=T["BG"])
        right.pack(side=tk.LEFT, fill=tk.X, expand=True)
        make(right).pack(anchor="w")
        if hint:
            color = hint[1] if isinstance(hint, tuple) else T["TEXT3"]
            text = hint[0] if isinstance(hint, tuple) else hint
            tk.Label(right, text=text, font=F["small"], fg=color, bg=T["BG"],
                     justify=tk.LEFT).pack(anchor="w", pady=(4, 0))

    def _rows_control(self, parent):
        T, F = self.T, self.F
        spin = tk.Spinbox(parent, from_=1, to=MAX_LIMIT, width=4, font=F["body_b"],
                          justify="center", state="readonly", cursor="hand2",
                          bg=T["PANEL"], fg=T["TEXT"], readonlybackground=T["PANEL"],
                          buttonbackground=T["RAISED"], relief="flat", bd=0,
                          highlightthickness=1, highlightbackground=T["LINE"],
                          highlightcolor=T["GOLD"])
        spin.config(command=lambda: self._set_limit(spin.get()))
        spin.config(state="normal")
        spin.delete(0, tk.END)
        spin.insert(0, str(self._limit))
        spin.config(state="readonly")
        return spin

    def _set_limit(self, value):
        """Строк в списках: применится к следующему поиску и сразу к драфтам."""
        self._limit = self._clamp_limit(value)
        self._save_prefs()
        self._draft_changed(fetch=False)
        self._cm_changed(fetch=False)

    def _hotkey_control(self, parent):
        T, F = self.T, self.F
        choices = list(HOTKEY_PRESETS)
        if not any(parse_hotkey(c) == parse_hotkey(self._hotkey_text) for c in choices):
            choices.append(self._hotkey_text)   # своя, вписанная в конфиг руками
        current = next(c for c in choices if parse_hotkey(c) == parse_hotkey(self._hotkey_text))
        return Segmented(parent, T, F, [(c, format_hotkey(c)) for c in choices], current,
                         self._set_hotkey, font="small_b", padx=9)

    def _hotkey_hint(self):
        """Пояснение под клавишами: результат смены, своя клавиша или ничего."""
        tr, T = self.tr, self.T
        note, self._hotkey_note = self._hotkey_note, None   # сообщение о смене — один раз
        if note:
            return note
        if not any(parse_hotkey(c) == parse_hotkey(self._hotkey_text) for c in HOTKEY_PRESETS):
            return "%s — %s" % (format_hotkey(self._hotkey_text), tr["set_hotkey_custom"])
        if not self._hotkey_ok:
            return (tr["ov_key_busy"].format(key=format_hotkey(self._hotkey_text)), T["BAD"])
        return tr["set_hotkey_sub"]

    def _changelog(self, parent):
        """История изменений: номера версий — заголовками, пункты — абзацами."""
        T, F, tr = self.T, self.F, self.tr
        box = tk.Frame(parent, bg=T["BG"])
        box.pack(fill=tk.X, pady=(12, 0))
        shown = 0
        for block in tr["upd_text"].split("\n\n"):
            lines = [line for line in block.split("\n") if line.strip()]
            if not lines:
                continue
            shown += 1
            if shown > 4:
                break                      # последние четыре версии — хватит
            tk.Label(box, text=lines[0], font=F["body_b"], fg=T["GOLD"], bg=T["BG"]).pack(
                anchor="w", pady=(8, 2))
            for line in lines[1:]:
                tk.Label(box, text="— " + line, font=F["body"], fg=T["TEXT2"], bg=T["BG"],
                         justify=tk.LEFT, wraplength=820).pack(anchor="w", pady=(0, 3))

    def _clear_page_cache(self):
        """Удалить сохранённые страницы: следующий поиск скачает свежие."""
        removed = self._pages.clear()
        self._cache_label.config(text=self.tr["set_cache_cleared"].format(n=removed),
                                 fg=self.T["GOLD"])

    def _set_hotkey(self, text):
        """Сменить клавишу оверлея. Занятую другой программой не берём — остаётся прежняя."""
        if parse_hotkey(text) == parse_hotkey(self._hotkey_text):
            return
        tr, old = self.tr, self._hotkey_text
        toggle = lambda: self.root.after(0, self._overlay.toggle)  # noqa: E731
        self._hotkey.stop()
        new = GlobalHotkey(text, toggle)
        if new.start():
            self._hotkey, self._hotkey_text, self._hotkey_ok = new, text, True
            update_config(overlay_hotkey=text)
            self._hotkey_note = (tr["set_hotkey_ok"].format(key=format_hotkey(text)),
                                 self.T["GOLD"])
        else:
            self._hotkey = GlobalHotkey(old, toggle)
            self._hotkey_ok = self._hotkey.start()
            self._hotkey_note = (tr["set_hotkey_busy"].format(key=format_hotkey(text),
                                                              old=format_hotkey(old)),
                                 self.T["BAD"])
        self._rebuild()   # подпись у кнопки оверлея, кнопки здесь, подвал оверлея
