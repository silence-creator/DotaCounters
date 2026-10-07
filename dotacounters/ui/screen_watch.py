"""Считывание драфта с экрана игры: выключатель, слежение и вопросы.

Примесь к DotaApp (app.py): методы работают с его состоянием через self.
Пока выключатель включён, раз в секунду в фоне делается снимок окна Dota
(capture.py) и читается то, что открыто сейчас: All Pick — во вкладке
«Драфт» или в оверлее в режиме All Pick, Captains Mode — во вкладке или в
оверлее в этом режиме. Что устоялось за несколько снимков (screen.Tracker),
переносится в общий состав; клетку, в которой программа не уверена,
она не заполняет, а спрашивает: три кандидата на один щелчок.

Портреты героев для сравнения грузятся при первом включении (с диска,
куда их уже скачал запуск программы), образцы подтверждённых клеток — из
cache/samples рядом с программой.
"""

import os
import threading
import tkinter as tk

from .. import capture, screen
from ..config import cache_dir, update_config
from ..heroes import ALL_HEROES
from ..icons import fetch_icons, portrait_url
from .hero_browser import HeroBrowserModal
from .widgets import button

#: Пауза между снимками, мс.
INTERVAL = 1000
#: Состояния под выключателем — ключи строк «scr_…».
STATES = ("loading", "portraits_failed", "missing", "minimized", "black", "idle", "no_draft",
          "watching", "side_unknown", "conflict", "error")
#: Портретов должно загрузиться хотя бы столько (доля), иначе сравнивать не с чем.
MIN_PORTRAITS = 0.9
#: Сторону и первый ход Captains Mode экран меняет, только если столько
#: снимков подряд согласны.
SIDE_AGREE = 3


