"""Короткая запись больших чисел для вывода: 48 459 -> «48к», 1 234 567 -> «1,2 млн»."""


def short_count(n, thousand: str = "k", million: str = "M", decimal: str = ".") -> str:
    """Число матчей коротко. Суффиксы и разделитель дроби — из языка интерфейса.

    До 10 тысяч и до 10 миллионов — с одним знаком после запятой. Округление
    вниз: запись не должна завышать число — 1 999 при округлении стало бы
    «2k», хотя по порогу редких пар (2 000) такая пара ещё редкая.
    """
    if n is None:
        return ""
    n = int(n)
    if n < 1000:
        return str(n)
    unit, suffix = (1000, thousand) if n < 1_000_000 else (1_000_000, million)
    if n < 10 * unit:
        tenths = n * 10 // unit
        text = "%d.%d" % (tenths // 10, tenths % 10)
    else:
        text = "%d" % (n // unit)
    text = text.replace(".", decimal)
    if text.endswith(decimal + "0"):
        text = text[:-2]
    return text + suffix
