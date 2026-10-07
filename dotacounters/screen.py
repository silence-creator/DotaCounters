"""Считывание драфта с экрана Dota 2: какой герой стоит в какой клетке.

Сеть и окна сюда не заглядывают. На входе снимок окна игры (PIL.Image) и
портреты героев с CDN Valve, на выходе — кто в какой клетке и насколько
программа в этом уверена. Снимок делает capture.py, портреты приносит
интерфейс.

Портреты в игре — те же картинки, что на CDN (`dota_react/heroes`), только
обрезаны по-разному: в верхней полосе All Pick видна середина портрета, на
доске Captains Mode — почти весь. Сравнение — на маленьких картинках 32×18:
каждый канал выравнивается по среднему и разбросу (свет и контраст в игре
другие), затем средняя разница. Вся арифметика идёт в PIL, без numpy: все
портреты лежат в одной полосе-атласе, и одна операция сравнивает клетку
сразу со всеми.

Главное правило — никогда не подставлять молча неуверенного героя. Клетка
бывает пустой, с героем «под курсором» у игрока, который ещё не выбрал
(полупрозрачный, серый), с героем в косметике, не похожим на CDN. Поэтому у
каждой клетки есть состояние и запас уверенности, а дальше решает Tracker:
герой записывается, только если несколько снимков подряд согласны.
"""

from dataclasses import dataclass, field

from PIL import Image, ImageChops, ImageOps, ImageStat

# ── Разметка экрана ───────────────────────────────────────────────────────────
#
# Интерфейс Dota масштабируется по высоте окна: всё измерено в «опорных»
# точках при высоте 1080, x — от середины экрана. Доска Captains Mode при 16:9
# и 16:10 стоит на одном месте, а верхняя полоса при 16:10 раздвинута к краям
# примерно на 25 точек (замер октябрь 2026: снимки 1920×1200 пользователя и
# 1280×720, 1920×1080 из чужих матчей).

REF_H = 1080

#: Верхняя полоса: шаг клеток и расстояние от середины экрана до середины
#: ближней к часам клетки при 16:9 и 16:10. Для других пропорций — по прямой.
TOP_PITCH = 124.5
TOP_INNER = {16 / 9: 195.0, 16 / 10: 220.0}
#: Клетка верхней полосы: полуширина и верх-низ, опорные точки.
TOP_HALF_W = 51
TOP_Y = (9, 69)
#: Имя игрока под клеткой: у своего — ярко-белое.
NAME_Y = (80, 102)
NAME_HALF_W = 58

#: Доска Captains Mode, формат 7.41 на 24 хода (замер на пустой доске 16:10).
#: Колонка — сторона, которая делает ход; x — внутренность чёрной клетки.
BOARD_X = {
    ("radiant", "ban"): (475, 530), ("radiant", "pick"): (461, 530),
    ("dire", "ban"): (617, 672), ("dire", "pick"): (617, 686),
}
BOARD_H = {"ban": 30.6, "pick": 37.9}
#: Верх клетки каждого хода, по номерам 1–24.
BOARD_Y = (215.3, 251.3, 251.3, 287.3, 287.3, 323.4, 359.4, 399.0, 399.0,
           445.9, 481.9, 481.9, 521.5, 521.5, 564.8, 564.8, 608.0, 608.0,
           654.8, 654.8, 690.9, 690.9, 730.5, 730.5)
#: Подписи сторон над доской: у своей команды цветная (Radiant — зелёная,
#: Dire — красная), у чужой — серая.
BOARD_LABEL_X = {"radiant": (415, 545), "dire": (600, 730)}
BOARD_LABEL_Y = (186, 210)

SIDES = ("radiant", "dire")


def _scale(size):
    w, h = size
    return w / 2, h / REF_H


def _box(size, x0, y0, x1, y1):
    """Опорные координаты (x от середины) в пиксели снимка."""
    cx, s = _scale(size)
    return (round(cx + x0 * s), round(y0 * s), round(cx + x1 * s), round(y1 * s))


