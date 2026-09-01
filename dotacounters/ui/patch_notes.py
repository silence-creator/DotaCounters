"""Модальное окно с заметками к текущему патчу и поиском по разделам."""

import threading
import tkinter as tk
from tkinter import ttk

from ..patches import fetch_patch_notes
from .winapi import set_title_bar_color


class PatchNotesModal(tk.Toplevel):
    def __init__(self, parent, theme: dict, tr: dict, patch_version: str):
        super().__init__(parent)
        self.T = theme
        self.tr = tr
        self.patch_version = patch_version

        self.title(tr["pn_window_title"].format(version=patch_version))
        self.configure(bg=theme["BG_DARK"])
        self.resizable(True, True)
        self.minsize(560, 500)
        self.geometry("720x760")
        self.transient(parent)
        self.grab_set()
        self._center(parent)
        set_title_bar_color(self)
        self._build()
        self.focus_set()

        # Запускаем загрузку в фоне
        threading.Thread(target=self._load_notes, daemon=True).start()

    def _center(self, parent):
        parent.update_idletasks()
        px = parent.winfo_x() + parent.winfo_width() // 2
        py = parent.winfo_y() + parent.winfo_height() // 2
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px - w // 2}+{py - h // 2}")

    def _build(self):
        T = self.T
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        # ── Заголовок ─────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=T["BG_DARK"])
        hdr.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 0))
        tk.Frame(hdr, bg=T["ACCENT"], width=4).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left = tk.Frame(hdr, bg=T["BG_DARK"])
        left.pack(side=tk.LEFT)
        tk.Label(left, text=f"PATCH  {self.patch_version}",
                 font=("Courier New", 18, "bold"),
                 fg=T["ACCENT"], bg=T["BG_DARK"]).pack(anchor="w")
        tk.Label(left, text=self.tr["pn_source"],
                 font=("Courier New", 9), fg=T["TEXT_DIM"], bg=T["BG_DARK"]).pack(anchor="w")

        close_btn = tk.Button(hdr, text="✕", font=("Courier New", 12, "bold"),
                              bg=T["BG_DARK"], fg=T["TEXT_DIM"],
                              activebackground=T["BG_DARK"], activeforeground=T["ACCENT2"],
                              relief="flat", bd=0, cursor="hand2", command=self.destroy)
        close_btn.pack(side=tk.RIGHT, padx=(0, 4))
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=T["ACCENT2"]))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=T["TEXT_DIM"]))

        tk.Frame(self, bg=T["BORDER"], height=1).grid(
            row=1, column=0, sticky="ew", padx=16, pady=(10, 0))

        # ── Поиск по заметкам ─────────────────────────────────────────────────
        sf = tk.Frame(self, bg=T["BG_DARK"])
        sf.grid(row=2, column=0, sticky="ew", padx=16, pady=(10, 6))
        sf.columnconfigure(0, weight=1)
        eb = tk.Frame(sf, bg=T["BORDER"], padx=1, pady=1)
        eb.grid(row=0, column=0, sticky="ew")
        ei = tk.Frame(eb, bg=T["BG_PANEL"])
        ei.pack(fill=tk.BOTH)
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search)
        self._filter_entry = tk.Entry(
            ei, textvariable=self._search_var,
            font=("Courier New", 11),
            bg=T["BG_PANEL"], fg=T["TEXT_PRIMARY"],
            insertbackground=T["ACCENT"],
            relief="flat", bd=5, highlightthickness=0)
        self._filter_entry.pack(fill=tk.X)
        self._filter_entry.bind("<FocusIn>",  self._search_focus_in)
        self._filter_entry.bind("<FocusOut>", self._search_focus_out)
        self._filter_entry.bind("<Escape>",   lambda e: self.destroy())
        self._ph_active = True
        self._set_ph()

        # ── Текстовая область ─────────────────────────────────────────────────
        wrap = tk.Frame(self, bg=T["BG_DARK"])
        wrap.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 0))
        wrap.columnconfigure(1, weight=1)
        wrap.rowconfigure(0, weight=1)

        tk.Frame(wrap, bg=T["ACCENT"], width=2).grid(row=0, column=0, sticky="ns")

        card = tk.Frame(wrap, bg=T["BG_CARD"],
                        highlightbackground=T["BORDER"], highlightthickness=1)
        card.grid(row=0, column=1, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=1)

        tf = tk.Frame(card, bg=T["BG_CARD"])
        tf.grid(row=0, column=0, sticky="nsew")
        tf.columnconfigure(0, weight=1)
        tf.rowconfigure(0, weight=1)

        self._text = tk.Text(
            tf, wrap=tk.WORD, font=("Courier New", 10),
            bg=T["BG_CARD"], fg=T["TEXT_PRIMARY"],
            insertbackground=T["ACCENT"],
            selectbackground=T["GLOW"],
            relief="flat", bd=0, padx=14, pady=10, spacing2=3,
            state=tk.DISABLED)
        self._text.grid(row=0, column=0, sticky="nsew")

        style = ttk.Style()
        style.configure("PN.Vertical.TScrollbar",
                        background=T["SCROLLBAR_BG"], troughcolor=T["SCROLLBAR_BG"],
                        bordercolor=T["SCROLLBAR_BG"], darkcolor=T["SCROLLBAR_BG"],
                        lightcolor=T["SCROLLBAR_BG"], arrowcolor=T["TEXT_DIM"],
                        relief="flat", borderwidth=0)
        style.map("PN.Vertical.TScrollbar",
                  background=[("active", T["BG_PANEL"]), ("disabled", T["SCROLLBAR_BG"])],
                  arrowcolor=[("active", T["ACCENT"])])

        sb = ttk.Scrollbar(tf, orient="vertical", style="PN.Vertical.TScrollbar",
                           command=self._text.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self._text.config(yscrollcommand=sb.set)
        self._text.bind("<MouseWheel>", lambda e: None)

        # Теги
        self._text.tag_config("section", foreground=T["ACCENT3"],
                               font=("Courier New", 10, "bold"))
        self._text.tag_config("divider", foreground=T["TEXT_MUTED"])
        self._text.tag_config("note",    foreground=T["TEXT_PRIMARY"])
        self._text.tag_config("loading", foreground=T["ACCENT3"])
        self._text.tag_config("error",   foreground=T["ACCENT2"],
                               font=("Courier New", 10, "bold"))
        self._text.tag_config("match",   foreground=T["ACCENT"],
                               font=("Courier New", 10, "bold"))

        # ── Статус-бар ────────────────────────────────────────────────────────
        self._status_lbl = tk.Label(
            self, text="", font=("Courier New", 8),
            fg=T["TEXT_MUTED"], bg=T["BG_DARK"])
        self._status_lbl.grid(row=4, column=0, sticky="w", padx=18, pady=(4, 8))

        # Показываем загрузку
        self._write_loading()

        # Храним все секции для фильтрации
        self._all_sections: list[dict] = []

    # ── Placeholder ───────────────────────────────────────────────────────────

    def _set_ph(self):
        ph = self.tr["pn_filter_ph"]
        self._filter_entry.delete(0, tk.END)
        self._filter_entry.insert(0, ph)
        self._filter_entry.config(fg=self.T["TEXT_DIM"])
        self._ph_active = True

    def _search_focus_in(self, event):
        if self._ph_active:
            self._filter_entry.delete(0, tk.END)
            self._filter_entry.config(fg=self.T["TEXT_PRIMARY"])
            self._ph_active = False

    def _search_focus_out(self, event):
        if not self._filter_entry.get():
            self._set_ph()

    # ── Загрузка ──────────────────────────────────────────────────────────────

    def _write_loading(self):
        self._text.config(state=tk.NORMAL)
        self._text.delete(1.0, tk.END)
        self._text.insert(
            tk.END, self.tr["pn_loading"].format(version=self.patch_version),
            "loading")
        self._text.config(state=tk.DISABLED)

    def _load_notes(self):
        tr = self.tr
        sections = fetch_patch_notes(
            self.patch_version,
            language=tr["api_language"],
            labels={"general": tr["pn_general"], "items": tr["pn_items"],
                    "neutral_items": tr["pn_neutral"]})
        self.after(0, self._apply_notes, sections)

    def _apply_notes(self, sections: list[dict]):
        self._all_sections = sections
        self._render_sections(sections)

    # ── Рендер ───────────────────────────────────────────────────────────────

    def _render_sections(self, sections: list[dict], query: str = ""):
        T = self.T
        txt = self._text
        txt.config(state=tk.NORMAL)
        txt.delete(1.0, tk.END)

        if not sections:
            txt.insert(tk.END, self.tr["pn_empty"], "error")
            txt.insert(
                tk.END,
                self.tr["pn_empty_hint"].format(version=self.patch_version), "note")
            self._status_lbl.config(text=self.tr["pn_status_empty"])
            txt.config(state=tk.DISABLED)
            return

        total_notes = 0
        for sec in sections:
            # Заголовок секции
            txt.insert(tk.END, "  " + "─" * 50 + "\n", "divider")
            txt.insert(tk.END, f"  ◈  {sec['title']}\n", "section")
            txt.insert(tk.END, "  " + "─" * 50 + "\n", "divider")
            for note in sec["notes"]:
                line = f"  ·  {note}\n"
                if query and query.lower() in note.lower():
                    txt.insert(tk.END, line, "match")
                else:
                    txt.insert(tk.END, line, "note")
                total_notes += 1
            txt.insert(tk.END, "\n")

        self._status_lbl.config(
            text=self.tr["pn_status"].format(sections=len(sections),
                                            notes=total_notes)
        )
        txt.config(state=tk.DISABLED)
        txt.yview_moveto(0)

    # ── Фильтр ────────────────────────────────────────────────────────────────

    def _on_search(self, *args):
        if self._ph_active or not self._all_sections:
            return
        query = self._search_var.get().strip()
        if not query:
            self._render_sections(self._all_sections)
            return
        filtered = []
        for sec in self._all_sections:
            matching = [n for n in sec["notes"] if query.lower() in n.lower()]
            # Также показываем секцию целиком если query совпадает с названием
            if query.lower() in sec["title"].lower():
                filtered.append(sec)
            elif matching:
                filtered.append({"title": sec["title"], "notes": matching})
        self._render_sections(filtered, query=query)
