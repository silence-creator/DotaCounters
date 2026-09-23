"""Модальное окно со списком всех героев и живым поиском."""

import tkinter as tk
from tkinter import ttk

from ..heroes import ALL_HEROES
from .winapi import set_title_bar_color


class HeroBrowserModal(tk.Toplevel):
    def __init__(self, parent, theme: dict, tr: dict, on_select=None):
        super().__init__(parent)
        self.T = theme
        self.tr = tr
        self.on_select = on_select

        self.title(tr["hb_title"])
        self.configure(bg=self.T["BG_DARK"])
        self.resizable(True, True)
        self.minsize(520, 560)
        self.geometry("620x660")
        self.transient(parent)
        self.grab_set()
        self._center(parent)
        set_title_bar_color(self)
        self._build()
        self.focus_set()

    def _center(self, parent):
        parent.update_idletasks()
        px = parent.winfo_x() + parent.winfo_width() // 2
        py = parent.winfo_y() + parent.winfo_height() // 2
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px - w // 2}+{py - h // 2}")

    def _build(self):
        T, tr = self.T, self.tr
        self.columnconfigure(0, weight=1)

        # Header
        hdr = tk.Frame(self, bg=T["BG_DARK"])
        hdr.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 0))
        tk.Frame(hdr, bg=T["ACCENT"], width=4).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left = tk.Frame(hdr, bg=T["BG_DARK"])
        left.pack(side=tk.LEFT)
        tk.Label(left, text=tr["hb_title"],
                 font=("Courier New", 18, "bold"),
                 fg=T["ACCENT"], bg=T["BG_DARK"]).pack(anchor="w")
        tk.Label(left, text=f"  {len(ALL_HEROES)} {tr['hb_sorted']}",
                 font=("Courier New", 9), fg=T["TEXT_DIM"], bg=T["BG_DARK"]).pack(anchor="w")

        close_btn = tk.Button(hdr, text="✕", font=("Courier New", 12, "bold"),
                              bg=T["BG_DARK"], fg=T["TEXT_DIM"],
                              activebackground=T["BG_DARK"], activeforeground=T["ACCENT2"],
                              relief="flat", bd=0, cursor="hand2", command=self.destroy)
        close_btn.pack(side=tk.RIGHT, padx=(0, 4))
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=T["ACCENT2"]))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=T["TEXT_DIM"]))

        tk.Frame(self, bg=T["BORDER"], height=1).grid(row=1, column=0, sticky="ew", padx=16, pady=(10, 0))

        # Search
        sf = tk.Frame(self, bg=T["BG_DARK"])
        sf.grid(row=2, column=0, sticky="ew", padx=16, pady=(10, 6))
        sf.columnconfigure(0, weight=1)
        eb = tk.Frame(sf, bg=T["BORDER"], padx=1, pady=1)
        eb.grid(row=0, column=0, sticky="ew")
        ei = tk.Frame(eb, bg=T["BG_PANEL"])
        ei.pack(fill=tk.BOTH)
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search)
        self._filter_entry = tk.Entry(ei, textvariable=self._search_var,
                                      font=("Courier New", 11),
                                      bg=T["BG_PANEL"], fg=T["TEXT_PRIMARY"],
                                      insertbackground=T["ACCENT"],
                                      relief="flat", bd=5, highlightthickness=0)
        self._filter_entry.pack(fill=tk.X)
        self._filter_entry.bind("<FocusIn>",  self._search_focus_in)
        self._filter_entry.bind("<FocusOut>", self._search_focus_out)
        self._filter_entry.bind("<Escape>",   lambda e: self.destroy())
        self._search_placeholder = True
        self._set_search_placeholder()

        # List
        lf = tk.Frame(self, bg=T["BG_DARK"])
        lf.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 14))
        self.rowconfigure(3, weight=1)
        lf.columnconfigure(0, weight=1)
        lf.rowconfigure(0, weight=1)
        card = tk.Frame(lf, bg=T["BG_CARD"], highlightbackground=T["BORDER"], highlightthickness=1)
        card.grid(row=0, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure("HB.Vertical.TScrollbar",
                        background=T["SCROLLBAR_BG"], troughcolor=T["SCROLLBAR_BG"],
                        bordercolor=T["SCROLLBAR_BG"], darkcolor=T["SCROLLBAR_BG"],
                        lightcolor=T["SCROLLBAR_BG"], arrowcolor=T["TEXT_DIM"],
                        relief="flat", borderwidth=0)
        style.map("HB.Vertical.TScrollbar",
                  background=[("active", T["BG_PANEL"]), ("disabled", T["SCROLLBAR_BG"])],
                  arrowcolor=[("active", T["ACCENT"])])

        self._canvas = tk.Canvas(card, bg=T["BG_CARD"], bd=0, highlightthickness=0)
        self._canvas.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(card, orient="vertical", style="HB.Vertical.TScrollbar",
                           command=self._canvas.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self._canvas.configure(yscrollcommand=sb.set)
        self._inner = tk.Frame(self._canvas, bg=T["BG_CARD"])
        self._canvas_window = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._inner.bind("<Configure>", lambda e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(
            self._canvas_window, width=e.width))
        # Колесо привязано к самому окну, а не к полотну: в Tk событие идёт по
        # цепочке «виджет → его класс → окно верхнего уровня», а не по
        # вложенности. Над карточкой героя полотно событие не получало, и
        # прокрутка работала только в промежутках между карточками.
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.bind(seq, self._on_mousewheel)

        self._count_label = tk.Label(self, text=f"{tr['hb_showing']} {len(ALL_HEROES)} {tr['hb_heroes']}",
                                     font=("Courier New", 8), fg=T["TEXT_MUTED"], bg=T["BG_DARK"])
        self._count_label.grid(row=4, column=0, sticky="w", padx=18, pady=(0, 6))
        self._render_heroes(ALL_HEROES)

    def _set_search_placeholder(self):
        self._filter_entry.delete(0, tk.END)
        self._filter_entry.insert(0, self.tr["hb_search_ph"])
        self._filter_entry.config(fg=self.T["TEXT_DIM"])
        self._search_placeholder = True

    def _search_focus_in(self, event):
        if self._search_placeholder:
            self._filter_entry.delete(0, tk.END)
            self._filter_entry.config(fg=self.T["TEXT_PRIMARY"])
            self._search_placeholder = False

    def _search_focus_out(self, event):
        if not self._filter_entry.get():
            self._set_search_placeholder()

    def _on_search(self, *args):
        if self._search_placeholder:
            return
        query = self._search_var.get().strip().lower()
        filtered = [h for h in ALL_HEROES if query in h.lower()] if query else ALL_HEROES
        self._render_heroes(filtered)
        tr = self.tr
        self._count_label.config(
            text=f"{tr['hb_showing']} {len(filtered)} {tr['hb_of']} {len(ALL_HEROES)} {tr['hb_heroes']}"
        )

    def _render_heroes(self, heroes):
        T, tr = self.T, self.tr
        for w in self._inner.winfo_children():
            w.destroy()
        if not heroes:
            tk.Label(self._inner, text=tr["hb_no_match"],
                     font=("Courier New", 10), fg=T["TEXT_DIM"],
                     bg=T["BG_CARD"]).pack(anchor="w", padx=14)
            self._canvas.yview_moveto(0)
            return
        groups: dict[str, list[str]] = {}
        for hero in heroes:
            groups.setdefault(hero[0].upper(), []).append(hero)
        COLS = 3
        for letter in sorted(groups.keys()):
            lf = tk.Frame(self._inner, bg=T["BG_CARD"])
            lf.pack(fill=tk.X, padx=10, pady=(10, 2))
            tk.Label(lf, text=f" {letter} ", font=("Courier New", 10, "bold"),
                     fg=T["ACCENT3"], bg=T["BG_PANEL"], padx=6, pady=1).pack(side=tk.LEFT)
            tk.Frame(lf, bg=T["BORDER"], height=1).pack(
                side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0), pady=6)
            gf = tk.Frame(self._inner, bg=T["BG_CARD"])
            gf.pack(fill=tk.X, padx=10, pady=(0, 4))
            for i, hero in enumerate(groups[letter]):
                btn = tk.Button(gf, text=hero, font=("Courier New", 10),
                                bg=T["BG_PANEL"], fg=T["TEXT_PRIMARY"],
                                activebackground=T["GLOW"], activeforeground=T["ACCENT"],
                                relief="flat", bd=0, padx=10, pady=5, anchor="w",
                                cursor="hand2", command=lambda h=hero: self._select_hero(h))
                btn.grid(row=i // COLS, column=i % COLS, sticky="ew", padx=2, pady=1)
                btn.bind("<Enter>", lambda e, b=btn: b.config(fg=T["ACCENT"], bg=T["GLOW"]))
                btn.bind("<Leave>", lambda e, b=btn: b.config(fg=T["TEXT_PRIMARY"], bg=T["BG_PANEL"]))
            for c in range(COLS):
                gf.columnconfigure(c, weight=1, uniform="hcol")
        self._canvas.update_idletasks()
        self._canvas.yview_moveto(0)

    def _select_hero(self, hero_name):
        if self.on_select:
            self.on_select(hero_name)
        self.destroy()

    def _on_mousewheel(self, event):
        if event.num == 4:
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self._canvas.yview_scroll(1, "units")
        else:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
