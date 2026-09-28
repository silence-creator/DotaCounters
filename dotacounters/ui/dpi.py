"""Чёткий текст при масштабе Windows 125–200%.

Программа, не объявившая Windows, что умеет в DPI, рисуется как при 100%, и
система растягивает готовую картинку — весь текст мыльный. Поэтому процесс
объявляется DPI-aware (`enable`, до создания окна Tk). Тогда Windows отдаёт
настоящие пиксели: шрифты Tk в пунктах увеличиваются сами, а размеры в
пикселях — отступы, рамки, ширина панелей, портреты — остались бы мелкими.

Их масштабирует `install`: Tk получает параметры виджетов, pack, grid и тегов
текста через `Misc._options`, и там целые пиксельные значения умножаются на
масштаб. Код интерфейса по-прежнему пишет размеры как при 100%. Размеры окон
(`geometry`, `minsize`) и картинок масштабируются явно — через `px`/`px_size`.

Не трогаются:
- ширина и высота текстовых виджетов (Label без картинки, Entry, Spinbox,
  Text) — они в символах и растут вместе со шрифтом;
- `place(...)` и элементы Canvas — туда передают настоящие пиксели из winfo_*
  и событий.
"""

import ctypes
import tkinter as tk

#: Во сколько раз экранный пиксель мельче пикселя макета (96 dpi). 1.0 — без масштаба.
SCALE = 1.0

# Параметры в пикселях — у любого виджета, в pack, grid, columnconfigure и тегах Text
_ALWAYS = frozenset((
    "padx", "pady", "ipadx", "ipady", "wraplength", "minsize",
    "highlightthickness", "borderwidth", "bd", "insertwidth", "selectborderwidth",
    "spacing1", "spacing2", "spacing3", "lmargin1", "lmargin2", "rmargin",
))
# width/height в пикселях — у контейнеров всегда, у Label/Button — если есть картинка
_BOX_WIDGETS = frozenset(("frame", "canvas", "toplevel", "labelframe", "ttk::frame"))
_IMAGE_WIDGETS = frozenset(("label", "button", "menubutton"))
_state = {"installed": False, "raw": 0}


def enable():
    """Объявить процесс DPI-aware. До создания tk.Tk(); вне Windows — ничего."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)      # system aware, Windows 8.1+
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()       # Windows 7
        except (AttributeError, OSError):
            pass


def px(value):
    """Пиксели макета -> экранные. Кортежи (отступы «сверху, снизу») — поэлементно."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return int(round(value * SCALE)) if value > 0 else value
    if isinstance(value, tuple) and all(isinstance(v, int) and not isinstance(v, bool)
                                        for v in value):
        return tuple(px(v) for v in value)
    return value


def px_size(size):
    """(ширина, высота) в экранных пикселях."""
    return (px(size[0]), px(size[1]))


def _scaled(widget, cnf):
    """Копия словаря параметров с пиксельными значениями в экранных пикселях."""
    name = getattr(widget, "widgetName", "")
    boxy = name in _BOX_WIDGETS
    if not boxy and name in _IMAGE_WIDGETS and ("width" in cnf or "height" in cnf):
        if "image" in cnf:
            boxy = bool(cnf["image"])
        else:
            try:
                boxy = bool(widget.cget("image"))
            except tk.TclError:
                boxy = False
    out = {}
    for key, value in cnf.items():
        if key in _ALWAYS or (boxy and key in ("width", "height")):
            value = px(value)
        out[key] = value
    return out


def _raw(method):
    """Обёртка: внутри вызова параметры передаются как есть."""
    def wrapper(*args, **kwargs):
        _state["raw"] += 1
        try:
            return method(*args, **kwargs)
        finally:
            _state["raw"] -= 1
    return wrapper


def install(root):
    """Узнать масштаб по окну и включить пересчёт пикселей. Повторный вызов — ничего."""
    global SCALE
    if _state["installed"]:
        return SCALE
    _state["installed"] = True
    try:
        SCALE = max(1.0, root.winfo_fpixels("1i") / 96.0)
    except tk.TclError:
        SCALE = 1.0
    if SCALE == 1.0:
        return SCALE

    original = tk.Misc._options

    def _options(self, cnf, kw=None):
        if not _state["raw"]:
            merged = tk._cnfmerge((cnf, kw)) if kw else (tk._cnfmerge(cnf) if cnf else cnf)
            if merged:
                return original(self, _scaled(self, merged))
        return original(self, cnf, kw)

    tk.Misc._options = _options
    tk.Place.place_configure = tk.Place.place = _raw(tk.Place.place_configure)
    tk.Canvas._create = _raw(tk.Canvas._create)
    tk.Canvas.itemconfigure = tk.Canvas.itemconfig = _raw(tk.Canvas.itemconfigure)
    return SCALE
