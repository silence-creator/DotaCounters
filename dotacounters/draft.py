"""Подбор героя против нескольких врагов.

На странице героя Dotabuff даёт полную таблицу матчапов: для каждого соперника
там стоит, насколько хуже этот герой против него играет. Значит, чтобы выбрать
пик против вражеского состава, достаточно сложить эти числа по всем врагам:
чем больше сумма, тем неудобнее нашему кандидату противостоят.

Сеть и интерфейс сюда не заглядывают — на входе уже разобранные отчёты.
"""

from dataclasses import dataclass, field

from .dotabuff import reliable
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


def counters_with_role(report, role: str, limit: int = DEFAULT_PICKS) -> tuple:
    """Разделы страницы контрпиков, оставив только соперников с ролью.

    Короткие таблицы Dotabuff — по пять строк на всех, после фильтра там
    почти никого не остаётся, поэтому разделы строятся из полной таблицы
    «Matchups». Её значение — насколько хуже герой страницы играет против
    соперника: положительное — «слабее против», отрицательное — «сильнее
    против». Так списки не пересекаются, даже если героев с ролью мало.
    Возвращает (слабее против, сильнее против); без полной таблицы — пустые.
    """
    rows = [m for m in (getattr(report, "matchups", None) or [])
            if m.advantage_value is not None and has_role(m.hero, role) and reliable(m)]
    limit = max(1, limit)
    weak = sorted((m for m in rows if m.advantage_value > 0),
                  key=lambda m: -m.advantage_value)[:limit]
    strong = sorted((m for m in rows if m.advantage_value < 0),
                    key=lambda m: m.advantage_value)[:limit]
    return weak, strong


@dataclass
class Pick:
    """Кандидат в пик и его преимущество над вражеским составом."""
    hero: str
    total: float                                  # сумма по всем врагам
    per_enemy: dict = field(default_factory=dict)  # враг -> преимущество
    icon_url: str | None = None
    #: Меньше всего матчей среди его пар с врагами: насколько верить сумме
    #: определяет самая слабая из них. None — число матчей неизвестно.
    matches: int | None = None

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
    totals, per_enemy, icons, fewest = {}, {}, {}, {}
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
            # Редкая пара — шум: считаем её нейтральной, а не выбрасываем
            # кандидата, иначе одна такая пара убрала бы героя из подсказок.
            value = matchup.advantage_value if reliable(matchup) else 0.0
            totals[matchup.hero] = totals.get(matchup.hero, 0.0) + value
            per_enemy.setdefault(matchup.hero, {})[enemy] = value
            icons.setdefault(matchup.hero, matchup.icon_url)
            if matchup.matches is not None:
                fewest[matchup.hero] = min(fewest.get(matchup.hero, matchup.matches),
                                           matchup.matches)

    # Кандидат учитывается, только если встретился у всех учтённых врагов:
    # иначе сумма по трём врагам конкурировала бы с суммой по одному.
    complete = [hero for hero, seen in per_enemy.items()
                if len(seen) == len(result.enemies)
                and (role is None or has_role(hero, role))]
    picks = [Pick(hero=hero, total=totals[hero], per_enemy=per_enemy[hero],
                  icon_url=icons.get(hero), matches=fewest.get(hero)) for hero in complete]
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


# ── Captains Mode ─────────────────────────────────────────────────────────────

#: Порядок ходов Captains Mode (7.41): кто ходит — «first» (тот, кто начинает
#: драфт) или «second», и что — бан или пик. Сверено со скриншотом игры.
CM_ORDER = (
    ("first", "ban"), ("first", "ban"), ("second", "ban"), ("second", "ban"),
    ("first", "ban"), ("second", "ban"), ("second", "ban"),
    ("first", "pick"), ("second", "pick"),
    ("first", "ban"), ("first", "ban"), ("second", "ban"),
    ("first", "pick"), ("second", "pick"), ("first", "pick"),
    ("second", "pick"), ("first", "pick"), ("second", "pick"),
    ("first", "ban"), ("second", "ban"), ("first", "ban"), ("second", "ban"),
    ("first", "pick"), ("second", "pick"),
)

#: Строки доски, как в игре: (бан или пик, номер хода первого, номер хода
#: второго); None — у этой стороны в строке хода нет. Номера с единицы.
CM_BOARD = (
    ("ban", 1, 3), ("ban", 2, 4), ("ban", 5, 6), ("ban", None, 7), ("pick", 8, 9),
    ("ban", 10, 12), ("ban", 11, None), ("pick", 13, 14), ("pick", 15, 16),
    ("pick", 17, 18), ("ban", 19, 20), ("ban", 21, 22), ("pick", 23, 24),
)

