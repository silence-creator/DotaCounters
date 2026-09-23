"""Подбор героя против нескольких врагов.

На странице героя Dotabuff даёт полную таблицу матчапов: для каждого соперника
там стоит, насколько хуже этот герой против него играет. Значит, чтобы выбрать
пик против вражеского состава, достаточно сложить эти числа по всем врагам:
чем больше сумма, тем неудобнее нашему кандидату противостоят.

Сеть и интерфейс сюда не заглядывают — на входе уже разобранные отчёты.
"""

from dataclasses import dataclass, field

#: Сколько героев показывать в каждом списке по умолчанию.
DEFAULT_PICKS = 5
#: Больше пяти врагов в Dota не бывает.
MAX_ENEMIES = 5


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


def analyse(reports: dict, limit: int = DEFAULT_PICKS) -> DraftResult:
    """Сложить матчапы врагов и отранжировать кандидатов.

    reports — {имя врага: CounterReport}. Учитываются только отчёты с полной
    таблицей матчапов: коротких списков на пять строк для суммирования мало.
    Сами враги из кандидатов исключаются — их уже забрали.
    """
    result = DraftResult()
    totals, per_enemy, icons = {}, {}, {}
    enemy_names = {name.strip().lower() for name in reports}

    for enemy, report in reports.items():
        rows = [m for m in (getattr(report, "matchups", None) or [])
                if m.advantage_value is not None]
        if not rows:
            result.skipped.append(enemy)
            continue
        result.enemies.append(enemy)
        for matchup in rows:
            if matchup.hero.strip().lower() in enemy_names:
                continue  # этого героя враг уже взял
            totals[matchup.hero] = totals.get(matchup.hero, 0.0) + matchup.advantage_value
            per_enemy.setdefault(matchup.hero, {})[enemy] = matchup.advantage_value
            icons.setdefault(matchup.hero, matchup.icon_url)

    # Кандидат учитывается, только если встретился у всех учтённых врагов:
    # иначе сумма по трём врагам конкурировала бы с суммой по одному.
    complete = [hero for hero, seen in per_enemy.items()
                if len(seen) == len(result.enemies)]
    picks = [Pick(hero=hero, total=totals[hero], per_enemy=per_enemy[hero],
                  icon_url=icons.get(hero)) for hero in complete]
    picks.sort(key=lambda p: (-p.total, p.hero))

    limit = max(1, limit)
    result.picks = picks[:limit]
    result.avoid = picks[::-1][:limit]
    return result
