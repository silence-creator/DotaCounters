"""Данные о патчах Dota 2 из официального datafeed Valve.

fetch_current_patch() определяет номер актуального патча, fetch_patch_notes()
разбирает заметки к нему в секции, пригодные для показа в окне.
"""

import re

from bs4 import BeautifulSoup

from .icons import LOCAL_ICON_PREFIX
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
# Из тех же справочников берётся внутренний ключ («bane_nightmare», «item_blink»),
# по которому строится адрес иконки на CDN.

ICON_CDN = "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react"


def hero_icon_url(key: str | None) -> str | None:
    """«npc_dota_hero_axe» -> маленькая иконка героя."""
    if not key:
        return None
    return "%s/heroes/icons/%s.png" % (ICON_CDN, key.replace("npc_dota_hero_", "", 1))


def item_icon_url(key: str | None) -> str | None:
    """«item_blink» -> иконка предмета (нейтральные лежат там же)."""
    if not key:
        return None
    return "%s/items/%s.png" % (ICON_CDN, key.replace("item_", "", 1))


def ability_icon_url(key: str | None) -> str | None:
    """«bane_nightmare» -> иконка способности."""
    if not key:
        return None
    return "%s/abilities/%s.png" % (ICON_CDN, key)


#: Значки характеристик из поля icon в заметках героя. Словарь собран по 25
#: патчам (7.36b–7.41f) и сверен с CDN. Для регенерации здоровья и маны у Valve
#: картинок нет — их рисует icons.py, адрес вида «local:…».
_STAT_ICONS = {
    "strength":         ICON_CDN + "/icons/hero_strength.png",
    "agility":          ICON_CDN + "/icons/hero_agility.png",
    "intelligence":     ICON_CDN + "/icons/hero_intelligence.png",
    "damage":           ICON_CDN + "/heroes/stats/icon_damage.png",
    "armor":            ICON_CDN + "/heroes/stats/icon_armor.png",
    "attack_speed":     ICON_CDN + "/heroes/stats/icon_attack_speed.png",
    "attack_range":     ICON_CDN + "/heroes/stats/icon_attack_range.png",
    "attack_time":      ICON_CDN + "/heroes/stats/icon_attack_time.png",
    "projectile_speed": ICON_CDN + "/heroes/stats/icon_projectile_speed.png",
    "movement":         ICON_CDN + "/heroes/stats/icon_movement_speed.png",
    "magic_resist":     ICON_CDN + "/heroes/stats/icon_magic_resist.png",
    "turn_rate":        ICON_CDN + "/heroes/stats/icon_turn_rate.png",
    "vision":           ICON_CDN + "/heroes/stats/icon_vision.png",
    "health_regen":     LOCAL_ICON_PREFIX + "health_regen",
    "mana_regen":       LOCAL_ICON_PREFIX + "mana_regen",
}


def stat_icon_url(icon: str | None) -> str | None:
    """«agility» -> адрес значка характеристики; незнакомое имя -> None."""
    return _STAT_ICONS.get(icon) if icon else None


_NAME_FEEDS = {
    "heroes":    ("https://www.dota2.com/datafeed/herolist?language=%s", "heroes"),
    "items":     ("https://www.dota2.com/datafeed/itemlist?language=%s", "itemabilities"),
    "abilities": ("https://www.dota2.com/datafeed/abilitylist?language=%s", "itemabilities"),
}

_name_cache = {}


def _name_map(kind: str, scraper, language: str) -> dict:
    """Справочник «идентификатор -> (имя, внутренний ключ)» для языка.

    Качается раз на язык. Имя может быть None, если перевода нет, — ключ при
    этом всё равно нужен, чтобы найти иконку.
    """
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
                name = entry.get("name_loc") or entry.get("name_english_loc") or None
                mapping[entry.get("id")] = (name, entry.get("name"))
    except Exception:
        pass  # без имён покажем идентификаторы, это лучше пустого окна
    _name_cache[cache_key] = mapping
    return mapping


_TAG_RE = re.compile(r"<[^>]+>")


def _clean_note(note: str) -> str:
    """Убрать HTML-теги: Valve кладёт в текст заметок <br> и подобное."""
    return " ".join(_TAG_RE.sub(" ", note).split())


#: Значок улучшения от Аганима — по полю aghanims («scepter» / «shard»).
#: Берутся иконки самих предметов: в heroes/stats/aghs_*.png лежат блёклые
#: контуры «неактивного» состояния, на тёмной теме в 24x16 их не видно.
_AGHANIMS_ICONS = {
    "scepter": ICON_CDN + "/items/ultimate_scepter.png",
    "shard":   ICON_CDN + "/items/aghanims_shard.png",
}

