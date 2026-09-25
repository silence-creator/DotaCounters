"""Подбор героя против нескольких врагов.

На странице героя Dotabuff даёт полную таблицу матчапов: для каждого соперника
там стоит, насколько хуже этот герой против него играет. Значит, чтобы выбрать
пик против вражеского состава, достаточно сложить эти числа по всем врагам:
чем больше сумма, тем неудобнее нашему кандидату противостоят.

Сеть и интерфейс сюда не заглядывают — на входе уже разобранные отчёты.
"""

from dataclasses import dataclass, field

from .roles import ROLE_LEVELS, ROLE_ORDER

#: Сколько героев показывать в каждом списке по умолчанию.
DEFAULT_PICKS = 5
#: Больше пяти врагов в Dota не бывает.
MAX_ENEMIES = 5
#: Союзники — остальные четверо в команде того, кто выбирает.
MAX_ALLIES = 4
#: С запасом: в Captains Mode банов 14, в рейтинговом All Pick меньше.
MAX_BANS = 16

#: Роли для фильтра. Jungler Valve всё ещё размечает, но отдельного леса в
#: игре больше нет, поэтому в фильтр он не вынесен.
ROLE_FILTERS = ("carry", "support", "initiator", "disabler",
                "nuker", "durable", "escape", "pusher")


def has_role(hero: str, role: str) -> bool:
    """Свойственна ли герою роль по разметке Valve. Незнакомый герой — нет."""
    levels = ROLE_LEVELS.get(hero)
    return bool(levels) and levels[ROLE_ORDER.index(role)] > 0


@dataclass
class Pick:
    """Кандидат в пик и его преимущество над вражеским составом."""
    hero: str
    total: float                                  # сумма по всем врагам
    per_enemy: dict = field(default_factory=dict)  # враг -> преимущество
    icon_url: str | None = None

    @property
    def average(self) -> float:
        return self.total / len(self.per_enemy) if self.per_enemy else 0.0


@dataclass
class DraftResult:
    """Итог подбора."""
    enemies: list = field(default_factory=list)   # враги, которых удалось учесть
    picks: list = field(default_factory=list)     # кого брать, лучшие первыми
    avoid: list = field(default_factory=list)     # кого не брать, худшие первыми
    #: Враги, у которых не нашлось полной таблицы матчапов, — они не учтены.
    skipped: list = field(default_factory=list)


def analyse(reports: dict, limit: int = DEFAULT_PICKS, exclude=(),
            role: str | None = None) -> DraftResult:
    """Сложить матчапы врагов и отранжировать кандидатов.

    reports — {имя врага: CounterReport}. Учитываются только отчёты с полной
    таблицей матчапов: коротких списков на пять строк для суммирования мало.
    Сами враги из кандидатов исключаются — их уже забрали. exclude — ещё
    недоступные герои: союзники и баны. role — оставить только героев с этой
    ролью (см. ROLE_FILTERS), и в «брать», и в «не брать».
    """
    result = DraftResult()
    totals, per_enemy, icons = {}, {}, {}
    enemy_names = {name.strip().lower() for name in reports}
    taken = enemy_names | {name.strip().lower() for name in exclude}

    for enemy, report in reports.items():
        rows = [m for m in (getattr(report, "matchups", None) or [])
                if m.advantage_value is not None]
        if not rows:
            result.skipped.append(enemy)
            continue
        result.enemies.append(enemy)
        for matchup in rows:
            if matchup.hero.strip().lower() in taken:
                continue  # героя уже взяли или забанили
            totals[matchup.hero] = totals.get(matchup.hero, 0.0) + matchup.advantage_value
            per_enemy.setdefault(matchup.hero, {})[enemy] = matchup.advantage_value
            icons.setdefault(matchup.hero, matchup.icon_url)

    # Кандидат учитывается, только если встретился у всех учтённых врагов:
    # иначе сумма по трём врагам конкурировала бы с суммой по одному.
    complete = [hero for hero, seen in per_enemy.items()
                if len(seen) == len(result.enemies)
                and (role is None or has_role(hero, role))]
    picks = [Pick(hero=hero, total=totals[hero], per_enemy=per_enemy[hero],
                  icon_url=icons.get(hero)) for hero in complete]
    picks.sort(key=lambda p: (-p.total, p.hero))

    limit = max(1, limit)
    result.picks = picks[:limit]
    result.avoid = picks[::-1][:limit]
    return result


# ── Состав драфта ─────────────────────────────────────────────────────────────

GROUPS = ("enemies", "allies", "bans")
_GROUP_LIMITS = {"enemies": MAX_ENEMIES, "allies": MAX_ALLIES, "bans": MAX_BANS}


class DraftBoard:
    """Враги, союзники и баны плюс скачанные страницы врагов.

    Один состав на вкладку «Драфт» и оверлей: героя, добавленного в одном
    месте, видно в другом, а страница врага качается один раз. Сеть сюда не
    заглядывает — отчёты приносит интерфейс через store().
    """

    def __init__(self):
        self.groups = {group: [] for group in GROUPS}
        self.reports = {}   # враг -> CounterReport
        self.failed = {}    # враг -> ошибка последней загрузки
        self.loading = set()  # враги, чьи страницы сейчас качаются
        self.role = None    # фильтр по роли, см. ROLE_FILTERS

    @property
    def enemies(self):
        return self.groups["enemies"]

    def group_of(self, hero: str):
        for group, heroes in self.groups.items():
            if any(h.lower() == hero.lower() for h in heroes):
                return group
        return None

    def add(self, group: str, hero: str) -> str:
        """Добавить героя: «added», «moved» (был в другом списке), «dup» или «full».

        Один герой не может быть сразу врагом и союзником, поэтому добавление
        в другой список переносит его.
        """
        current = self.group_of(hero)
        if current == group:
            return "dup"
        if len(self.groups[group]) >= _GROUP_LIMITS[group]:
            return "full"
        if current:
            self.remove(hero)
        self.groups[group].append(hero)
        return "moved" if current else "added"

    def remove(self, hero: str) -> None:
        for heroes in self.groups.values():
            for h in list(heroes):
                if h.lower() == hero.lower():
                    heroes.remove(h)

    def clear(self) -> None:
        """Очистить состав. Скачанные страницы остаются — пригодятся в следующем драфте."""
        for heroes in self.groups.values():
            heroes.clear()
        self.failed.clear()

    def limit_of(self, group: str) -> int:
        return _GROUP_LIMITS[group]

    def missing(self, retry: bool = False) -> list:
        """Враги, чьи страницы надо скачать: ещё нет и не качаются.

        Не загрузившиеся сами не повторяются — только по retry, иначе каждое
        изменение состава снова стучалось бы в отказавший Dotabuff.
        """
        return [hero for hero in self.enemies
                if hero not in self.reports and hero not in self.loading
                and (retry or hero not in self.failed)]

    def store(self, hero: str, report=None, error=None) -> None:
        self.loading.discard(hero)
        if report is not None:
            self.reports[hero] = report
            self.failed.pop(hero, None)
        else:
            self.failed[hero] = error

    def analyse(self, limit: int = DEFAULT_PICKS):
        """Подбор по скачанным страницам; None, если врагов со страницей нет."""
        reports = {hero: self.reports[hero] for hero in self.enemies if hero in self.reports}
        if not reports:
            return None
        return analyse(reports, limit=limit, role=self.role,
                       exclude=self.groups["allies"] + self.groups["bans"])
