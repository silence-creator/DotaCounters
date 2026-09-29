"""Мета героев по рангам — для банов первой фазы Captains Mode.

Первые семь ходов Captains Mode — баны до любых пиков: контрпики считать не
от чего. Остаётся мета: кто сейчас сильнее всех. Страница Dotabuff
/heroes/meta даёт для каждого героя частоту выбора (Pick %, доля матчей, где
он есть; в сумме 1000%) и винрейт — отдельно по пяти группам рангов. Период
страница не меняет: всегда последний месяц.

Кого банить: сильнейших по винрейту, но только среди тех, кого берут хотя бы в
MIN_PICK % игр. Без этого наверх выходят нишевые герои (Visage, Meepo — около
2% игр): винрейт у них высокий за счёт тех, кто на них специализируется.
"""

from dataclasses import dataclass

from bs4 import BeautifulSoup

from .dotabuff import BASE_URL, FetchError, ParseError, _get_with_retries
from .net import create_scraper

URL = BASE_URL + "/heroes/meta"
#: Группы рангов в порядке колонок страницы; «all» — среднее по ним.
BRACKETS = ("herald", "archon", "legend", "ancient", "divine")
RANKS = ("all",) + BRACKETS
#: Порог частоты выбора, %: реже берут — в баны не предлагаем.
MIN_PICK = 5.0
#: Имя в кеше страниц (pagecache.PageCache.save_data).
CACHE_NAME = "meta"


@dataclass
class MetaHero:
    """Герой в мете выбранного ранга."""
    hero: str
    win: float      # винрейт, %
    pick: float     # в какой доле матчей его берут, %


def parse_meta(html: str) -> dict:
    """Страница меты -> {герой: ((pick, win) по каждой группе BRACKETS)}.

    Колонки: иконка и имя (заголовок «Hero» на две ячейки), затем пары
    Pick % / Win % по группам рангов. Числа — из data-value.
    """
    table = BeautifulSoup(html, "html.parser").find("table")
    if table is None or table.find("tbody") is None:
        raise ParseError("на странице меты нет таблицы героев")
    columns = []
    for th in table.find("thead").find_all("tr")[-1].find_all("th"):
        columns.extend([th.get_text(" ", strip=True).lower()] * int(th.get("colspan") or 1))
    pairs = [i for i, name in enumerate(columns) if name == "pick %"]
    if len(pairs) != len(BRACKETS) or any(columns[i + 1] != "win %" for i in pairs):
        raise ParseError("колонки меты не те: %s" % columns)
    out = {}
    for row in table.find("tbody").find_all("tr"):
        cells = row.find_all("td")
        if len(cells) != len(columns):
            continue
        hero = (cells[0].get("data-value") or cells[1].get_text(strip=True)).strip()
        try:
            values = tuple((round(float(cells[i]["data-value"]), 2),
                            round(float(cells[i + 1]["data-value"]), 2)) for i in pairs)
        except (KeyError, ValueError):
            raise ParseError("у %s нет чисел в колонках меты" % hero) from None
        if hero:
            out[hero] = values
    if len(out) < 100:
        raise ParseError("в таблице меты всего %d героев" % len(out))
    return out


def fetch_meta(scraper=None, cache=None) -> dict:
    """Мета с Dotabuff; свежая из кеша — без сети. Ошибки — FetchError/ParseError."""
    if cache is not None:
        hit = cache.load_data(CACHE_NAME)
        if hit:
            return {hero: tuple(tuple(pair) for pair in values) for hero, values in hit.items()}
    scraper = scraper or create_scraper()
    try:
        resp = _get_with_retries(scraper, URL)
    except Exception as exc:
        raise FetchError(str(exc)) from exc
    if resp.status_code != 200:
        raise FetchError("HTTP %d" % resp.status_code)
    meta = parse_meta(resp.text)
    if cache is not None:
        cache.save_data(CACHE_NAME, meta)
    return meta


def in_rank(meta: dict, rank: str = "all") -> dict:
    """{герой: (pick, win)} для группы рангов; «all» — среднее по пяти группам."""
    if rank in BRACKETS:
        i = BRACKETS.index(rank)
        return {hero: values[i] for hero, values in meta.items()}
    n = len(BRACKETS)
    return {hero: (sum(p for p, _ in values) / n, sum(w for _, w in values) / n)
            for hero, values in meta.items()}


def strongest(meta: dict, rank: str = "all", allowed=None, limit: int = 5) -> list:
    """Кандидаты в бан: винрейт по убыванию среди тех, кого берут от MIN_PICK %.

    allowed(герой) -> bool — кого вообще можно предлагать (не взят, не забанен,
    подходит под фильтр позиции).
    """
    rows = [MetaHero(hero, win, pick) for hero, (pick, win) in in_rank(meta, rank).items()
            if pick >= MIN_PICK and (allowed is None or allowed(hero))]
    rows.sort(key=lambda m: (-m.win, m.hero))
    return rows[:max(1, limit)]