#: Значок таланта. На CDN он есть только в SVG — его растеризует icons.py.
TALENT_ICON = ICON_CDN + "/icons/talents.svg"

#: Пометка перед строкой-пояснением из поля info.
INFO_MARK = "↳ "

#: Пометка перед строкой-меткой из поля title: «New Armor Item», «Item Reworked»,
#: «New Tier 4 Artifact», «New Hero?». Текст метки приходит переведённым.
#: По этому префиксу интерфейс выделяет строку цветом.
BADGE_MARK = "★ "


def _note_rows(entries, ns, icon=None, group=None, prefix="") -> tuple:
    """Строки заметок с иконками и группами: (строки, иконки, группы).

    Из [{note, indent_level, icon, aghanims, info}, ...]:

    * вложенность передаётся отступом;
    * prefix («BLINK DAGGER: », «[Nightmare] ») ставится перед каждой заметкой;
    * icon и group — общие для блока (предмет, способность). Без group каждая
      заметка — отдельная группа, и иконка показывается у каждой строки;
    * заметка с флагом aghanims получает значок Аганима, заметка с полем icon —
      значок характеристики; такая строка всегда в своей группе;
    * пояснение info идёт следующей строкой в той же группе, без иконки.

    ns отличает группы разных блоков одной секции друг от друга.
    """
    lines, icons, groups = [], [], []
    for idx, entry in enumerate(entries or []):
        if not isinstance(entry, dict):
            continue
        note = _clean_note(entry.get("note") or entry.get("text") or "")
        if not note:
            continue  # заметка была одним лишь тегом
        try:
            depth = max(0, int(entry.get("indent_level", 1)) - 1)
        except (TypeError, ValueError):
            depth = 0
        pad = "    " * depth

        own_icon = _AGHANIMS_ICONS.get(entry.get("aghanims")) or stat_icon_url(entry.get("icon"))
        if own_icon:
            line_icon, line_group = own_icon, ("own", ns, idx)
        else:
            line_icon = icon
            line_group = group if group is not None else ("own", ns, idx)

        lines.append(pad + prefix + note)
        icons.append(line_icon)
        groups.append(line_group)

        info = _clean_note(entry.get("info") or "")
        if info:
            lines.append(pad + "    " + INFO_MARK + info)
            icons.append(None)
            groups.append(line_group)
    return lines, icons, groups


def _section(title, rows, icon=None) -> dict | None:
    lines, icons, groups = rows
    if not lines:
        return None
    return {"title": title, "icon": icon, "notes": lines, "icons": icons,
            "groups": groups}


def _merge(*parts) -> tuple:
    """Склеить несколько (строки, иконки, группы) в одни."""
    lines, icons, groups = [], [], []
    for part_lines, part_icons, part_groups in parts:
        lines.extend(part_lines)
        icons.extend(part_icons)
        groups.extend(part_groups)
    return lines, icons, groups


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


def _tier_row(title, ns) -> tuple:
    """Строка-заголовок уровня внутри секции: «— Artifacts —»."""
    return ["— %s —" % _clean_note(title)], [None], [("tier", ns)]


def _badge_row(title, icon, group) -> tuple:
    """Строка-метка «★ New Armor Item» в начале группы; пусто, если метки нет."""
    text = _clean_note(title or "")
    if not text:
        return [], [], []
    return [BADGE_MARK + text], [icon], [group]


def _item_rows(entries, lookup, ns) -> tuple:
    """Предметы: строки каждого предмета — одна группа с его иконкой."""
    parts = []
    for n, entry in enumerate(entries or []):
        if not isinstance(entry, dict):
            continue
        if entry.get("is_general_note"):
            if entry.get("title"):
                parts.append(_tier_row(entry["title"], (ns, n)))
            continue
        if not entry.get("ability_notes"):
            continue
        item_id = entry.get("ability_id")
        name, key = lookup("items").get(item_id, (None, None))
        name = name or ("ID %s" % item_id)
        icon, group = item_icon_url(key), ("item", ns, n)
        # Метка «New Item» идёт первой строкой той же группы, поэтому иконка
        # предмета встаёт рядом с ней, а не с первой заметкой.
        parts.append(_badge_row(entry.get("title"), icon, group))
        parts.append(_note_rows(entry.get("ability_notes"), (ns, n),
                                icon=icon, group=group,
                                prefix="%s: " % name.upper()))
    return _merge(*parts)


def _creep_rows(entries) -> tuple:
    """Нейтральные крипы: имя уже переведено в самом ответе."""
    parts = []
    for n, entry in enumerate(entries or []):
        if not isinstance(entry, dict):
            continue
        name = _clean_note(entry.get("localized_name") or entry.get("title") or "")
        if entry.get("is_general_note"):
            if name:
                parts.append(_tier_row(name, ("creep", n)))
            continue
        name = name or (entry.get("name") or "").replace("npc_dota_neutral_", "")
        parts.append(_note_rows(entry.get("neutral_creep_notes"), ("creep", n),
                                group=("creep", n), prefix="%s: " % name.upper()))
    return _merge(*parts)


