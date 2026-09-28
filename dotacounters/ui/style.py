"""Шрифты интерфейса.

Весь текст — Bahnschrift: узкий «инженерный» шрифт, близкий к шрифтам самой
Dota. Есть в Windows 10 (1709) и новее; где его нет — Segoe UI. Мелкий текст
тоже Bahnschrift: с Segoe UI подписи выглядели безлико, как в любом
сгенерированном интерфейсе.

Размеры — в пунктах Tk; в скобках — пиксели макета при 96 dpi.
"""

from tkinter import font as tkfont

_FALLBACK = ("Segoe UI", "Segoe UI Semibold")


def _families(root):
    names = set(tkfont.families(root))
    if "Bahnschrift" in names and "Bahnschrift SemiBold" in names:
        return "Bahnschrift", "Bahnschrift SemiBold"
    return _FALLBACK


def make_fonts(root) -> dict:
    """Набор шрифтов по ролям. Вызывать после создания окна Tk."""
    text, semi = _families(root)
    return {
        "brand":  (semi, 14),    # название программы (18)
        "tab":    (semi, 11),    # вкладки (15)
        "h1":     (semi, 21),    # имя героя (28)
        "big":    (semi, 24),    # «Ваш бан» (32)
        "h2":     (semi, 12),    # заголовки разделов (16)
        "name":   (semi, 11),    # имя героя в строке (15)
        "value":  (semi, 12),    # число преимущества (16)
        "body":   (text, 10),    # обычный текст (13)
        "body_b": (semi, 10),
        "small":  (text, 9),     # подписи (12)
        "small_b": (semi, 9),
        "tiny":   (text, 8),     # клавиша в подсказке (11)
        "input":  (text, 12),    # поле ввода (16)
        "button": (semi, 10),
    }
