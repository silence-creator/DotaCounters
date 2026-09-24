"""Список героев для встроенного браузера и подсказок ввода."""

import re
from difflib import SequenceMatcher

ALL_HEROES = sorted([
    "Abaddon", "Alchemist", "Ancient Apparition", "Anti-Mage", "Arc Warden",
    "Axe", "Bane", "Batrider", "Beastmaster", "Bloodseeker",
    "Bounty Hunter", "Brewmaster", "Bristleback", "Broodmother", "Centaur Warrunner",
    "Chaos Knight", "Chen", "Clinkz", "Clockwerk", "Crystal Maiden",
    "Dark Seer", "Dark Willow", "Dawnbreaker", "Dazzle", "Death Prophet",
    "Disruptor", "Doom", "Dragon Knight", "Drow Ranger", "Earth Spirit",
    "Earthshaker", "Elder Titan", "Ember Spirit", "Enchantress", "Enigma",
    "Faceless Void", "Grimstroke", "Gyrocopter", "Hoodwink", "Huskar",
    "Invoker", "Io", "Jakiro", "Juggernaut", "Keeper of the Light",
    "Kez", "Kunkka", "Legion Commander", "Leshrac", "Lich",
    "Lifestealer", "Lina", "Lion", "Lone Druid", "Luna",
    "Lycan", "Magnus", "Marci", "Mars", "Medusa",
    "Meepo", "Mirana", "Monkey King", "Morphling", "Muerta",
    "Naga Siren", "Nature's Prophet", "Necrophos", "Night Stalker", "Nyx Assassin",
    "Ogre Magi", "Omniknight", "Oracle", "Outworld Destroyer", "Pango",
    "Phantom Assassin", "Phantom Lancer", "Phoenix", "Primal Beast", "Puck",
    "Pudge", "Pugna", "Queen of Pain", "Razor", "Riki",
    "Ringmaster", "Rubick", "Sand King", "Shadow Demon", "Shadow Fiend",
    "Shadow Shaman", "Silencer", "Skywrath Mage", "Slardar", "Slark",
    "Snapfire", "Sniper", "Spectre", "Spirit Breaker", "Storm Spirit",
    "Sven", "Techies", "Templar Assassin", "Terrorblade", "Tidehunter",
    "Timbersaw", "Tinker", "Tiny", "Treant Protector", "Troll Warlord",
    "Tusk", "Underlord", "Undying", "Ursa", "Vengeful Spirit",
    "Venomancer", "Viper", "Visage", "Void Spirit", "Warlock",
    "Weaver", "Wind Ranger", "Winter Wyvern", "Witch Doctor", "Wraith King",
    "Zeus",
])


#: Сколько подсказок показывать под полем ввода.
SUGGEST_LIMIT = 8

_NOT_LETTERS = re.compile(r"[^a-z0-9]")

#: Побуквенная транслитерация: имена героев Valve не переводит, а набирают их
#: часто по-русски. Точного совпадения это не даёт («пудж» -> «pudzh» против
#: «pudge»), поэтому дальше работает нестрогое сравнение.
_RU_TO_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}

#: Насколько похожими должны быть строки, чтобы считать это попаданием.
#: Подобрано на списке реальных русских написаний имён героев.
FUZZY_RATIO = 0.62


def _translit(text: str) -> str:
    return "".join(_RU_TO_LAT.get(ch, ch) for ch in text.lower())


#: Сглаживание написания: применяется к обеим сторонам сравнения, поэтому
#: правила нужны не «правильные», а одинаково действующие. «кс» и «x» звучат
#: одинаково (акс -> aks -> ax = Axe), «ee» по-русски пишут через «и»
#: (мипо -> mipo, Meepo -> mipo).
_FOLD = (("ks", "x"), ("ph", "f"), ("ck", "k"), ("ee", "i"), ("oo", "u"),
         ("dzh", "dj"), ("zh", "j"))


def _fold(key: str) -> str:
    for old, new in _FOLD:
        key = key.replace(old, new)
    out = []
    for ch in key:                      # двойные буквы схлопываем
        if not out or out[-1] != ch:
            out.append(ch)
    return "".join(out)


def _key(name: str) -> str:
    """«Anti-Mage» -> «antimage», «Пудж» -> «pudzh».

    Дефисы и апострофы при вводе пропускают, русские буквы переводятся
    в латиницу побуквенно.
    """
    return _NOT_LETTERS.sub("", _translit(name))


def _fuzzy_key(name: str) -> str:
    """Тот же ключ, но со сглаженным написанием — только для сравнения внахлёст.

    В точном поиске сглаживание мешало бы: «ck» перестало бы находить
    Clockwerk, потому что превращается в «k».
    """
    return _fold(_key(name))


def suggest(query: str, limit: int = SUGGEST_LIMIT, heroes=None) -> list:
    """Герои, подходящие под ввод: сначала начинающиеся с запроса.

    Пустой запрос подсказок не даёт. Регистр, дефисы и апострофы не важны,
    поэтому «antimage» находит «Anti-Mage», а «natures» — «Nature's Prophet».
    """
    key = _key(query)
    if not key:
        return []
    names = [(hero, _key(hero)) for hero in (ALL_HEROES if heroes is None else heroes)]

    starts = [hero for hero, name in names if name.startswith(key)]
    # Одна буква внутри имени встречается почти у всех — не подсказка.
    inside = [hero for hero, name in names
              if len(key) >= 2 and key in name and not name.startswith(key)]
    if starts or inside:
        return (starts + inside)[:limit]

    # Ничего не совпало буквально — пробуем нестрого: так находятся русские
    # написания («пудж» -> pudj против pudge) и опечатки. Только запасной
    # вариант: иначе к точным совпадениям примешивался бы шум.
    close = []
    fuzzy = _fuzzy_key(query)
    for hero, _ in names:
        name = _fuzzy_key(hero)
        # Сравниваем и с началом имени той же длины (иначе длинные имена
        # проигрывают коротким), и с именем целиком, берём лучшее.
        head = SequenceMatcher(None, fuzzy, name[:max(len(fuzzy), 3)]).ratio()
        whole = SequenceMatcher(None, fuzzy, name).ratio()
        ratio = max(head, whole)
        if ratio >= FUZZY_RATIO:
            close.append((ratio, hero))
    close.sort(key=lambda pair: (-pair[0], pair[1]))
    return [hero for _, hero in close][:limit]