def _hero_rows(hero, lookup) -> tuple:
    """Герой: общие изменения, способности, затем таланты.

    Раздел subsections — это аспекты героев. С патча 7.41 их нет ни в игре, ни
    в ответе API, поэтому в старых патчах он сознательно пропускается.
    """
    parts = [_badge_row(hero.get("title"), None, ("badge", "hero")),
             _note_rows(hero.get("hero_notes"), "hero")]
    for ability in hero.get("abilities") or []:
        if not isinstance(ability, dict) or not ability.get("ability_notes"):
            continue
        ab_id = ability.get("ability_id")
        ab_name, ab_key = lookup("abilities").get(ab_id, (None, None))
        ab_name = ab_name or ("ability %s" % ab_id)
        parts.append(_note_rows(ability.get("ability_notes"), ("ability", ab_id),
                                icon=ability_icon_url(ab_key),
                                group=("ability", ab_id),
                                prefix="[%s] " % ab_name))
    # Каждый талант — отдельная строка со своим значком.
    parts.append(_note_rows(hero.get("talent_notes"), "talent", icon=TALENT_ICON))
    return _merge(*parts)


#: Подписи секций по умолчанию, если вызывающий не передал свои.
DEFAULT_LABELS = {"general": "GENERAL", "items": "ITEMS",
                  "neutral_items": "NEUTRAL ITEMS", "neutral_creeps": "NEUTRAL CREEPS"}


def build_sections(data: dict, lookup, labels: dict | None = None) -> list[dict]:
    """Разложить ответ /datafeed/patchnotes на секции. Сети не касается.

    lookup(kind) возвращает справочник {id: (имя, внутренний ключ)} для kind
    из «heroes», «items», «abilities» и вызывается, только когда он нужен.
    Формат секций описан в fetch_patch_notes.
    """
    labels = dict(DEFAULT_LABELS, **(labels or {}))
    cache = {}

    def names(kind):
        if kind not in cache:
            cache[kind] = lookup(kind) or {}
        return cache[kind]

    sections = []

    # Общие изменения — сгруппированы по собственным заголовкам.
    for n, block in enumerate(data.get("general_notes") or []):
        if not isinstance(block, dict):
            continue
        title = _clean_note(block.get("title") or "") or labels["general"]
        sections.append(_section(title.upper(), _note_rows(
            block.get("generic") or block.get("general"), ("general", n))))

    sections.append(_section(labels["items"], _item_rows(data.get("items"), names, "items")))
    sections.append(_section(labels["neutral_items"],
                             _item_rows(data.get("neutral_items"), names, "neutral")))
    sections.append(_section(labels["neutral_creeps"], _creep_rows(data.get("neutral_creeps"))))

    for hero in data.get("heroes") or []:
        if not isinstance(hero, dict):
            continue
        rows = _hero_rows(hero, names)
        if not rows[0]:
            continue
        hero_id = hero.get("hero_id")
        name, key = names("heroes").get(hero_id, (None, None))
        title = name or ("HERO %s" % hero_id)
        sections.append(_section(title.upper(), rows, icon=hero_icon_url(key)))

    return [s for s in sections if s]


def fetch_patch_notes(patch_version: str, language: str = "english",
                      labels: dict | None = None) -> list[dict]:
    """Заметки к патчу в виде списка секций:

        {"title":  str,          заголовок секции
         "icon":   str | None,   адрес иконки к заголовку (у героев)
         "notes":  [str, ...],   строки заметок
         "icons":  [str | None], адрес иконки к каждой строке, той же длины
         "groups": [hashable]}   группа строки, той же длины

    Строки одной группы — это несколько изменений одного предмета или одной
    способности, плюс их пояснения: иконку достаточно показать у первой.
    Значок характеристики или Аганима у каждой строки свой, поэтому каждая
    такая строка — отдельная группа.

    Сами картинки здесь не скачиваются — только адреса; загрузкой занимается
    интерфейс, чтобы текст можно было показать, не дожидаясь иконок.

    language — код языка для datafeed Valve («english», «russian», …). Текст
    заметок, названия способностей и крипов приходят переведёнными; имена
    героев и предметов Valve оставляет английскими, как и в самой игре.

    labels — подписи собственных секций: общей, предметов, нейтральных
    предметов и нейтральных крипов. Заголовки остальных приходят из API.
    """
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
    return build_sections(data, lambda kind: _name_map(kind, scraper, language), labels)
