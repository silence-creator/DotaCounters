"""Оценка драфта: команда против команды на данных матчапов Dotabuff.

На странице героя для каждого соперника есть преимущество — насколько хуже
герой играет против него. Пара «наш — их» видна с двух страниц: с нашей
(плюс — соперник нас контрит) и с их (плюс — мы контрим соперника). Значение
пары — среднее по тем страницам, что есть, со знаком «плюс — хорошо для нас».
Редкая пара (меньше MIN_MATCHES матчей) — ноль, как в подборе.

Итог — сумма по всем парам, делённая на 5: каждый герой играет против пяти.
Это перевес по матчапам, а не вероятность победы: как одно переводится в
другое, эти данные не говорят.

Сеть и интерфейс сюда не заглядывают — на входе уже скачанные отчёты.
"""

from dataclasses import dataclass, field

from .dotabuff import reliable
from .meta import in_rank
from .positions import assign_positions

#: Линии: наши позиции против их позиций. Лёгкая линия одной команды — это
#: сложная линия другой.
LANES = (
    ("safe", ("pos1", "pos5"), ("pos3", "pos4")),
    ("mid", ("pos2",), ("pos2",)),
    ("off", ("pos3", "pos4"), ("pos1", "pos5")),
)


@dataclass
class Pair:
    ours: str
    theirs: str
    value: float                 # плюс — пара выгодна нам
    matches: int | None = None


@dataclass
class Lane:
    lane: str                    # safe | mid | off — со стороны нашей команды
    ours: list
    theirs: list
    value: float


@dataclass
class Evaluation:
    ours: list
    theirs: list
    pairs: dict = field(default_factory=dict)      # (наш, их) -> Pair
    score: float = 0.0                             # сумма пар / 5
    lanes: list = field(default_factory=list)
    meta: tuple | None = None                      # (средний винрейт наших, их) в %
    #: Герои, по которым нет ни одной страницы с их парами, — не учтены.
    unknown: list = field(default_factory=list)

    def value(self, ours, theirs):
        pair = self.pairs.get((ours, theirs))
        return pair.value if pair else None

    def hero_total(self, hero) -> float:
        """Сумма пар героя (для их героя — со знаком «плюс — хорошо для нас»)."""
        return sum(p.value for p in self.pairs.values() if hero in (p.ours, p.theirs))

    def best(self, n=3) -> list:
        """Самые выгодные нам пары."""
        return [p for p in sorted(self.pairs.values(), key=lambda p: -p.value)[:n] if p.value > 0]

    def worst(self, n=3) -> list:
        """Самые опасные для нас пары."""
        return [p for p in sorted(self.pairs.values(), key=lambda p: p.value)[:n] if p.value < 0]


def _row(report, opponent):
    for m in getattr(report, "matchups", None) or []:
        if m.hero == opponent and m.advantage_value is not None:
            return m
    return None


def pair_value(ours, theirs, reports):
    """(значение пары, матчей) по доступным страницам; None — ни одной строки."""
    values, matches = [], None
    ours_row = _row(reports.get(ours), theirs)
    if ours_row is not None:
        values.append(-ours_row.advantage_value if reliable(ours_row) else 0.0)
        matches = ours_row.matches
    theirs_row = _row(reports.get(theirs), ours)
    if theirs_row is not None:
        values.append(theirs_row.advantage_value if reliable(theirs_row) else 0.0)
        matches = matches if matches is not None else theirs_row.matches
    if not values:
        return None
    return sum(values) / len(values), matches


def evaluate(ours, theirs, reports, meta=None, rank="all", lanes=None) -> Evaluation:
    """Оценить драфт. reports — {герой: CounterReport} любой из команд; meta —
    данные meta.py (или None); lanes — снимок линий для расстановки позиций
    (по умолчанию lanes.py)."""
    result = Evaluation(ours=list(ours), theirs=list(theirs))
    seen = set()
    for a in ours:
        for b in theirs:
            found = pair_value(a, b, reports)
            if found is None:
                continue
            value, matches = found
            result.pairs[(a, b)] = Pair(a, b, value, matches)
            seen.update((a, b))
    result.unknown = [h for h in list(ours) + list(theirs) if h not in seen]
    result.score = sum(p.value for p in result.pairs.values()) / 5

    our_pos = assign_positions(ours, lanes)
    their_pos = assign_positions(theirs, lanes)
    for lane, mine, other in LANES:
        a = [h for h, p in our_pos.items() if p in mine]
        b = [h for h, p in their_pos.items() if p in other]
        if a and b:
            value = sum(result.value(x, y) or 0.0 for x in a for y in b)
            result.lanes.append(Lane(lane, a, b, value))

    if meta:
        stats = in_rank(meta, rank)
        wr = [[stats[h][1] for h in team if h in stats] for team in (ours, theirs)]
        if wr[0] and wr[1]:
            result.meta = (sum(wr[0]) / len(wr[0]), sum(wr[1]) / len(wr[1]))
    return result
