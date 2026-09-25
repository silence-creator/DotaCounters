"""Пересобрать dotacounters/roles.py из datafeed Valve.

Запуск из корня проекта:  python tools/update_roles.py

Роли героев меняются редко — с новым героем или переработкой. Поэтому они
не качаются при каждом запуске программы, а лежат в модуле рядом со списком
героев; этот скрипт обновляет модуль. Запросов — по одному на героя, с паузой.
"""

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotacounters.heroes import ALL_HEROES  # noqa: E402
from dotacounters.net import create_scraper  # noqa: E402

FEED = "https://www.dota2.com/datafeed"
OUT = os.path.join(ROOT, "dotacounters", "roles.py")

HEADER = '''"""Роли героев по разметке Valve. Файл собран tools/update_roles.py — руками не править.

role_levels из datafeed/herodata: для каждой роли уровень 0–3, где 0 — роль
герою не свойственна. Порядок ролей — как в ответе Valve.
"""

#: Порядок значений в role_levels.
ROLE_ORDER = ("carry", "support", "nuker", "disabler", "jungler",
              "durable", "escape", "pusher", "initiator")

ROLE_LEVELS = {
'''


def main():
    scraper = create_scraper()
    heroes = scraper.get(FEED + "/herolist?language=english", timeout=20).json()
    heroes = heroes["result"]["data"]["heroes"]
    ids = {h["name_english_loc"]: h["id"] for h in heroes}

    missing = sorted(set(ALL_HEROES) - set(ids))
    if missing:
        sys.exit("нет в datafeed: %s — сверьте имена в heroes.py" % ", ".join(missing))

    lines = []
    for name in ALL_HEROES:
        url = FEED + "/herodata?language=english&hero_id=%d" % ids[name]
        data = scraper.get(url, timeout=20).json()["result"]["data"]["heroes"][0]
        levels = tuple(int(v) for v in data["role_levels"])
        lines.append("    %r: %r,\n" % (name, levels))
        print(name, levels)
        time.sleep(0.2)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(HEADER + "".join(lines) + "}\n")
    print("записано:", OUT)


if __name__ == "__main__":
    main()
