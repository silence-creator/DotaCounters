"""Позиции героев 1–5 по статистике линий Dotabuff.

У Valve позиций нет — только роли (керри, саппорт, инициатор…), поэтому
«мида» или «тройки» в разметке Valve не найти. Dotabuff на странице
/heroes/lanes?lane=... для каждой линии даёт долю матчей героя на ней
(Presence) и его средний GPM там. Отсюда позиции:

- мид (2) — от MIN_PRESENCE матчей на миде;
- лёгкая линия — керри (1), если GPM там не ниже SAFE_CORE_GPM, иначе
  пятёрка (5). Граница чистая: у саппортов до ~410, у коров от ~510;
- сложная линия вместе с роумом — тройка (3), если GPM не ниже
  OFF_CORE_GPM, четвёрка (4), если ниже OFF_SUPPORT_GPM. Чёткой границы
  тут нет: между ними герои, которых играют и так и так (Earthshaker,
  Magnus, Spirit Breaker) — они получают обе позиции. Кроме явных
  саппортов по разметке Valve (уровень support от SUPPORT_LEVEL): Omniknight
  или Ogre Magi с GPM 404–432 — четвёрки, а не тройки.

Если ни одна линия не набирает порога, герою достаётся самая частая —
иначе фильтр по позиции не показал бы его никогда.

Сами цифры лежат в lanes.py (собирается tools/update_lanes.py), сеть здесь
не нужна; разбор страницы — parse_lanes — для скрипта и тестов.
"""

import itertools

from bs4 import BeautifulSoup

from .dotabuff import ParseError
from .roles import ROLE_LEVELS, ROLE_ORDER

#: Ключи фильтра и номера позиций.
POSITIONS = ("pos1", "pos2", "pos3", "pos4", "pos5")
#: Линии страницы Dotabuff, из которых складываются позиции.
LANE_KEYS = ("safe", "mid", "off", "roaming")

#: Порог доли матчей на линии, %. Выбрал пользователь.
MIN_PRESENCE = 20.0
#: Лёгкая линия: не ниже — керри, ниже — пятёрка.
SAFE_CORE_GPM = 460
#: Сложная линия: не ниже OFF_CORE_GPM — тройка, ниже OFF_SUPPORT_GPM —
#: четвёрка; между ними — обе.
OFF_CORE_GPM = 400
OFF_SUPPORT_GPM = 440
#: Уровень роли support у Valve (0–3), с которого герой в полосе между
#: OFF_CORE_GPM и OFF_SUPPORT_GPM считается только четвёркой.
SUPPORT_LEVEL = 2


def parse_lanes(html: str) -> dict:
    """Таблица страницы линии -> {герой: (доля матчей, %; GPM)}.

    Колонки ищутся по подписям, с учётом colspan: «Hero» занимает две ячейки
    (иконка и имя). Числа берутся из data-value — там они без округления.
    """
    table = BeautifulSoup(html, "html.parser").find("table")
    if table is None or table.find("thead") is None:
        raise ParseError("на странице линии нет таблицы героев")
    columns = []
    for th in table.find("thead").find_all("th"):
        columns.extend([th.get_text(" ", strip=True).lower()] * int(th.get("colspan") or 1))
    try:
        hero_col = columns.index("hero")
        presence_col, gpm_col = columns.index("presence"), columns.index("gpm")
    except ValueError:
        raise ParseError("не найдены колонки Hero, Presence, GPM среди %s" % columns) from None

    out = {}
    for row in table.find("tbody").find_all("tr"):
        cells = row.find_all("td")
        if len(cells) != len(columns):
            continue
        hero = (cells[hero_col].get("data-value") or cells[hero_col].get_text(strip=True)).strip()
        try:
            presence = float(cells[presence_col]["data-value"])
            gpm = float(cells[gpm_col]["data-value"])
        except (KeyError, ValueError):
            raise ParseError("у %s нет числа в колонке Presence или GPM" % hero) from None
        if hero:
            out[hero] = (round(presence, 2), round(gpm))
    if not out:
        raise ParseError("таблица линии пуста")
    return out