def top_inner(aspect: float) -> float:
    """Расстояние до ближней к часам клетки при пропорциях aspect (ширина/высота)."""
    (a1, v1), (a2, v2) = sorted(TOP_INNER.items())
    return v1 + (aspect - a1) * (v2 - v1) / (a2 - a1)


def top_slots(size) -> list:
    """Десять клеток верхней полосы в пикселях: Radiant 1–5 слева, Dire 1–5 справа."""
    w, h = size
    inner = top_inner(w / h)
    out = []
    for side in SIDES:
        for k in range(5):
            # у Radiant первый игрок — дальний от часов, у Dire — ближний
            dist = inner + TOP_PITCH * (4 - k if side == "radiant" else k)
            cx = -dist if side == "radiant" else dist
            out.append(_box(size, cx - TOP_HALF_W, TOP_Y[0], cx + TOP_HALF_W, TOP_Y[1]))
    return out


def name_boxes(size) -> list:
    """Места имён игроков под клетками верхней полосы, в том же порядке."""
    out = []
    for l, t, r, b in top_slots(size):
        cx = (l + r) / 2
        _, s = _scale(size)
        out.append((round(cx - NAME_HALF_W * s), round(NAME_Y[0] * s),
                    round(cx + NAME_HALF_W * s), round(NAME_Y[1] * s)))
    return out


def board_cells(size, first: str) -> list:
    """24 клетки доски Captains Mode по ходам, если первым ходит first."""
    from .draft import CM_ORDER
    second = "dire" if first == "radiant" else "radiant"
    out = []
    for i, (who, kind) in enumerate(CM_ORDER):
        side = first if who == "first" else second
        x0, x1 = BOARD_X[(side, kind)]
        y0 = BOARD_Y[i]
        out.append(_box(size, x0, y0, x1, y0 + BOARD_H[kind]))
    return out


# ── Признаки и сравнение ──────────────────────────────────────────────────────

FEATURE_SIZE = (32, 18)
#: Выровненные каналы хранятся в 8 битах: среднее 128, разброс SPREAD.
SPREAD = 40.0

#: Какая часть клетки сравнивается (без скошенных краёв и рамки) и какая часть
#: портрета CDN ей соответствует — в долях (лево, верх, право, низ). Окна
#: подобраны перебором по известным героям на снимках (прототип, октябрь 2026).
KINDS = {
    # верхняя полоса: видна середина портрета, у Dire кадр сдвинут влево и вверх
    "top_radiant": {"cell": (0.15, 0.1, 0.85, 0.95), "portrait": (0.2, 0.15, 0.8, 0.95),
                    "gray": False},
    "top_dire": {"cell": (0.15, 0.1, 0.85, 0.95), "portrait": (0.15, 0.05, 0.75, 0.85),
                 "gray": False},
    # доска CM: клетка почти в пропорциях портрета, виден он весь. Пик
    # цветной; бан серый, тёмный и перечёркнут — сравнение только по яркости и
    # без краёв, где крестик. На старой доске (22 хода) так узнались 7 пиков
    # из 7 с отрывом от 0,25 и 9 банов из 10 с отрывом от 0,27; у десятого
    # отрыв 0,03 — он остаётся под вопросом.
    "pick": {"cell": (0.1, 0.1, 0.9, 0.9), "portrait": (0.1, 0.1, 0.9, 0.9),
             "gray": False},
    "ban": {"cell": (0.15, 0.1, 0.85, 0.9), "portrait": (0.15, 0.1, 0.85, 0.9),
            "gray": True},
}

#: Фон под прозрачными краями портрета — как фон клеток в игре.
PORTRAIT_BG = (20, 22, 26)


def _crop(img, frac):
    w, h = img.size
    l, t, r, b = frac
    return img.crop((round(l * w), round(t * h), round(r * w), round(b * h)))


def _normalize_band(band):
    stat = ImageStat.Stat(band)
    mean, sd = stat.mean[0], stat.stddev[0] or 1.0
    k = SPREAD / sd
    return band.point(lambda v: max(0, min(255, round(128 + (v - mean) * k))))


