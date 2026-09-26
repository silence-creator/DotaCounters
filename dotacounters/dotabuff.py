"""Получение и разбор таблиц контрпиков с Dotabuff.

Разбор устроен так, чтобы при изменении вёрстки Dotabuff приложение падало
громко и понятно, а не показывало молча неверные цифры.

Что известно о странице /heroes/<slug>/counters на момент написания:

* таблиц на ней **три** — «X is countered by», «X counters» и большая
  «Matchups» на 126 строк. Брать первые две по счёту — совпадение, а не
  правило, поэтому нужные разделы опознаются по заголовку над таблицей;
* в <thead> три колонки, а в строке <tbody> — четыре: у первой ячейки с
  иконкой героя заголовка нет. Поэтому «i-й заголовок = i-я ячейка» неверно,
  индексы сдвинуты, и сдвиг вычисляется явно;
* значения продублированы в атрибуте data-value в машинном виде.
"""

import re
import time
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

from .net import create_scraper

BASE_URL = "https://www.dotabuff.com"

_WIN_RATE_RE = re.compile(r"win\s*rate", re.I)
_ADVANTAGE_RE = re.compile(r"advantage|disadvantage|\badv\b|\bdis\b", re.I)
_MATCHES_RE = re.compile(r"\bmatches\b", re.I)
_PERCENT_RE = re.compile(r"^-?\d{1,3}(?:[.,]\d+)?%$")
_COUNTERED_BY_RE = re.compile(r"is\s+countered\s+by", re.I)
_COUNTERS_RE = re.compile(r"\bcounters\b", re.I)
_MATCHUPS_RE = re.compile(r"\bmatchups\b", re.I)

#: Сколько строк показывать в каждом разделе по умолчанию — столько же, сколько
#: в коротких таблицах Dotabuff.
DEFAULT_LIMIT = 5
#: Верхняя граница выбора в интерфейсе.
MAX_LIMIT = 12
#: Пары, сыгранные реже, считаются шумом: при 2000 матчей погрешность винрейта
#: около ±1,1 п.п., а типичное преимущество в паре — 0,8. Замер по всем героям
#: (7.41f): таких пар 0,5%, почти все — с Chen, Batrider, Elder Titan, Lycan,
#: Visage, Brewmaster. В разделах поиска их нет, в драфте они дают ноль.
MIN_MATCHES = 2000
#: Паузы перед повторами запроса, отбитого с 403. Cloudflare отвечает так
#: примерно на четверть холодных запросов; на замере из 12 страниц одной
#: попытки хватило 8 раз, двух — 10, трёх — 11.
RETRY_PAUSES = (0.6, 1.5)


# ── Ошибки ────────────────────────────────────────────────────────────────────


class DotabuffError(Exception):
    """Общий предок ошибок работы с Dotabuff."""


class FetchError(DotabuffError):
    """Страницу не удалось получить: сеть или неожиданный HTTP-код."""


class HeroNotFound(FetchError):
    """Dotabuff не знает такого героя — обычно опечатка в имени."""


class ParseError(DotabuffError):
    """Страница получена, но её структура не та, что ожидалась."""


# ── Результат ─────────────────────────────────────────────────────────────────

@dataclass
class Matchup:
    """Одна строка таблицы: соперник и статистика против него."""
    hero: str
    win_rate: str
    advantage: str | None = None
    icon_url: str | None = None
    #: Преимущество числом из data-value: насколько хуже играет герой страницы
    #: против этого соперника. Положительное — соперник его контрит.
    advantage_value: float | None = None
    #: Сколько матчей сыграно в этой паре — только в полной таблице «Matchups».
    matches: int | None = None


@dataclass
class CounterReport:
    """Разобранная страница контрпиков одного героя."""
    hero_slug: str
    countered_by: list = field(default_factory=list)  # против кого играет слабее
    counters: list = field(default_factory=list)      # против кого играет сильнее
    #: Полная таблица «Matchups» — все герои, по убыванию преимущества над
    #: нашим. Из неё берутся разделы, когда нужно больше пяти строк.
    matchups: list = field(default_factory=list)
    #: True, если разделы пришлось определять по позиции, а не по заголовку —
    #: данные показываются, но с предупреждением.
    degraded: bool = False
    #: Короткие таблицы Dotabuff — запасной источник разделов, когда полной
    #: таблицы нет или в ней мало надёжных строк. Иначе не разбираются.
    short_countered_by: list = field(default_factory=list)
    short_counters: list = field(default_factory=list)
    #: Сколько секунд назад страница скачана, если взята из кеша; иначе None.
    cached_age: float | None = None


def reliable(matchup) -> bool:
    """Достаточно ли матчей в паре, чтобы верить её цифре."""
    return matchup.matches is None or matchup.matches >= MIN_MATCHES


# ── Разбор ────────────────────────────────────────────────────────────────────

