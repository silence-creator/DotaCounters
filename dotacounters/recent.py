"""Недавние герои, избранное и запомненная геометрия окна.

Здесь только работа со списками и строками — ни интерфейса, ни файлов.
"""

import re

#: Сколько недавних героев помнить.
MAX_HISTORY = 10
#: Больше не влезает в строку под полем ввода.
MAX_FAVOURITES = 8

_GEOMETRY_RE = re.compile(r"^(\d{2,5})x(\d{2,5})([+-]-?\d{1,5})([+-]-?\d{1,5})$")


def remember(history, hero: str, limit: int = MAX_HISTORY) -> list:
    """Поставить героя в начало списка недавних, без повторов."""
    hero = (hero or "").strip()
    if not hero:
        return list(history or [])
    rest = [h for h in (history or []) if h.lower() != hero.lower()]
    return [hero] + rest[:limit - 1]


def toggle_favourite(favourites, hero: str, limit: int = MAX_FAVOURITES) -> list:
    """Добавить героя в избранное или убрать, если он там уже есть."""
    hero = (hero or "").strip()
    favourites = list(favourites or [])
    if not hero:
        return favourites
    for existing in favourites:
        if existing.lower() == hero.lower():
            favourites.remove(existing)
            return favourites
    if len(favourites) >= limit:
        return favourites  # молча не добавляем сверх предела
    favourites.append(hero)
    return favourites


def is_favourite(favourites, hero: str) -> bool:
    hero = (hero or "").strip().lower()
    return any(h.lower() == hero for h in (favourites or []))


def clean_list(values, limit: int) -> list:
    """Привести к списку строк: из конфига может прийти что угодно."""
    if not isinstance(values, list):
        return []
    out = []
    for value in values:
        if isinstance(value, str) and value.strip():
            if not any(value.strip().lower() == o.lower() for o in out):
                out.append(value.strip())
    return out[:limit]


def sane_geometry(value, screen_width: int, screen_height: int,
                  min_width: int = 620, min_height: int = 620) -> str | None:
    """Проверить запомненную геометрию «ШxВ+X+Y».

    Возвращает None, если строка испорчена или окно оказалось бы за пределами
    экрана: монитор могли отключить, и окно открылось бы в пустоте.
    """
    if not isinstance(value, str):
        return None
    found = _GEOMETRY_RE.match(value.strip())
    if not found:
        return None
    width, height = int(found.group(1)), int(found.group(2))
    x, y = int(found.group(3)), int(found.group(4))
    if width < min_width or height < min_height:
        return None
    if width > screen_width or height > screen_height:
        return None
    # Заголовок окна должен остаться доступным мышью
    if x < -width + 100 or x > screen_width - 100:
        return None
    if y < 0 or y > screen_height - 60:
        return None
    return "%dx%d%+d%+d" % (width, height, x, y)


_POSITION_RE = re.compile(r"^([+-]-?\d{1,5})([+-]-?\d{1,5})$")


def sane_position(value, screen_width: int, screen_height: int,
                  width: int, height: int) -> str | None:
    """Проверить запомненное место окна без рамки «+X+Y».

    У такого окна нет заголовка, за который его можно вытащить, поэтому оно
    должно целиком помещаться на экране. Иначе None.
    """
    if not isinstance(value, str):
        return None
    found = _POSITION_RE.match(value.strip())
    if not found:
        return None
    x, y = int(found.group(1)), int(found.group(2))
    if x < 0 or y < 0 or x + width > screen_width or y + height > screen_height:
        return None
    return "%+d%+d" % (x, y)
