"""Пересобрать dotacounters/lanes.py со страниц линий Dotabuff.

Запуск из корня проекта:  python tools/update_lanes.py

Из этих цифр positions.py выводит позиции героев 1–5. Мета меняется от патча
к патчу, но не за день, поэтому страницы не качаются при каждом запуске
программы — как роли в roles.py. Обновлять с новым патчем. Данные — за месяц
(то, что Dotabuff показывает по умолчанию). Запросов — четыре, с паузой.
"""

import datetime
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotacounters.heroes import ALL_HEROES  # noqa: E402
from dotacounters.net import create_scraper  # noqa: E402
from dotacounters.positions import LANE_KEYS, parse_lanes  # noqa: E402

URL = "https://www.dotabuff.com/heroes/lanes?lane=%s"
OUT = os.path.join(ROOT, "dotacounters", "lanes.py")

HEADER = '''"""Статистика линий Dotabuff. Файл собран tools/update_lanes.py — руками не править.

Снимок от %s, данные за месяц. LANES — {герой: {линия: (доля матчей героя на
линии, %%; средний GPM там)}}. Линии, где героя меньше ~5%%, Dotabuff не
показывает — их здесь нет. Позиции из этого выводит positions.py.
"""

LANES = {
'''


def fetch(scraper, lane):
    """Страница линии; Dotabuff иногда отвечает 403 — несколько попыток."""
    for attempt in range(4):
        response = scraper.get(URL % lane, timeout=20)
        if response.status_code == 200:
            return parse_lanes(response.text)
        print(lane, "ответ", response.status_code, "— повтор")
        time.sleep(2 + 2 * attempt)
    sys.exit("страница линии %s не загрузилась" % lane)


def main():
    scraper = create_scraper()
    table = {}
    for lane in LANE_KEYS:
        rows = fetch(scraper, lane)
        unknown = sorted(set(rows) - set(ALL_HEROES))
        if unknown:
            sys.exit("Dotabuff знает героев, которых нет в heroes.py: %s" % ", ".join(unknown))
        for hero, value in rows.items():
            table.setdefault(hero, {})[lane] = value
        print(lane, len(rows), "героев")
        time.sleep(1)

    lines = []
    for hero in ALL_HEROES:
        lanes = table.get(hero, {})
        body = ", ".join("%r: (%r, %d)" % (lane, lanes[lane][0], lanes[lane][1])
                         for lane in LANE_KEYS if lane in lanes)
        lines.append("    %r: {%s},\n" % (hero, body))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(HEADER % datetime.date.today().isoformat() + "".join(lines) + "}\n")
    print("записано:", OUT)


if __name__ == "__main__":
    main()