def hero_slug(hero_name: str) -> str:
    """«Anti-Mage» -> «anti-mage», «Nature's Prophet» -> «natures-prophet»."""
    return hero_name.strip().lower().replace(" ", "-").replace("'", "")


def _table_headers(table) -> list:
    thead = table.find("thead")
    if thead is None:
        return []
    return [th.get_text(" ", strip=True) for th in thead.find_all("th")]


def _column_map(headers: list, n_cells: int) -> dict:
    """Сопоставить заголовки колонок с индексами ячеек строки.

    Первая ячейка строки — иконка героя, заголовка у неё нет, поэтому <thead>
    короче строки. Разница длин и есть сдвиг, на который смещены все колонки.
    """
    offset = n_cells - len(headers)
    if offset < 0:
        raise ParseError(
            "в строке %d ячеек, а заголовков %d — колонок меньше, чем подписей"
            % (n_cells, len(headers))
        )

    idx = {}
    for i, header in enumerate(headers):
        cell = i + offset
        if "win_rate" not in idx and _WIN_RATE_RE.search(header):
            idx["win_rate"] = cell
        elif "hero" not in idx and header.strip().lower() == "hero":
            idx["hero"] = cell
        elif "advantage" not in idx and _ADVANTAGE_RE.search(header):
            idx["advantage"] = cell
        elif "matches" not in idx and _MATCHES_RE.search(header):
            idx["matches"] = cell

    missing = [k for k in ("hero", "win_rate") if k not in idx]
    if missing:
        raise ParseError(
            "не найдены колонки %s среди заголовков %s"
            % (", ".join(missing), headers or "(таблица без <thead>)")
        )
    return idx


def _icon_url(row) -> str | None:
    img = row.find("img")
    src = img.get("src") if img else None
    if not src:
        return None
    return BASE_URL + src if src.startswith("/") else src


def _to_float(value) -> float | None:
    """«3.2809» -> 3.2809; «—», пусто и мусор -> None."""
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _cell_text(cell) -> str:
    """Предпочитаем data-value: там значение без форматирования."""
    return (cell.get("data-value") or cell.get_text(strip=True) or "").strip()


def _parse_rows(table, idx: dict) -> list:
    body = table.find("tbody")
    rows = body.find_all("tr") if body else table.find_all("tr")
    last = max(idx.values())
    out = []

    for row in rows:
        cells = row.find_all("td")
        if len(cells) <= last:
            continue  # строки-разделители и прочий шум

        hero = _cell_text(cells[idx["hero"]])
        win_rate = cells[idx["win_rate"]].get_text(strip=True)
        if not hero:
            continue

        # Главная проверка: если на месте винрейта не процент, вёрстка
        # разъехалась. Молча показать это число нельзя — оно будет неверным.
        if not _PERCENT_RE.match(win_rate):
            raise ParseError(
                "в колонке винрейта оказалось %r вместо процента — "
                "колонки Dotabuff сместились" % win_rate[:40]
            )

        advantage, advantage_value = None, None
        if "advantage" in idx and len(cells) > idx["advantage"]:
            cell = cells[idx["advantage"]]
            advantage = cell.get_text(strip=True) or None
            advantage_value = _to_float(cell.get("data-value"))

        matches = None
        if "matches" in idx and len(cells) > idx["matches"]:
            value = _to_float(cells[idx["matches"]].get("data-value"))
            matches = int(value) if value is not None else None

        out.append(Matchup(hero=hero, win_rate=win_rate, advantage=advantage,
                           icon_url=_icon_url(row), advantage_value=advantage_value,
                           matches=matches))
    return out


def _classify(table) -> str | None:
    """Определить раздел по заголовку над таблицей."""
    heading = table.find_previous(["h1", "h2", "h3", "header"])
    text = heading.get_text(" ", strip=True) if heading else ""
    if _COUNTERED_BY_RE.search(text):
        return "countered_by"
    if _COUNTERS_RE.search(text):
        return "counters"
    if _MATCHUPS_RE.search(text):
        return "matchups"
    return None


def _rows_of(table, kind: str = "") -> list:
    """Разобрать таблицу целиком, определив колонки по её заголовкам."""
    body = table.find("tbody")
    first = body.find("tr") if body else table.find("tr")
    if first is None:
        raise ParseError("таблица «%s» пуста" % (kind or "?"))
    idx = _column_map(_table_headers(table), len(first.find_all("td")))
    return _parse_rows(table, idx)