def positions_of(hero: str, lanes: dict | None = None) -> tuple:
    """Позиции героя, например ("pos3", "pos4"). Незнакомый герой — пусто.

    lanes — {герой: {линия: (доля, GPM)}}; по умолчанию снимок из lanes.py.
    """
    if lanes is None:
        from .lanes import LANES as lanes
    data = lanes.get(hero)
    if not data:
        return ()
    safe, mid, off = data.get("safe"), data.get("mid"), data.get("off")
    roaming = data.get("roaming", (0.0, 0))[0]
    found = set()
    if mid and mid[0] >= MIN_PRESENCE:
        found.add("pos2")
    if safe and safe[0] >= MIN_PRESENCE:
        found.add("pos1" if safe[1] >= SAFE_CORE_GPM else "pos5")
    # Роумят саппорты: доля роума прибавляется к сложной линии
    off_share = (off[0] if off else 0.0) + roaming
    if off_share >= MIN_PRESENCE:
        gpm = off[1] if off else 0
        if gpm >= OFF_SUPPORT_GPM or (gpm >= OFF_CORE_GPM and not _valve_support(hero)):
            found.add("pos3")
        if gpm < OFF_SUPPORT_GPM:
            found.add("pos4")
    if not found:
        found = _most_played(safe, mid, off, roaming)
    return tuple(p for p in POSITIONS if p in found)


#: Какая линия стоит за позицией — чтобы сравнить, где герой играет чаще.
_POSITION_LANE = {"pos1": "safe", "pos5": "safe", "pos2": "mid", "pos3": "off", "pos4": "off"}


def _share(hero: str, position: str, lanes: dict) -> float:
    """Доля матчей героя на линии позиции (для сложной — вместе с роумом)."""
    data = lanes.get(hero) or {}
    lane = _POSITION_LANE[position]
    share = (data.get(lane) or (0.0, 0))[0]
    if lane == "off":
        share += (data.get("roaming") or (0.0, 0))[0]
    return share


def assign_positions(heroes, lanes: dict | None = None) -> dict:
    """Расставить команду по позициям: {герой: позиция}.

    У героя бывает две-три позиции, поэтому перебираются все расстановки
    (героев не больше пяти, вариантов — единицы сотен) и берётся та, что
    закрывает больше разных позиций; при равенстве — где герои стоят на
    своих самых частых линиях. Герой без позиций в расстановку не попадает.
    """
    if lanes is None:
        from .lanes import LANES as lanes
    heroes = [h for h in heroes if positions_of(h, lanes)]
    if not heroes:
        return {}
    best, best_key = None, None
    for combo in itertools.product(*(positions_of(h, lanes) for h in heroes)):
        key = (len(set(combo)), sum(_share(h, p, lanes) for h, p in zip(heroes, combo)))
        if best_key is None or key > best_key:
            best, best_key = combo, key
    return dict(zip(heroes, best))


def missing_positions(heroes, lanes: dict | None = None) -> tuple:
    """Позиции, которые команда ещё не закрыла, по порядку 1–5."""
    taken = set(assign_positions(heroes, lanes).values())
    return tuple(p for p in POSITIONS if p not in taken)


def _valve_support(hero: str) -> bool:
    """Явный саппорт по разметке Valve."""
    levels = ROLE_LEVELS.get(hero)
    return bool(levels) and levels[ROLE_ORDER.index("support")] >= SUPPORT_LEVEL


def _most_played(safe, mid, off, roaming) -> set:
    """Позиция самой частой линии — когда ни одна не набрала порога."""
    shares = {"safe": safe[0] if safe else 0.0, "mid": mid[0] if mid else 0.0,
              "off": (off[0] if off else 0.0) + roaming}
    lane = max(shares, key=shares.get)
    if shares[lane] <= 0:
        return set()
    if lane == "mid":
        return {"pos2"}
    if lane == "safe":
        return {"pos1" if safe[1] >= SAFE_CORE_GPM else "pos5"}
    gpm = off[1] if off else 0
    return {"pos3"} if gpm >= (OFF_CORE_GPM + OFF_SUPPORT_GPM) / 2 else {"pos4"}