def features(img, frac, gray=False):
    """Маленькая выровненная картинка части frac: по ней и идёт сравнение."""
    part = _crop(img.convert("RGB"), frac).resize(FEATURE_SIZE, Image.Resampling.BILINEAR)
    if gray:
        return _normalize_band(ImageOps.grayscale(part))
    return Image.merge("RGB", [_normalize_band(b) for b in part.split()])


def flatten(portrait):
    """Портрет с прозрачностью — на фон клетки."""
    img = portrait.convert("RGBA")
    bg = Image.new("RGB", img.size, PORTRAIT_BG)
    bg.paste(img, mask=img.getchannel("A"))
    return bg


class Matcher:
    """Сравнение клетки со всеми портретами разом.

    Для каждого вида клетки (KINDS) — полоса-атлас из признаков всех портретов
    подряд. Клетка размножается на ту же длину, разница считается одной
    операцией PIL, а среднее по каждому куску — сжатием полосы до одной
    точки на портрет. Расстояние — средняя абсолютная разница в единицах
    разброса: устойчивее квадрата к значкам и крестику поверх портрета.

    Образцы (`add_sample`) — клетки, которые подтвердил пользователь: герой в
    косметике сравнивается и с ними.
    """

    def __init__(self, portraits: dict, samples=()):
        """portraits — {герой: портрет CDN}; samples — [(вид, герой, клетка)]."""
        self._names = {kind: [] for kind in KINDS}
        self._tiles = {kind: [] for kind in KINDS}
        self._atlas = {}
        for hero, img in portraits.items():
            flat = flatten(img)
            for kind, spec in KINDS.items():
                self._names[kind].append(hero)
                self._tiles[kind].append(features(flat, spec["portrait"], spec["gray"]))
        for kind, hero, cell in samples:
            if kind in KINDS and hero in portraits:
                spec = KINDS[kind]
                self._names[kind].append(hero)
                self._tiles[kind].append(features(cell, spec["cell"], spec["gray"]))
        self._build()

    def _build(self):
        w, h = FEATURE_SIZE
        for kind, tiles in self._tiles.items():
            mode = "L" if KINDS[kind]["gray"] else "RGB"
            atlas = Image.new(mode, (w * max(1, len(tiles)), h))
            for i, tile in enumerate(tiles):
                atlas.paste(tile, (i * w, 0))
            self._atlas[kind] = atlas

    @property
    def heroes(self) -> set:
        return set(self._names["pick"])

    def add_sample(self, kind: str, hero: str, cell) -> None:
        """Подтверждённая клетка как ещё один образец героя для этого вида."""
        spec = KINDS[kind]
        self._names[kind].append(hero)
        self._tiles[kind].append(features(cell, spec["cell"], spec["gray"]))
        self._build()

    def rank(self, cell, kind: str, top: int = 3) -> list:
        """Ближайшие герои: [(расстояние, герой)], по возрастанию, без повторов."""
        spec = KINDS[kind]
        f = features(cell, spec["cell"], spec["gray"])
        atlas = self._atlas[kind]
        n = len(self._names[kind])
        if not n:
            return []
        w, h = FEATURE_SIZE
        tiled = Image.new(atlas.mode, atlas.size)
        for i in range(n):
            tiled.paste(f, (i * w, 0))
        diff = ImageChops.difference(atlas, tiled).resize((n, 1), Image.Resampling.BOX)
        bands = diff.split()
        best = {}
        for i, hero in enumerate(self._names[kind]):
            d = sum(b.getpixel((i, 0)) for b in bands) / len(bands) / SPREAD
            if hero not in best or d < best[hero]:
                best[hero] = d
        return sorted((d, hero) for hero, d in best.items())[:top]


# ── Состояние клетки ──────────────────────────────────────────────────────────
#
# Портрет пёстрый почти везде, а пустая клетка гладкая: тёмный градиент или
# чёрный прямоугольник доски. Но на пустой клетке бывает значок ранга или
# уровня, а герой «под курсором» у игрока, который ещё не выбрал, — серый и
# блёклый. Поэтому мерится разброс яркости по кускам 3×3 и берётся медиана:
# значок занимает один-два куска и на неё не влияет. Замер: пустые 3–4, со
# значком 11–15, наведённый герой 8–10, выбранный — от 20.