def parse_counters(html: str, slug: str = "",
                   limit: int = DEFAULT_LIMIT) -> CounterReport:
    """Разобрать HTML страницы контрпиков. Бросает ParseError при несовпадении.

    limit — сколько строк вернуть в каждом разделе. Короткие таблицы Dotabuff
    содержат ровно пять строк, поэтому для больших значений разделы берутся
    из полной таблицы «Matchups»: она отсортирована по убыванию преимущества
    соперника, так что начало — те, против кого играть хуже всего, а конец —
    те, против кого лучше всего.
    """
    limit = max(1, min(int(limit), MAX_LIMIT))

    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        raise ParseError("на странице нет ни одной таблицы")

    picked, degraded = {}, False
    for table in tables:
        kind = _classify(table)
        if kind and kind not in picked:
            picked[kind] = table

    if "countered_by" not in picked or "counters" not in picked:
        # Заголовки не опознаны. Не падаем, а откатываемся к прежнему
        # поведению — первые две таблицы, — но помечаем результат как
        # ненадёжный, чтобы интерфейс предупредил пользователя.
        if len(tables) < 2:
            raise ParseError(
                "ожидались таблицы «is countered by» и «counters», "
                "найдено таблиц: %d" % len(tables)
            )
        degraded = True
        picked["countered_by"] = tables[0]
        picked["counters"] = tables[1]

    report = CounterReport(hero_slug=slug, degraded=degraded)

    if "matchups" in picked:
        report.matchups = _rows_of(picked["matchups"], "matchups")

    # Короткие таблицы нужны, только если полной не хватит на самый большой
    # выбор «КОЛ-ВО». Разбираем их лишь тогда: если они сломаны, а полная цела,
    # данные всё равно есть. В кеш уходит то, из чего разделы собираются для
    # любого limit.
    if sum(1 for m in report.matchups if reliable(m)) < 2 * MAX_LIMIT:
        report.short_countered_by = _rows_of(picked["countered_by"], "countered_by")
        report.short_counters = _rows_of(picked["counters"], "counters")

    select_sections(report, limit)
    if not report.countered_by and not report.counters:
        raise ParseError("таблицы найдены, но ни одной строки разобрать не удалось")
    return report


def select_sections(report: CounterReport, limit: int = DEFAULT_LIMIT) -> CounterReport:
    """Разделы «слабее против» и «сильнее против» на limit строк.

    Берутся из полной таблицы без редких пар (MIN_MATCHES): она отсортирована
    по убыванию преимущества соперника, начало — против кого хуже всего, конец —
    против кого лучше. Голова и хвост не должны пересечься, поэтому полная
    таблица идёт в дело, только когда надёжных строк хватает на оба раздела;
    иначе — короткие таблицы Dotabuff как есть.
    """
    limit = max(1, min(int(limit), MAX_LIMIT))
    rows = [m for m in report.matchups if reliable(m)]
    if len(rows) >= 2 * limit:
        report.countered_by = rows[:limit]
        report.counters = list(reversed(rows[-limit:]))
    else:
        report.countered_by = report.short_countered_by[:limit]
        report.counters = report.short_counters[:limit]
    return report


# ── Сеть ──────────────────────────────────────────────────────────────────────

def fetch_counters(hero_name: str, scraper=None,
                   limit: int = DEFAULT_LIMIT, cache=None) -> CounterReport:
    """Скачать и разобрать страницу контрпиков героя.

    cache — pagecache.PageCache: свежая сохранённая страница берётся оттуда
    без сети, скачанная — сохраняется туда.
    """
    slug = hero_slug(hero_name)
    if cache is not None:
        hit = cache.load(slug)
        if hit is not None:
            return select_sections(hit, limit)
    report = _download(hero_name, slug, scraper, limit)
    if cache is not None:
        cache.save(slug, report)
    return report


def _download(hero_name: str, slug: str, scraper, limit: int) -> CounterReport:
    scraper = scraper or create_scraper()
    url = "%s/heroes/%s/counters" % (BASE_URL, slug)
    try:
        resp = scraper.get(url, timeout=10)
        for pause in RETRY_PAUSES:
            # Cloudflare отбивает часть запросов случайно; повтор тем же
            # соединением обычно проходит.
            if resp.status_code != 403:
                break
            time.sleep(pause)
            resp = scraper.get(url, timeout=10)
    except Exception as exc:
        raise FetchError(str(exc)) from exc

    if resp.status_code == 404:
        raise HeroNotFound(hero_name.strip())
    if resp.status_code != 200:
        raise FetchError("HTTP %d" % resp.status_code)

    return parse_counters(resp.text, slug, limit=limit)


def fetch_many(heroes, limit: int = DEFAULT_LIMIT, scraper=None, fetch=None, cache=None):
    """Страницы нескольких героев одной сессией: -> (отчёты, [(герой, ошибка)]).

    Одна сессия на всю серию: на серии запросов с новым соединением каждый раз
    Cloudflare отбивает часть из них. Ошибка по одному герою не прерывает
    остальных. fetch подменяется в тестах.
    """
    fetch = fetch or fetch_counters
    scraper = scraper or create_scraper()
    reports, failed = {}, []
    for hero in heroes:
        try:
            reports[hero] = fetch(hero, scraper=scraper, limit=limit, cache=cache)
        except DotabuffError as exc:
            failed.append((hero, exc))
        except Exception as exc:
            failed.append((hero, FetchError(str(exc))))
    return reports, failed
