"""Кеш разобранных страниц Dotabuff на диске: cache/pages рядом с программой.

Хранится не HTML (140 КБ на героя), а то, что из него разобрано: полная
таблица матчапов и, если понадобились, короткие таблицы — около 30 КБ, на
всех героев около 4 МБ. Из этого разделы собираются под любое «КОЛ-ВО»
(dotabuff.select_sections).

Страница живёт MAX_AGE. Если известен текущий патч и страница сохранена при
другом, она тоже устарела: цифры после патча другие. Испорченный или чужой
формат файла — просто промах, программа скачает страницу заново.
"""

import json
import os
import re
import threading
import time
from dataclasses import asdict, fields

from .dotabuff import CounterReport, Matchup

#: Сколько хранится страница.
MAX_AGE = 24 * 3600
#: Версия формата файла: при изменении старые файлы считаются промахом.
FORMAT = 1

_SAFE_SLUG = re.compile(r"^[a-z0-9-]{1,40}$")
_MATCHUP_FIELDS = {f.name for f in fields(Matchup)}


def _rows(items) -> list:
    return [Matchup(**{k: v for k, v in item.items() if k in _MATCHUP_FIELDS})
            for item in items]


class PageCache:
    def __init__(self, folder: str | None, max_age: float = MAX_AGE, clock=time.time):
        self.folder = folder          # None — кеш выключен (папка недоступна)
        self.max_age = max_age
        self.clock = clock
        #: Текущий патч, когда он известен. Выставляет интерфейс.
        self.patch = None

    def _path(self, slug: str) -> str | None:
        if not self.folder or not _SAFE_SLUG.match(slug or ""):
            return None                # имя файла из ввода — только безопасное
        return os.path.join(self.folder, slug + ".json")

    def load(self, slug: str) -> CounterReport | None:
        """Свежая сохранённая страница или None."""
        path = self._path(slug)
        if not path:
            return None
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("format") != FORMAT:
                return None
            age = self.clock() - float(data["fetched_at"])
            if not 0 <= age < self.max_age:
                return None            # просрочена или часы переводили назад
            if self.patch and data.get("patch") and data["patch"] != self.patch:
                return None            # сохранена при прошлом патче
            return CounterReport(
                hero_slug=data["slug"],
                matchups=_rows(data.get("matchups", [])),
                short_countered_by=_rows(data.get("short_countered_by", [])),
                short_counters=_rows(data.get("short_counters", [])),
                degraded=bool(data.get("degraded")),
                cached_age=age,
            )
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def save(self, slug: str, report: CounterReport) -> None:
        path = self._path(slug)
        if not path:
            return
        data = {
            "format": FORMAT,
            "slug": slug,
            "fetched_at": self.clock(),
            "patch": self.patch,
            "degraded": report.degraded,
            "matchups": [asdict(m) for m in report.matchups],
            "short_countered_by": [asdict(m) for m in report.short_countered_by],
            "short_counters": [asdict(m) for m in report.short_counters],
        }
        try:
            os.makedirs(self.folder, exist_ok=True)
            # Свой временный файл на поток: поиск и драфт могут сохранять
            # одного героя одновременно.
            tmp = "%s.%d.tmp" % (path, threading.get_ident())
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            os.replace(tmp, path)      # целиком или никак: полуфайл не прочтётся
        except OSError:
            pass                       # нет места или прав — живём без кеша

    def count(self) -> int:
        if not self.folder:
            return 0   # os.listdir(None) читает текущую папку — не то
        try:
            return sum(1 for name in os.listdir(self.folder) if name.endswith(".json"))
        except OSError:
            return 0

    def clear(self) -> int:
        """Удалить все сохранённые страницы. Возвращает, сколько удалено."""
        if not self.folder:
            # Без этой проверки os.listdir(None) дал бы текущую папку, и
            # удалились бы чужие .json — например, dota_config.json.
            return 0
        removed = 0
        try:
            names = os.listdir(self.folder)
        except OSError:
            return 0
        for name in names:
            if name.endswith((".json", ".tmp")):
                try:
                    os.unlink(os.path.join(self.folder, name))
                    removed += name.endswith(".json")
                except OSError:
                    pass
        return removed
