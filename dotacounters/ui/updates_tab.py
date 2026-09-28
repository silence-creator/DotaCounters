"""Обновления: плашка о новой версии под шапкой, проверка и установка.

Примесь к DotaApp (app.py): методы работают с его состоянием через self.
История изменений и кнопка ручной проверки — в «Настройках» (settings_tab).
"""

import os
import threading
import tkinter as tk
import webbrowser
from datetime import date

from .. import relaunch, updates
from ..config import load_config, update_config
from ..version import APP_VERSION
from .widgets import button


class UpdatesTab:

    def _build_update_banner(self, parent):
        """Полоса под шапкой. Пустая и скрытая, пока обновления нет."""
        T, F = self.T, self.F
        self._banner = tk.Frame(parent, bg=T["GOLD_BG"], highlightthickness=1,
                                highlightbackground=T["GOLD"])
        self._banner.grid(row=1, column=0, sticky="ew", padx=24, pady=(14, 0))
        self._banner.grid_remove()
        self._banner_label = tk.Label(self._banner, text="", font=F["body_b"], fg=T["TEXT"],
                                      bg=T["GOLD_BG"])
        self._banner_label.pack(side=tk.LEFT, padx=14, pady=10)
        self._banner_buttons = tk.Frame(self._banner, bg=T["GOLD_BG"])
        self._banner_buttons.pack(side=tk.RIGHT, padx=10, pady=6)
        if getattr(self, "_update", None):
            self._show_update(self._update)

    def _start_update_check(self, manual=False):
        """Проверка раз в сутки; по кнопке — всегда."""
        if not manual:
            today = date.today().isoformat()
            if load_config().get("last_update_check") == today:
                return
            update_config(last_update_check=today)
        if manual:
            self._set_update_status(self.tr["upd_checking"])
        threading.Thread(target=self._check_updates, args=(manual,), daemon=True).start()

    def _check_updates(self, manual):
        found = updates.check()
        self.root.after(0, self._apply_update_check, found, manual)

    def _apply_update_check(self, found, manual):
        self._update = found
        if found:
            self._show_update(found)
            self._set_update_status(self.tr["upd_available"].format(version=found.version))
        elif manual:
            self._set_update_status(self.tr["upd_uptodate"].format(version=APP_VERSION))

    def _set_update_status(self, text):
        label = getattr(self, "_update_status", None)
        if label is not None:
            try:
                label.config(text=text)
            except tk.TclError:
                pass  # вкладку пересобрали

    def _show_update(self, update):
        T, F, tr = self.T, self.F, self.tr
        self._banner_label.config(text=tr["upd_available"].format(version=update.version),
                                  fg=T["TEXT"])
        for w in self._banner_buttons.winfo_children():
            w.destroy()
        self._update_btn = None
        if updates.can_install():
            self._update_btn = button(self._banner_buttons, T, F, tr["upd_install_btn"],
                                      self._install_update, kind="primary")
            self._update_btn.pack(side=tk.LEFT, padx=4)
        button(self._banner_buttons, T, F, tr["upd_page_btn"],
               lambda: webbrowser.open(update.page)).pack(side=tk.LEFT, padx=4)
        button(self._banner_buttons, T, F, "×", self._hide_update, kind="link", font="h2",
               bg=T["GOLD_BG"]).pack(side=tk.LEFT, padx=(4, 0))
        self._banner.grid()

    def _hide_update(self):
        self._banner.grid_remove()

    def _install_update(self):
        """Скачать, сверить сумму, заменить файл и перезапуститься."""
        if self._update_btn:
            self._update_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._run_install, daemon=True).start()

    def _run_install(self):
        update = self._update
        exe = updates.current_exe()
        target = exe + ".new"
        try:
            def progress(received, total):
                if total:
                    self.root.after(0, self._banner_label.config, {
                        "text": self.tr["upd_downloading"].format(
                            percent=min(100, int(100 * received / total)))})
            updates.download(update, target, progress=progress)
            self.root.after(0, self._banner_label.config,
                            {"text": self.tr["upd_installing"]})
            updates.install(target, exe)
        except Exception as exc:
            try:
                os.unlink(target)
            except OSError:
                pass
            self.root.after(0, self._update_failed, exc)
            return
        self.root.after(0, self._restart_after_update, exe)

    def _update_failed(self, exc):
        self._banner_label.config(text=self.tr["upd_error"].format(detail=exc),
                                  fg=self.T["BAD"])
        if self._update_btn:
            self._update_btn.config(state=tk.NORMAL)

    def _restart_after_update(self, exe):
        self._banner_label.config(text=self.tr["upd_restart"])
        self.root.update_idletasks()
        relaunch.launch(exe)
        self.root.destroy()
