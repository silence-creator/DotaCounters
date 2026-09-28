"""Цветовые схемы интерфейса.

Каждая тема — плоский словарь токенов; виджеты читают цвета как T["GOLD"].
Ключи name_en/name_ru — подпись в настройках.

С 2.0 темы две: «Графит» (по макету нового интерфейса) и светлая. Золото —
только для хода, фокуса и активного; «выгодно» — синим, «опасно» —
оранжевым: пара различима и при дальтонизме, в отличие от красного с
зелёным. Цвета Radiant и Dire — только для подписей сторон.

Старые ключи (BG_DARK, ACCENT…) оставлены: ими пользуются окна списка
героев, патчноутов и подсказки ввода.
"""

_GRAPHITE = {
    "name_en": "Graphite",
    "name_ru": "Графит",
    "BG":        "#111317",   # фон окна
    "TOPBAR":    "#15181c",   # шапка, доска Captains Mode
    "PANEL":     "#181b20",   # карточки, поля ввода
    "RAISED":    "#20242b",   # кнопки второго плана
    "SELECTED":  "#2a2e35",   # выбранный сегмент, наведение
    "LINE":      "#2b3038",   # рамки
    "LINE_SOFT": "#23272e",   # разделители строк
    "TEXT":      "#ebe6da",
    "TEXT2":     "#a8a398",
    "TEXT3":     "#8a867d",
    "TEXT4":     "#6f6c66",   # совсем второстепенное: будущие ходы
    "GOLD":      "#d6a652",
    "GOLD_BG":   "#2a2619",   # подложка под выбранной «фишкой» и текущим ходом
    "ON_GOLD":   "#16140f",   # текст на золотой кнопке
    "GOOD":      "#62b0d9",
    "BAD":       "#e38b4f",
    "RADIANT":   "#8fbf6a",
    "DIRE":      "#d46a55",
    "SLOT":      "#0c0e11",   # пустая клетка доски
}

_LIGHT = {
    "name_en": "Light",
    "name_ru": "Светлая",
    "BG":        "#f3f0e8",
    "TOPBAR":    "#e9e5dc",
    "PANEL":     "#fbfaf6",
    "RAISED":    "#e6e1d6",
    "SELECTED":  "#dcd6c9",
    "LINE":      "#cfc9bc",
    "LINE_SOFT": "#e2ddd2",
    "TEXT":      "#1d1b17",
    "TEXT2":     "#4f4b43",
    "TEXT3":     "#655f55",
    "TEXT4":     "#827c71",
    "GOLD":      "#865a14",
    "GOLD_BG":   "#f1e3c4",
    "ON_GOLD":   "#ffffff",
    "GOOD":      "#1f6a93",
    "BAD":       "#a24c17",
    "RADIANT":   "#416b29",
    "DIRE":      "#ad3d2a",
    "SLOT":      "#e6e1d6",
}


def _with_legacy(t: dict) -> dict:
    """Добавить старые имена токенов, которыми пользуются модальные окна."""
    t = dict(t)
    t.update({
        "BG_DARK": t["BG"], "BG_CARD": t["PANEL"], "BG_PANEL": t["RAISED"],
        "BORDER": t["LINE"], "ACCENT": t["GOLD"], "ACCENT2": t["BAD"], "ACCENT3": t["GOLD"],
        "TEXT_PRIMARY": t["TEXT"], "TEXT_DIM": t["TEXT2"], "TEXT_MUTED": t["TEXT3"],
        "SCROLLBAR_BG": t["TOPBAR"], "GLOW": t["SELECTED"],
    })
    return t


THEMES = {"graphite": _with_legacy(_GRAPHITE), "light": _with_legacy(_LIGHT)}
DEFAULT_THEME = "graphite"

#: Темы до 2.0: светлая «Призрак» стала светлой, неоновые — «Графитом».
_LEGACY = {"ghost": "light"}


def theme_key(value) -> str:
    """Тема из конфига -> существующая. Старые и испорченные значения приводятся."""
    if value in THEMES:
        return value
    return _LEGACY.get(value, DEFAULT_THEME)
