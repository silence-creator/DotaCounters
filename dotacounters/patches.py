"""Данные о патчах Dota 2 из официального datafeed Valve.

fetch_current_patch() определяет номер актуального патча, fetch_patch_notes()
разбирает заметки к нему в секции, пригодные для показа в окне.
"""

import re

from bs4 import BeautifulSoup

from .net import create_scraper


def fetch_current_patch():
    scraper = create_scraper()
    # Source 1: Valve JSON API
    try:
        url = "https://www.dota2.com/datafeed/patchnoteslist?language=english"
        resp = scraper.get(url, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            patches = data.get("patches") or data.get("patch_notes") or []
            if patches:
                newest = patches[-1]
                number = (
                    newest.get("patch_number")
                    or newest.get("patch_name")
                    or newest.get("version")
                    or ""
                )
                m = re.search(r'7\.\d+[a-z]?', str(number))
                if m:
                    return m.group(0)
    except Exception:
        pass
    # Source 2: Dotabuff page
    try:
        resp = scraper.get(
            "https://www.dotabuff.com/heroes/anti-mage/counters", timeout=10
        )
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup.find_all(string=re.compile(r'(?i)patch')):
                m = re.search(r'7\.\d+[a-z]?', tag)
                if m:
                    return m.group(0)
            m = re.search(r'7\.\d+[a-z]?', resp.text)
            if m:
                return m.group(0)
    except Exception:
        pass
    return "7.41b"


# ── Заметки к патчу ───────────────────────────────────────────────────────────
#
# Формат ответа /datafeed/patchnotes (проверен на 7.41d и 7.41e):
#
#   general_notes  список [{title, generic: [{note, indent_level}]}]
#   items          список [{ability_id, ability_notes: [{note}]}]
#   neutral_items  список, где записи с is_general_note=true — заголовки уровней
#   heroes         список [{hero_id, hero_notes: [...], abilities: [...]}]
#
# Имён в ответе нет — только числовые идентификаторы, поэтому они разрешаются
# через отдельные справочники datafeed и кэшируются на время работы программы.

_NAME_FEEDS = {
    "heroes":    ("https://www.dota2.com/datafeed/herolist?language=%s", "heroes"),
    "items":     ("https://www.dota2.com/datafeed/itemlist?language=%s", "itemabilities"),
    "abilities": ("https://www.dota2.com/datafeed/abilitylist?language=%s", "itemabilities"),
}

_name_cache = {}


def _name_map(kind: str, scraper, language: str) -> dict:
    """Справочник «идентификатор -> имя» для языка. Качается раз на язык."""
    cache_key = (kind, language)
    if cache_key in _name_cache:
        return _name_cache[cache_key]
    url_tpl, data_key = _NAME_FEEDS[kind]
    url = url_tpl % language
    mapping = {}
    try:
        resp = scraper.get(url, timeout=20)
        if resp.status_code == 200:
            entries = resp.json().get("result", {}).get("data", {}).get(data_key, [])
            for entry in entries:
                name = entry.get("name_loc") or entry.get("name_english_loc")
                if name:
                    mapping[entry.get("id")] = name
    except Exception:
        pass  # без имён покажем идентификаторы, это лучше пустого окна
    _name_cache[cache_key] = mapping
    return mapping


_TAG_RE = re.compile(r"<[^>]+>")


def _clean_note(note: str) -> str:
    """Убрать HTML-теги: Valve кладёт в текст заметок <br> и подобное."""
    return " ".join(_TAG_RE.sub(" ", note).split())


def _notes_from(entries) -> list:
    """Строки заметок из [{note, indent_level}, ...] с сохранением вложенности."""
    out = []
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue
        note = _clean_note(entry.get("note") or entry.get("text") or "")
        if not note:
            continue  # заметка была одним лишь тегом
        try:
            depth = max(0, int(entry.get("indent_level", 1)) - 1)
        except (TypeError, ValueError):
            depth = 0
        out.append("    " * depth + note)
    return out


def _resolve_version(patch_version: str, scraper, language: str) -> str:
    """Уточнить внутренний ключ версии по списку патчей."""
    version = (patch_version or "").strip().strip(".")
    try:
        resp = scraper.get(
            "https://www.dota2.com/datafeed/patchnoteslist"
            "?language=%s" % language, timeout=10)
        if resp.status_code != 200:
            return version
        patches = resp.json().get("patches") or []
        for p in reversed(patches):
            names = [str(p.get(k) or "") for k in ("patch_name", "patch_number", "version")]
            if version in names:
                return str(p.get("patch_name") or p.get("patch_number") or version).strip()
        if patches and not version:
            last = patches[-1]
            return str(last.get("patch_name") or last.get("patch_number") or "").strip()
    except Exception:
        pass
    return version


def _item_section(entries, title: str, scraper, language: str) -> dict | None:
    """Секция по списку предметов; записи-заголовки уровней идут строками."""
    names, notes = None, []
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue
        if entry.get("is_general_note") and entry.get("title"):
            notes.append("— %s —" % entry["title"])
            continue
        lines = _notes_from(entry.get("ability_notes"))
        if not lines:
            continue
        if names is None:
            names = _name_map("items", scraper, language)
        item_id = entry.get("ability_id")
        name = names.get(item_id) or ("ID %s" % item_id)
        notes.extend("%s: %s" % (name.upper(), line) for line in lines)
    return {"title": title, "notes": notes} if notes else None


#: Подписи секций по умолчанию, если вызывающий не передал свои.
DEFAULT_LABELS = {"general": "GENERAL", "items": "ITEMS",
                  "neutral_items": "NEUTRAL ITEMS"}


def fetch_patch_notes(patch_version: str, language: str = "english",
                      labels: dict | None = None) -> list[dict]:
    """Заметки к патчу в виде [{"title": str, "notes": [str, ...]}, ...].

    language — код языка для datafeed Valve («english», «russian», …). Текст
    заметок и названия способностей приходят переведёнными; имена героев Valve
    оставляет английскими на всех языках, как и в самой игре.

    labels — подписи трёх собственных секций: общей, предметов и нейтральных
    предметов. Заголовки остальных секций приходят из ответа API.
    """
    labels = dict(DEFAULT_LABELS, **(labels or {}))
    scraper = create_scraper()
    try:
        version = _resolve_version(patch_version, scraper, language)
        resp = scraper.get(
            "https://www.dota2.com/datafeed/patchnotes"
            "?version=%s&language=%s" % (version, language), timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
    except Exception:
        return []

    sections = []

    # Общие изменения — сгруппированы по собственным заголовкам.
    for block in data.get("general_notes") or []:
        if not isinstance(block, dict):
            continue
        notes = _notes_from(block.get("generic") or block.get("general"))
        if notes:
            title = block.get("title") or labels["general"]
            sections.append({"title": title.upper(), "notes": notes})

    for entries, title in ((data.get("items"), labels["items"]),
                           (data.get("neutral_items"), labels["neutral_items"])):
        section = _item_section(entries, title, scraper, language)
        if section:
            sections.append(section)

    # Герои — по секции на героя, способности подписаны именами.
    hero_entries = data.get("heroes") or []
    hero_names = _name_map("heroes", scraper, language) if hero_entries else {}
    ability_names = None
    for hero in hero_entries:
        if not isinstance(hero, dict):
            continue
        notes = _notes_from(hero.get("hero_notes"))
        for ability in hero.get("abilities") or []:
            if not isinstance(ability, dict):
                continue
            lines = _notes_from(ability.get("ability_notes"))
            if not lines:
                continue
            if ability_names is None:
                ability_names = _name_map("abilities", scraper, language)
            ab_id = ability.get("ability_id")
            ab_name = ability_names.get(ab_id) or ("ability %s" % ab_id)
            notes.extend("[%s] %s" % (ab_name, line) for line in lines)
        if notes:
            hero_id = hero.get("hero_id")
            title = hero_names.get(hero_id) or ("HERO %s" % hero_id)
            sections.append({"title": title.upper(), "notes": notes})

    return sections