#: Медиана разброса яркости, с которой клетка считается занятой героем.
HERO_TEXTURE = 17.0
#: Чёрная клетка доски: темнее этого и глаже EMPTY_TEXTURE.
BLACK_LIGHT = 25.0
EMPTY_TEXTURE = 6.0


def texture(cell) -> float:
    """Медиана разброса яркости по кускам 3×3 середины клетки."""
    g = _crop(cell.convert("L"), (0.1, 0.1, 0.9, 0.9))
    w, h = g.size
    if w < 3 or h < 3:
        return 0.0
    values = sorted(ImageStat.Stat(g.crop((i * w // 3, j * h // 3,
                                           (i + 1) * w // 3, (j + 1) * h // 3))).stddev[0]
                    for i in range(3) for j in range(3))
    return values[4]


def is_black(cell) -> bool:
    """Пустая клетка доски Captains Mode — чёрный прямоугольник."""
    g = _crop(cell.convert("L"), (0.15, 0.15, 0.85, 0.85))
    stat = ImageStat.Stat(g)
    return stat.mean[0] < BLACK_LIGHT and stat.stddev[0] < EMPTY_TEXTURE


def has_hero(cell) -> bool:
    return texture(cell) >= HERO_TEXTURE


#: Порог уверенности: расстояние до лучшего героя не больше MAX_DISTANCE и
#: отрыв от второго не меньше MIN_MARGIN. Замер на снимках: у верных пиков
#: расстояние 0,2–0,7 и отрыв 0,2–0,65; у неверных отрыв до 0,05.
MAX_DISTANCE = 0.75
MIN_MARGIN = 0.12


@dataclass
class Cell:
    """Что видно в клетке.

    hero_seen — в клетке выбранный герой (а не пусто и не наведённый).
    candidates — ближайшие герои [(расстояние, герой)]; hero — уверенно
    узнанный или None: тогда клетка под вопросом и выбирает пользователь.
    image — сама клетка: подтверждённую пользователь превращает в образец.
    """
    hero_seen: bool
    kind: str = ""
    candidates: list = field(default_factory=list)
    hero: str | None = None
    image: object = None

    @property
    def margin(self) -> float:
        if len(self.candidates) < 2:
            return 0.0
        return self.candidates[1][0] - self.candidates[0][0]

    @property
    def unsure(self) -> bool:
        return self.hero_seen and self.hero is None


def judge(candidates: list) -> str | None:
    """Уверенно узнанный герой по ближайшим или None."""
    if not candidates:
        return None
    best, hero = candidates[0]
    second = candidates[1][0] if len(candidates) > 1 else best + 1
    if best <= MAX_DISTANCE and second - best >= MIN_MARGIN:
        return hero
    return None


def resolve_duplicates(cells: list) -> None:
    """Один герой не бывает в двух клетках: при совпадении уверенным остаётся
    тот, у кого больше отрыв, другой становится вопросом."""
    owner = {}
    for i, cell in enumerate(cells):
        if not cell.hero:
            continue
        j = owner.get(cell.hero)
        if j is None:
            owner[cell.hero] = i
        elif cells[j].margin >= cell.margin:
            cell.hero = None
        else:
            cells[j].hero = None
            owner[cell.hero] = i


# ── Подгонка разметки ─────────────────────────────────────────────────────────
#
# Сдвиг клетки на 6 опорных точек роняет отрыв верного героя от второго с 0,57
# до 0,11, а разметка измерена по немногим снимкам. Поэтому для каждой группы
# клеток (сторона верхней полосы, доска) ищется общий сдвиг, при котором
# занятые клетки ближе всего к своим героям: сначала грубо, потом точнее.
# Найденный сдвиг держится, пока не изменится размер окна.

COARSE = [(dx, dy) for dx in range(-16, 17, 4) for dy in range(-8, 9, 4)]
FINE = [(dx, dy) for dx in (-2, 0, 2) for dy in (-2, 0, 2)]


def shift_box(box, dx, dy, size):
    _, s = _scale(size)
    l, t, r, b = box
    return (round(l + dx * s), round(t + dy * s), round(r + dx * s), round(b + dy * s))


def find_shift(img, boxes, kinds, matcher) -> tuple:
    """Общий сдвиг (dx, dy) в опорных точках для клеток boxes с героями."""
    def score(dx, dy):
        total = 0.0
        for box, kind in zip(boxes, kinds):
            ranked = matcher.rank(img.crop(shift_box(box, dx, dy, img.size)), kind, top=1)
            total += ranked[0][0] if ranked else 1.0
        return total

    if not boxes:
        return (0, 0)
    _, (bx, by) = min((score(dx, dy), (dx, dy)) for dx, dy in COARSE)
    _, best = min((score(bx + dx, by + dy), (bx + dx, by + dy)) for dx, dy in FINE)
    return best


# ── Чтение снимка ─────────────────────────────────────────────────────────────

@dataclass
class Reading:
    """Что видно на снимке.

    mode — «allpick» или «captains». cells — для All Pick десять клеток
    верхней полосы (Radiant 0–4, Dire 5–9), для Captains Mode — 24 хода
    доски; клетки после первой пустой хода ещё не сделаны. Если на снимке
    не драфт (меню, загрузка, сама игра), cells пуст. first — кто ходит
    первым в Captains Mode, ours — наша сторона; None — не удалось понять.
    """
    mode: str
    cells: list

    @property
    def present(self) -> bool:
        return bool(self.cells)
    first: str | None = None
    ours: str | None = None
    local: int | None = None   # All Pick: клетка самого игрока


#: Своё имя в верхней полосе ярко-белое: самые яркие точки ≥ 200, у чужих
#: ≤ 170. Своим считается имя, которое ярче следующего на столько.
NAME_GAP = 30

#: Подпись своей стороны над доской цветная: насыщенных точек нужного оттенка
#: в её прямоугольнике не меньше этой доли.
LABEL_SHARE = 0.04


def local_slot(img) -> int | None:
    """Клетка самого игрока: под ней самое яркое имя, заметно ярче прочих."""
    scores = []
    for i, box in enumerate(name_boxes(img.size)):
        hist = img.crop(box).convert("L").histogram()
        # среднее 30 самых ярких точек
        left, total, value = 30, 0, 255
        while left > 0 and value >= 0:
            take = min(left, hist[value])
            total += take * value
            left -= take
            value -= 1
        scores.append((total / 30, i))
    scores.sort(reverse=True)
    if scores[0][0] - scores[1][0] >= NAME_GAP:
        return scores[0][1]
    return None


def _label_share(img, side) -> float:
    x0, x1 = BOARD_LABEL_X[side]
    part = img.crop(_box(img.size, x0, BOARD_LABEL_Y[0], x1, BOARD_LABEL_Y[1])).convert("HSV")
    hue, sat, val = part.split()
    # оттенок в PIL — 0–255 по кругу: зелёный около 85, красный около 0
    if side == "radiant":
        hue_ok = hue.point(lambda h: 255 if 60 <= h <= 110 else 0)
    else:
        hue_ok = hue.point(lambda h: 255 if h <= 12 or h >= 244 else 0)
    mask = ImageChops.multiply(hue_ok, ImageChops.multiply(
        sat.point(lambda v: 255 if v > 110 else 0), val.point(lambda v: 255 if v > 110 else 0)))
    return mask.histogram()[255] / max(1, part.width * part.height)


def our_board_side(img) -> str | None:
    """Наша сторона по подписи над доской: у своей она цветная."""
    shares = {side: _label_share(img, side) for side in SIDES}
    lit = [side for side, share in shares.items() if share >= LABEL_SHARE]
    return lit[0] if len(lit) == 1 else None


#: Цвета игроков в верхней полосе (Radiant 1–5, Dire 1–5) — одни во всех
#: замерах. Полоска под пустой клеткой и над портретом выбравшего.
PLAYER_COLORS = ((51, 114, 249), (100, 249, 188), (188, 0, 188), (238, 234, 10), (250, 105, 0),
                 (247, 130, 190), (158, 177, 70), (99, 213, 241), (1, 130, 32), (162, 102, 0))
#: Полосы, где ищется полоска: над клеткой и под ней, опорные y.
BAR_BANDS = ((0, 9), (64, 73))
#: Насколько цвет полоски может отличаться (сумма разниц каналов) и сколько
#: полосок должно найтись, чтобы считать, что на экране драфт.
BAR_TOLERANCE = 70
BAR_MIN = 6


def _bar_found(img, box, color) -> bool:
    l, t, r, b = box
    cx, hw = (l + r) / 2, (r - l) * 0.3
    _, s = _scale(img.size)
    for y0, y1 in BAR_BANDS:
        band = img.crop((round(cx - hw), round(y0 * s), round(cx + hw), max(round(y1 * s),
                                                                            round(y0 * s) + 1)))
        for y in range(band.height):
            mean = ImageStat.Stat(band.crop((0, y, band.width, y + 1))).mean
            if sum(abs(a - b) for a, b in zip(mean, color)) <= BAR_TOLERANCE:
                return True
    return False


def top_bar_present(img) -> bool:
    """Есть ли на снимке верхняя полоса драфта: цветные полоски игроков на местах.
    В меню, на загрузке и в самой игре их там нет — тогда снимок не читается."""
    img = img.convert("RGB")
    found = sum(_bar_found(img, box, color)
                for box, color in zip(top_slots(img.size), PLAYER_COLORS))
    return found >= BAR_MIN


def _cellness(img, box) -> bool:
    """Похоже ли место на клетку доски: чёрная пустая или с героем.
    Фон доски — гладкий и не чёрный."""
    cell = img.crop(box)
    return is_black(cell) or has_hero(cell)


#: Доска на экране: при лучшей раскладке клеток на местах не меньше BOARD_MIN
#: из 24, и она лучше другой хотя бы на FIRST_GAP (раскладки различаются
#: всего несколькими местами: на пустой доске 24 против 22).
BOARD_MIN = 20
FIRST_GAP = 2


def board_scores(img) -> dict:
    """Сколько мест ходов похожи на клетки при каждой раскладке."""
    img = img.convert("RGB")
    return {first: sum(_cellness(img, box) for box in board_cells(img.size, first))
            for first in SIDES}


def first_side(img, scores=None) -> str | None:
    """Кто ходит первым: при какой раскладке на местах ходов стоят клетки."""
    scores = scores or board_scores(img)
    a, b = scores["radiant"], scores["dire"]
    if abs(a - b) < FIRST_GAP:
        return None
    return "radiant" if a > b else "dire"


def board_present(img, scores=None) -> bool:
    scores = scores or board_scores(img)
    return max(scores.values()) >= BOARD_MIN


class Reader:
    """Чтение снимков с подгонкой разметки под окно.

    Сдвиги запоминаются по размеру снимка и группе клеток и пересчитываются,
    пока занятых клеток в группе прибавляется (по одной-двум клеткам сдвиг
    ненадёжен), но не больше чем по SHIFT_CELLS клеткам.
    """

    SHIFT_CELLS = 3

    def __init__(self, matcher: Matcher):
        self.matcher = matcher
        self._shifts = {}   # (размер, группа) -> (сдвиг, по скольким клеткам)

    def _shift(self, img, group, boxes, kinds):
        key = (img.size, group)
        known = self._shifts.get(key)
        if known and known[1] >= min(self.SHIFT_CELLS, len(boxes)):
            return known[0]
        if not boxes:
            return known[0] if known else (0, 0)
        use = list(zip(boxes, kinds))[:self.SHIFT_CELLS]
        shift = find_shift(img, [b for b, _ in use], [k for _, k in use], self.matcher)
        self._shifts[key] = (shift, len(use))
        return shift

    def _cells(self, img, boxes, kinds, seen):
        cells = []
        for box, kind, hero_seen in zip(boxes, kinds, seen):
            if not hero_seen:
                cells.append(Cell(False, kind))
                continue
            image = img.crop(box)
            ranked = self.matcher.rank(image, kind)
            cells.append(Cell(True, kind, ranked, judge(ranked), image))
        resolve_duplicates(cells)
        return cells

    def read_allpick(self, img) -> Reading:
        img = img.convert("RGB")
        if not top_bar_present(img):
            return Reading("allpick", [])
        boxes = top_slots(img.size)
        kinds = ["top_radiant"] * 5 + ["top_dire"] * 5
        seen = [has_hero(img.crop(b)) for b in boxes]
        for side, part in (("radiant", range(0, 5)), ("dire", range(5, 10))):
            filled = [i for i in part if seen[i]]
            dx, dy = self._shift(img, side, [boxes[i] for i in filled], [kinds[i] for i in filled])
            for i in part:
                boxes[i] = shift_box(boxes[i], dx, dy, img.size)
        seen = [has_hero(img.crop(b)) for b in boxes]
        local = local_slot(img)
        ours = None if local is None else ("radiant" if local < 5 else "dire")
        return Reading("allpick", self._cells(img, boxes, kinds, seen), ours=ours, local=local)

    def read_captains(self, img, first: str | None = None) -> Reading:
        """Доска Captains Mode. first — кто ходит первым, если снимок этого
        не показывает (до первого хода оба места пусты одинаково)."""
        from .draft import CM_ORDER
        img = img.convert("RGB")
        scores = board_scores(img)
        if not board_present(img, scores):
            return Reading("captains", [])
        found = first_side(img, scores)
        first = found or first or "radiant"
        boxes = board_cells(img.size, first)
        kinds = [kind for _, kind in CM_ORDER]
        # ходы делаются по порядку: после первой не занятой клетки дальше не смотрим
        seen = []
        for box in boxes:
            seen.append(has_hero(img.crop(box)) and (not seen or seen[-1]))
        filled = [i for i, s in enumerate(seen) if s]
        dx, dy = self._shift(img, "board", [boxes[i] for i in filled], [kinds[i] for i in filled])
        boxes = [shift_box(b, dx, dy, img.size) for b in boxes]
        seen = []
        for box in boxes:
            seen.append(has_hero(img.crop(box)) and (not seen or seen[-1]))
        return Reading("captains", self._cells(img, boxes, kinds, seen),
                       first=found, ours=our_board_side(img))


# ── Несколько снимков подряд ──────────────────────────────────────────────────

#: Сколько снимков подряд клетка должна показывать одно и то же, чтобы это
#: записалось. Снимок раз в секунду — запись через пару секунд после пика.
AGREE = 3


class Tracker:
    """Что видно устойчиво: клетка записывается, только если AGREE снимков
    подряд показывают в ней одно и то же. Так не записываются мелькнувший
    при анимации кадр и герой, которого игрок лишь навёл.

    Значение клетки: имя героя, «?» (герой есть, но не узнан) или None (пусто).
    """

    def __init__(self, agree: int = AGREE):
        self.agree = agree
        self._key = None
        self._runs = {}     # клетка -> (значение, сколько снимков подряд)

    def update(self, reading: Reading) -> dict:
        """Учесть снимок; вернуть {клетка: значение} для устойчивых клеток."""
        key = (reading.mode, len(reading.cells))
        if key != self._key:
            self._key, self._runs = key, {}
        stable = {}
        for i, cell in enumerate(reading.cells):
            value = (cell.hero or "?") if cell.hero_seen else None
            old, count = self._runs.get(i, (None, 0))
            count = count + 1 if value == old else 1
            self._runs[i] = (value, count)
            if count >= self.agree:
                stable[i] = value
        return stable

    def reset(self):
        self._key, self._runs = None, {}


# ── Перенос в драфт ───────────────────────────────────────────────────────────

def apply_allpick(board, stable: dict, ours: str | None, applied: dict) -> list:
    """Устойчиво узнанных героев верхней полосы — в состав All Pick.

    Наша сторона — в «Свои», чужая — во «Враги». applied — {клетка: герой},
    что уже перенесено: каждая находка переносится один раз, поэтому героя,
    которого пользователь убрал руками, экран не вернёт, пока в клетке не
    появится другой. Если в клетке сменился герой или она опустела (начался
    новый драфт), прежний — перенесённый отсюда же — убирается.
    Возвращает (перенесённые, убранные).
    """
    if ours is None:
        return [], []
    done, gone = [], []
    for slot, hero in sorted(stable.items()):
        old = applied.get(slot)
        # клетка опустела или в ней теперь неузнанный герой: прежнего там нет —
        # узнанный однажды, он и дальше узнавался бы уверенно
        if hero in (None, "?") and old:
            if board.group_of(old):
                board.remove(old)
                gone.append(old)
            del applied[slot]
            continue
        if not hero or hero == "?" or old == hero:
            continue
        if old and board.group_of(old):
            board.remove(old)
            gone.append(old)
        side = "radiant" if slot < 5 else "dire"
        group = "allies" if side == ours else "enemies"
        if board.add(group, hero) in ("added", "moved", "dup"):
            applied[slot] = hero
            done.append(hero)
    return done, gone


def apply_captains(draft, stable: dict) -> tuple:
    """Устойчиво узнанные ходы доски — в драфт Captains Mode, по порядку.

    Записываются только ходы подряд с текущего: на первом пустом, «?» или
    ещё не устоявшемся ходу запись останавливается. Если экран показывает
    меньше сделанных ходов, чем записано (начался новый драфт или ход
    записали заранее), лишние ходы снимаются. Записанное другим героем не
    переписывается: номер такого хода возвращается как расхождение.
    Возвращает (записанные герои, сколько ходов снято, расхождение или None).
    """
    played, undone = [], 0
    empty = next((i for i in range(len(draft.heroes)) if i in stable and stable[i] is None), None)
    if empty is not None:
        while (draft.current is None or draft.current > empty) and draft.undo():
            undone += 1
    for index, hero in enumerate(draft.heroes):
        seen = stable.get(index)
        if hero is not None:
            if seen and seen != "?" and seen != hero:
                return played, undone, index
            continue
        if not seen or seen == "?" or index != draft.current:
            break
        if draft.play(seen) != "ok":
            return played, undone, index
        played.append(seen)
    return played, undone, None


# ── Образцы ───────────────────────────────────────────────────────────────────
#
# Клетку, которую пользователь подтвердил сам, программа запоминает как ещё
# один образец героя: герой в косметике с другим портретом в следующий раз
# узнаётся по ней. Образцы лежат в cache/samples/<вид>/<герой>__<n>.png, не
# больше MAX_SAMPLES на героя и вид — новый вытесняет самый старый.

MAX_SAMPLES = 3


def _sample_name(hero: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in hero)


def save_sample(folder, kind: str, hero: str, image) -> None:
    import os
    if not folder or kind not in KINDS or image is None:
        return
    path = os.path.join(folder, kind)
    prefix = _sample_name(hero) + "__"
    try:
        os.makedirs(path, exist_ok=True)
        numbers = []
        for name in os.listdir(path):
            tail = name[len(prefix):-4] if name.startswith(prefix) and name.endswith(".png") else ""
            if tail.isdigit():
                numbers.append(int(tail))
        numbers.sort()
        for n in numbers[:max(0, len(numbers) - MAX_SAMPLES + 1)]:
            os.remove(os.path.join(path, "%s%d.png" % (prefix, n)))
        new = (numbers[-1] + 1) if numbers else 1
        image.convert("RGB").save(os.path.join(path, "%s%d.png" % (prefix, new)))
    except OSError:
        pass


def load_samples(folder, heroes) -> list:
    """[(вид, герой, картинка)] из папки образцов; незнакомые имена пропускаются."""
    import os
    if not folder or not os.path.isdir(folder):
        return []
    by_name = {_sample_name(h): h for h in heroes}
    out = []
    for kind in KINDS:
        path = os.path.join(folder, kind)
        if not os.path.isdir(path):
            continue
        for name in os.listdir(path):
            hero = by_name.get(name.split("__", 1)[0])
            if hero is None or not name.endswith(".png"):
                continue
            try:
                with Image.open(os.path.join(path, name)) as img:
                    out.append((kind, hero, img.convert("RGB")))
            except OSError:
                continue
    return out