class ScreenWatch:

    def _init_screen(self, cfg):
        self._watch_on = False
        self._watch_busy = False
        self._watch_job = None
        self._reader = None
        self._reader_lock = threading.Lock()
        self._trackers = {"allpick": screen.Tracker(), "captains": screen.Tracker()}
        self._screen_applied = {}      # All Pick: клетка -> перенесённый герой
        self._screen_ours = None       # All Pick: наша сторона по последнему снимку
        self._screen_votes = {}        # «first»/«ours» -> (значение, снимков подряд)
        self._screen_state = ("idle", {})
        self._screen_unsure = []       # [(режим, клетка, Cell)]
        self._screen_cells = {}        # режим -> клетки последнего снимка
        self._screen_panels = []       # (рамка, ширина переноса)
        self._screen_shown = None      # что сейчас нарисовано в панелях
        if cfg.get("screen_watch") is True:
            self.root.after(500, lambda: self._set_watch(True))

    def _samples_dir(self):
        folder = cache_dir()
        return os.path.join(folder, "samples") if folder else None

    # ── Выключатель ───────────────────────────────────────────────────────────

    def _set_watch(self, on):
        self._watch_on = on
        update_config(screen_watch=on)
        self._overlay.exclude_from_capture(on)
        if self._watch_job is not None:
            self.root.after_cancel(self._watch_job)
            self._watch_job = None
        for tracker in self._trackers.values():
            tracker.reset()
        self._screen_unsure = []
        self._screen_state = ("idle", {})
        if on:
            self._watch_tick()
        self._render_screen_panels()

    def _watch_mode(self):
        """Какой драфт читать: тот, что открыт в оверлее или во вкладке."""
        overlay = self._overlay
        if overlay.visible and overlay.mode in ("draft", "cm"):
            return "allpick" if overlay.mode == "draft" else "captains"
        return {"draft": "allpick", "cm": "captains"}.get(self._active_tab)

    def _watch_tick(self):
        self._watch_job = None
        if not self._watch_on:
            return
        mode = self._watch_mode()
        if mode is None:
            self._set_screen_state("idle")
        elif not self._watch_busy:
            self._watch_busy = True
            threading.Thread(target=self._watch_work, args=(mode, self._cm.first),
                             daemon=True).start()
        self._watch_job = self.root.after(INTERVAL, self._watch_tick)

    # ── Фон: снимок и чтение ──────────────────────────────────────────────────

    def _ensure_reader(self):
        if self._reader is not None:
            return self._reader
        self.root.after(0, self._set_screen_state, "loading")
        urls = {hero: portrait_url(hero) for hero in ALL_HEROES}
        images = fetch_icons([u for u in urls.values() if u], box=(256, 144), workers=6)
        portraits = {hero: images[url] for hero, url in urls.items() if url in images}
        if len(portraits) < MIN_PORTRAITS * len(ALL_HEROES):
            return None
        samples = screen.load_samples(self._samples_dir(), portraits)
        self._reader = screen.Reader(screen.Matcher(portraits, samples))
        return self._reader

    def _watch_work(self, mode, first):
        try:
            reader = self._ensure_reader()
            if reader is None:
                result = ("portraits_failed", None)
            else:
                shot = capture.grab()
                if shot.status != "ok":
                    result = (shot.status, None)
                else:
                    with self._reader_lock:
                        if mode == "allpick":
                            reading = reader.read_allpick(shot.image)
                        else:
                            reading = reader.read_captains(shot.image, first)
                    result = ("ok", reading)
        except Exception as exc:          # снимок, разбор — показать словами, не падать
            result = ("error", str(exc))
        try:
            self.root.after(0, self._watch_done, mode, result)
        except RuntimeError:
            pass                          # окно уже закрыто

    # ── Итог снимка ───────────────────────────────────────────────────────────

    def _watch_done(self, mode, result):
        self._watch_busy = False
        if not self._watch_on or mode != self._watch_mode():
            return
        status, reading = result
        if status == "error":
            self._set_screen_state("error", detail=reading)
            return
        if status != "ok":
            self._screen_unsure = []
            self._set_screen_state(status)
            return
        if not reading.present:
            self._screen_unsure = []
            self._set_screen_state("no_draft")
            return
        stable = self._trackers[mode].update(reading)
        self._screen_cells[mode] = reading.cells
        if mode == "allpick":
            self._screen_allpick(reading, stable)
        else:
            self._screen_captains(reading, stable)

    def _screen_allpick(self, reading, stable):
        if reading.ours:
            self._screen_ours = reading.ours
        done, gone = screen.apply_allpick(self._board, stable, self._screen_ours,
                                          self._screen_applied)
        self._screen_unsure = [("allpick", i, reading.cells[i]) for i, v in sorted(stable.items())
                               if v == "?"]
        if self._screen_ours is None:
            self._set_screen_state("side_unknown")
        else:
            seen = sum(1 for v in stable.values() if v and v != "?")
            self._set_screen_state("watching", n=seen)
        if done or gone:
            self._draft_changed()

    def _vote(self, key, value):
        """Значение, которое SIDE_AGREE снимков подряд одно и то же, иначе None."""
        if value is None:
            self._screen_votes.pop(key, None)
            return None
        old, count = self._screen_votes.get(key, (None, 0))
        count = count + 1 if old == value else 1
        self._screen_votes[key] = (value, count)
        return value if count >= SIDE_AGREE else None

    def _screen_captains(self, reading, stable):
        cm = self._cm
        changed = False
        first, ours = self._vote("first", reading.first), self._vote("ours", reading.ours)
        if first and first != cm.first:
            cm.first, changed = first, True
        if ours and ours != cm.ours:
            cm.ours, changed = ours, True
        played, undone, conflict = screen.apply_captains(cm, stable)
        current = cm.current
        self._screen_unsure = []
        if current is not None and stable.get(current) == "?":
            self._screen_unsure = [("captains", current, reading.cells[current])]
        if conflict is not None:
            self._set_screen_state("conflict", n=conflict + 1, screen=stable[conflict],
                                   model=cm.heroes[conflict])
        else:
            done = len(cm.heroes) if current is None else current
            self._set_screen_state("watching", n=sum(1 for h in cm.heroes[:done] if h))
        if played or undone or changed:
            if played:
                self._cm_finished()
            self._cm_changed()

    def _screen_reset(self, mode):
        """Состав очищен руками: экран перенесёт заново то, что показывает."""
        self._trackers[mode].reset()
        if mode == "allpick":
            self._screen_applied.clear()

    # ── Ответ пользователя ────────────────────────────────────────────────────

    def _screen_confirm(self, mode, key, hero):
        """Пользователь выбрал героя для клетки под вопросом: записать и запомнить
        клетку как образец этого героя."""
        cells = self._screen_cells.get(mode) or []
        cell = cells[key] if key < len(cells) else None
        if cell is not None and cell.image is not None and self._reader is not None:
            screen.save_sample(self._samples_dir(), cell.kind, hero, cell.image)
            with self._reader_lock:
                self._reader.matcher.add_sample(cell.kind, hero, cell.image)
        self._screen_unsure = [u for u in self._screen_unsure if (u[0], u[1]) != (mode, key)]
        if mode == "allpick":
            if self._screen_ours is not None:
                side = "radiant" if key < 5 else "dire"
                group = "allies" if side == self._screen_ours else "enemies"
                if self._board.add(group, hero) in ("added", "moved", "dup"):
                    self._screen_applied[key] = hero
                self._draft_changed()
        elif key == self._cm.current and self._cm.play(hero) == "ok":
            self._cm_finished()
            self._cm_changed()
        self._render_screen_panels()

    # ── Панель под выключателем ───────────────────────────────────────────────

    def _set_screen_state(self, state, **args):
        self._screen_state = (state, args)
        self._render_screen_panels()

    def _screen_panel(self, parent, wrap=300):
        """Выключатель «Читать с экрана», состояние и вопросы — для вкладок и оверлея.
        Рамку размещает вызывающий."""
        frame = tk.Frame(parent, bg=self.T["BG"])
        self._screen_panels = [(f, w) for f, w in self._screen_panels if f.winfo_exists()]
        self._screen_panels.append((frame, wrap))
        self._fill_screen_panel(frame, wrap)
        return frame

    def _screen_signature(self):
        unsure = tuple((m, k, tuple(h for _, h in c.candidates)) for m, k, c in self._screen_unsure)
        state, args = self._screen_state
        return (self._watch_on, state, tuple(sorted(args.items())), unsure)

    def _render_screen_panels(self, force=False):
        signature = self._screen_signature()
        if signature == self._screen_shown and not force:
            return
        self._screen_shown = signature
        alive = []
        for frame, wrap in self._screen_panels:
            try:
                if not frame.winfo_exists():
                    continue
                for w in frame.winfo_children():
                    w.destroy()
                self._fill_screen_panel(frame, wrap)
                alive.append((frame, wrap))
            except tk.TclError:
                continue
        self._screen_panels = alive

    def _fill_screen_panel(self, frame, wrap):
        T, tr, F = self.T, self.tr, self.F
        line = tk.Frame(frame, bg=T["BG"])
        line.pack(fill=tk.X)
        if self._watch_on:
            text, kind = tr["scr_on"], "primary"
        else:
            text, kind = tr["scr_off"], "ghost"
        button(line, T, F, text, lambda: self._set_watch(not self._watch_on), kind=kind,
               font="small_b", padx=10, pady=3).pack(side=tk.LEFT)
        if not self._watch_on:
            tk.Label(frame, text=tr["scr_hint"], font=F["tiny"], fg=T["TEXT3"], bg=T["BG"],
                     justify=tk.LEFT, wraplength=wrap).pack(anchor="w", pady=(4, 0))
            return
        state, args = self._screen_state
        color = {"watching": T["GOOD"], "loading": T["GOLD"], "idle": T["TEXT3"],
                 "no_draft": T["TEXT3"]}.get(state, T["BAD"])
        tk.Label(frame, text=tr["scr_" + state].format(**args), font=F["small"], fg=color,
                 bg=T["BG"], justify=tk.LEFT, wraplength=wrap).pack(anchor="w", pady=(4, 0))
        for mode, key, cell in self._screen_unsure:
            self._unsure_row(frame, mode, key, cell, wrap)

    def _unsure_row(self, parent, mode, key, cell, wrap):
        """«Dire 3 — кто это?» и три кандидата портретами; «другой…» — список героев."""
        T, tr, F = self.T, self.tr, self.F
        box = tk.Frame(parent, bg=T["PANEL"], highlightthickness=1, highlightbackground=T["GOLD"])
        box.pack(fill=tk.X, pady=(6, 0))
        if mode == "allpick":
            side = "radiant" if key < 5 else "dire"
            question = tr["scr_ask_slot"].format(side=tr["side_" + side], n=key % 5 + 1)
        else:
            question = tr["scr_ask_move"].format(n=key + 1)
        tk.Label(box, text=question, font=F["small_b"], fg=T["GOLD"], bg=T["PANEL"],
                 wraplength=wrap).pack(anchor="w", padx=8, pady=(6, 4))
        row = tk.Frame(box, bg=T["PANEL"])
        row.pack(fill=tk.X, padx=8, pady=(0, 6))
        pick = lambda hero: self._screen_confirm(mode, key, hero)  # noqa: E731
        for _, hero in cell.candidates[:3]:
            item = tk.Frame(row, bg=T["PANEL"], cursor="hand2")
            item.pack(side=tk.LEFT, padx=(0, 6))
            photo = tk.Label(item, image=self.photo(hero, (48, 27)), bg=T["PANEL"], cursor="hand2")
            photo.pack()
            name = tk.Label(item, text=hero, font=F["tiny"], fg=T["TEXT2"], bg=T["PANEL"],
                            cursor="hand2", wraplength=64)
            name.pack()
            for w in (item, photo, name):
                w.bind("<Button-1>", lambda e, h=hero: pick(h))
        button(row, T, F, tr["scr_other"], lambda: HeroBrowserModal(
            self.root, T, tr, on_select=pick, fonts=F), kind="link", font="small_b",
            bg=T["PANEL"]).pack(side=tk.LEFT, anchor="n")