#: Фазы: (первый ход, последний ход, бан или пик, номер фазы этого вида).
CM_PHASES = ((1, 7, "ban", 1), (8, 9, "pick", 1), (10, 12, "ban", 2),
             (13, 18, "pick", 2), (19, 22, "ban", 3), (23, 24, "pick", 3))

SIDES = ("radiant", "dire")


class CaptainsDraft:
    """Драфт Captains Mode: 24 хода по порядку и скачанные страницы пиков.

    Стороны — «radiant» и «dire»; first — кто ходит первым, ours — за кого
    играем мы. Подсказки: банить тех, кто сильнее всех против НАШИХ пиков,
    брать тех, кто сильнее всех против ИХ пиков. Сеть сюда не заглядывает —
    страницы приносит интерфейс через store().
    """

    def __init__(self):
        self.first = "radiant"
        self.ours = "radiant"
        self.heroes = [None] * len(CM_ORDER)
        self.reports = {}
        self.failed = {}
        self.loading = set()
        self.role = None

    # ── Ходы ──────────────────────────────────────────────────────────────

    def side(self, index: int) -> str:
        """Сторона, которая делает ход index (с нуля)."""
        who = CM_ORDER[index][0]
        other = "dire" if self.first == "radiant" else "radiant"
        return self.first if who == "first" else other

    @staticmethod
    def kind(index: int) -> str:
        return CM_ORDER[index][1]

    @property
    def current(self):
        """Номер (с нуля) хода, который сейчас делается; None — драфт окончен."""
        for index, hero in enumerate(self.heroes):
            if hero is None:
                return index
        return None

    def taken(self) -> set:
        return {h.lower() for h in self.heroes if h}

    def play(self, hero: str) -> str:
        """Записать героя на текущий ход: «ok», «taken» (уже выбран или забанен), «done»."""
        index = self.current
        if index is None:
            return "done"
        if hero.lower() in self.taken():
            return "taken"
        self.heroes[index] = hero
        return "ok"

    def undo(self):
        """Отменить последний сделанный ход. Возвращает героя или None."""
        for index in range(len(self.heroes) - 1, -1, -1):
            if self.heroes[index]:
                hero, self.heroes[index] = self.heroes[index], None
                return hero
        return None

    def reset(self):
        self.heroes = [None] * len(CM_ORDER)
        self.failed.clear()

    def upcoming(self, count: int = 3) -> list:
        """Следующие ходы после текущего: [(номер с нуля, сторона, бан/пик)]."""
        start = self.current
        if start is None:
            return []
        return [(i, self.side(i), self.kind(i))
                for i in range(start + 1, min(start + 1 + count, len(CM_ORDER)))]

    def next_pick(self, side: str):
        """Номер (с нуля) ближайшего пика стороны начиная с текущего хода; None — нет."""
        start = self.current
        if start is None:
            return None
        for i in range(start, len(CM_ORDER)):
            if self.kind(i) == "pick" and self.side(i) == side:
                return i
        return None

    @staticmethod
    def phase(index: int):
        """(бан или пик, номер фазы) для хода index (с нуля)."""
        n = index + 1
        for first, last, kind, number in CM_PHASES:
            if first <= n <= last:
                return kind, number
        return None

    def picks(self, side: str) -> list:
        return [h for i, h in enumerate(self.heroes)
                if h and self.kind(i) == "pick" and self.side(i) == side]

    def bans(self, side: str) -> list:
        return [h for i, h in enumerate(self.heroes)
                if h and self.kind(i) == "ban" and self.side(i) == side]

    @property
    def theirs(self) -> str:
        return "dire" if self.ours == "radiant" else "radiant"

    # ── Страницы и подсказки ──────────────────────────────────────────────

    def missing(self, retry: bool = False) -> list:
        """Пики, чьих страниц нет и которые не качаются. Баны страниц не требуют."""
        heroes = self.picks("radiant") + self.picks("dire")
        return [h for h in heroes if h not in self.reports and h not in self.loading
                and (retry or h not in self.failed)]

    def store(self, hero: str, report=None, error=None) -> None:
        self.loading.discard(hero)
        if report is not None:
            self.reports[hero] = report
            self.failed.pop(hero, None)
        else:
            self.failed[hero] = error

    def _suggest(self, heroes, limit):
        reports = {h: self.reports[h] for h in heroes if h in self.reports}
        if not reports:
            return None
        return analyse(reports, limit=limit, role=self.role,
                       exclude=[h for h in self.heroes if h])

    def ban_suggestions(self, limit: int = DEFAULT_PICKS):
        """Кого банить: сильнейшие против наших пиков. None — наших пиков со страницей нет."""
        return self._suggest(self.picks(self.ours), limit)

    def pick_suggestions(self, limit: int = DEFAULT_PICKS):
        """Кого брать: сильнейшие против их пиков. None — их пиков со страницей нет."""
        return self._suggest(self.picks(self.theirs), limit)
