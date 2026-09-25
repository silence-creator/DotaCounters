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
    "Kez", "Kunkka", "Largo", "Legion Commander", "Leshrac", "Lich",
    "Lifestealer", "Lina", "Lion", "Lone Druid", "Luna",
    "Lycan", "Magnus", "Marci", "Mars", "Medusa",
    "Meepo", "Mirana", "Monkey King", "Morphling", "Muerta",
    "Naga Siren", "Nature's Prophet", "Necrophos", "Night Stalker", "Nyx Assassin",
    "Ogre Magi", "Omniknight", "Oracle", "Outworld Destroyer", "Pangolier",
    "Phantom Assassin", "Phantom Lancer", "Phoenix", "Primal Beast", "Puck",
    "Pudge", "Pugna", "Queen of Pain", "Razor", "Riki",
    "Ringmaster", "Rubick", "Sand King", "Shadow Demon", "Shadow Fiend",
    "Shadow Shaman", "Silencer", "Skywrath Mage", "Slardar", "Slark",
    "Snapfire", "Sniper", "Spectre", "Spirit Breaker", "Storm Spirit",
    "Sven", "Techies", "Templar Assassin", "Terrorblade", "Tidehunter",
    "Timbersaw", "Tinker", "Tiny", "Treant Protector", "Troll Warlord",
    "Tusk", "Underlord", "Undying", "Ursa", "Vengeful Spirit",
    "Venomancer", "Viper", "Visage", "Void Spirit", "Warlock",
    "Weaver", "Windranger", "Winter Wyvern", "Witch Doctor", "Wraith King",
    "Zeus",
])


#: Прозвища, сокращения и старые имена. Транслитерация их не ловит: «бара» —
#: это не написание Spirit Breaker, а сленг. Русские и латинские сокращения
#: записаны отдельно, потому что «вк» переводится в «vk», а не в «wk».
#: Pango и Wind Ranger — так герои назывались в списке до 1.7, и Dotabuff их
#: под этими именами не находил.
NICKNAMES = {
    "Abaddon": ("аба", "абадон", "abba"),
    "Alchemist": ("алх", "алхимик", "alch"),
    "Ancient Apparition": ("aa", "аа", "апарат", "апп"),
    "Anti-Mage": ("am", "ам", "антимаг", "антимаге"),
    "Arc Warden": ("arc", "арк", "зет", "zet"),
    "Beastmaster": ("beast", "бист", "бистмастер"),
    "Bloodseeker": ("bs", "бс", "сикер", "бладсикер"),
    "Bounty Hunter": ("bh", "бх", "баунти"),
    "Brewmaster": ("brew", "брю", "панда"),
    "Bristleback": ("bb", "бб", "брист", "бристл"),
    "Broodmother": ("brood", "бруда", "паук"),
    "Centaur Warrunner": ("cent", "кентавр", "центавр", "цент"),
    "Chaos Knight": ("ck", "чк", "хаос"),
    "Crystal Maiden": ("cm", "цм", "см", "кристалка", "рилай"),
    "Dark Seer": ("ds", "дс", "дарксир"),
    "Dark Willow": ("willow", "виллоу", "вилоу"),
    "Dawnbreaker": ("dawn", "донбрейкер", "даунбрейкер", "дон"),
    "Death Prophet": ("dp", "дп", "крикса"),
    "Dragon Knight": ("dk", "дк", "дракон"),
    "Drow Ranger": ("drow", "дров", "дровка", "трахаус"),
    "Earthshaker": ("es", "ес", "шейкер", "шейк"),
    "Elder Titan": ("et", "ет", "элдер", "титан"),
    "Ember Spirit": ("ember", "эмбер", "ксин"),
    "Enchantress": ("ench", "энча", "энчантресс"),
    "Faceless Void": ("fv", "фв", "войд", "void", "фейслес"),
    "Grimstroke": ("grim", "грим"),
    "Hoodwink": ("hood", "худ", "белка"),
    "Invoker": ("invo", "инвок", "воккер", "карл"),
    "Io": ("wisp", "висп", "ио"),
    "Jakiro": ("жакиро", "джакиро", "твинхед"),
    "Juggernaut": ("jugg", "джагер", "джаг", "джага", "юрнеро"),
    "Keeper of the Light": ("kotl", "котл", "кипер"),
    "Kunkka": ("кунка", "адмирал"),
    "Legion Commander": ("lc", "лц", "легионка", "легион"),
    "Leshrac": ("леший", "лешрак", "лейшрак"),
    "Lifestealer": ("ls", "лс", "naix", "найкс", "наикс"),
    "Lone Druid": ("ld", "лд", "друид", "медведь"),
    "Lycan": ("волк", "ликан"),
    "Monkey King": ("mk", "мк", "манки", "обезьяна"),
    "Morphling": ("morph", "морф"),
    "Naga Siren": ("naga", "нага"),
    "Nature's Prophet": ("np", "нп", "furion", "фурион"),
    "Necrophos": ("necro", "некр", "некрофос"),
    "Night Stalker": ("ns", "нс", "сталкер", "баланар"),
    "Nyx Assassin": ("nyx", "никс"),
    "Ogre Magi": ("ogre", "огр"),
    "Outworld Destroyer": ("od", "од", "обсидиан"),
    "Pangolier": ("pango", "панго", "панголир"),
    "Phantom Assassin": ("pa", "па", "фантомка", "мортред"),
    "Phantom Lancer": ("pl", "пл", "лансер"),
    "Primal Beast": ("primal", "примал"),
    "Pudge": ("пуджик", "мясник", "butcher"),
    "Queen of Pain": ("qop", "квоп", "квопа", "акаша"),
    "Sand King": ("sk", "ск", "санд", "краб"),
    "Shadow Demon": ("sd", "сд", "демон"),
    "Shadow Fiend": ("sf", "сф", "невер", "nevermore"),
    "Shadow Shaman": ("ss", "шаман", "раста", "rhasta"),
    "Silencer": ("сайлер", "сайленсер", "нортром"),
    "Skywrath Mage": ("sky", "скай", "скайрат"),
    "Snapfire": ("snap", "снап", "бабка"),
    "Spirit Breaker": ("sb", "сб", "бара", "барат", "бык"),
    "Storm Spirit": ("storm", "шторм", "штормик"),
    "Techies": ("течис", "техис", "минер"),
    "Templar Assassin": ("ta", "та", "темпларка", "ланая"),
    "Terrorblade": ("tb", "тб", "терор", "террор"),
    "Tidehunter": ("tide", "тайд", "тайдхантер"),
    "Timbersaw": ("timber", "тимбер", "риззрак"),
    "Treant Protector": ("treant", "треант", "дерево"),
    "Troll Warlord": ("troll", "тролль", "тролль варлорд"),
    "Underlord": ("pitlord", "питлорд", "андерлорд"),
    "Vengeful Spirit": ("venga", "венга", "венгеф"),
    "Venomancer": ("veno", "веник", "веном"),
    "Void Spirit": ("vs", "вс", "войдспирит"),
    "Windranger": ("wr", "виндра", "виндранер", "wind ranger"),
    "Winter Wyvern": ("ww", "виверна", "вивера"),
    "Witch Doctor": ("wd", "вд", "витч", "доктор"),
    "Wraith King": ("wk", "вк", "скелет", "леорик"),
    "Zeus": ("зевс", "зеус"),
}


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


#: Ключ прозвища -> герой. Прозвище, совпавшее у двух героев, ловит тест.
ALIASES = {_key(alias): hero for hero, aliases in NICKNAMES.items() for alias in aliases}


def _unique(heroes) -> list:
    seen, out = set(), []
    for hero in heroes:
        if hero not in seen:
            seen.add(hero)
            out.append(hero)
    return out


def resolve(text: str) -> str:
    """Набранное -> имя героя, если оно однозначно: точное имя или прозвище.

    Иначе возвращается как есть — поиск покажет «герой не найден», а не
    молча подставит похожего.
    """
    key = _key(text)
    for hero in ALL_HEROES:
        if _key(hero) == key:
            return hero
    return ALIASES.get(key, (text or "").strip())


def best_match(text: str) -> str:
    """Имя героя для запроса: точное имя или прозвище, иначе первая подсказка.

    Без этого «пудж» и Enter в главном окне уходили на Dotabuff как есть и
    получали «герой не найден», хотя подсказка под полем показывала Pudge.
    Если подсказок нет, набранное возвращается как есть.
    """
    hero = resolve(text)
    if hero in ALL_HEROES:
        return hero
    matches = suggest(text, limit=1)
    return matches[0] if matches else hero


def suggest(query: str, limit: int = SUGGEST_LIMIT, heroes=None) -> list:
    """Герои, подходящие под ввод: сначала начинающиеся с запроса.

    Пустой запрос подсказок не даёт. Регистр, дефисы и апострофы не важны,
    поэтому «antimage» находит «Anti-Mage», а «natures» — «Nature's Prophet».
    Точное прозвище («бара», «sf») идёт первым, начало прозвища — после
    начал настоящих имён.
    """
    key = _key(query)
    if not key:
        return []
    pool = ALL_HEROES if heroes is None else heroes
    names = [(hero, _key(hero)) for hero in pool]
    allowed = set(pool)

    nick_exact = [ALIASES[key]] if ALIASES.get(key) in allowed else []
    starts = [hero for hero, name in names if name.startswith(key)]
    nick_starts = [hero for alias, hero in ALIASES.items()
                   if len(key) >= 2 and alias.startswith(key) and alias != key
                   and hero in allowed]
    # Одна буква внутри имени встречается почти у всех — не подсказка.
    inside = [hero for hero, name in names
              if len(key) >= 2 and key in name and not name.startswith(key)]
    found = _unique(nick_exact + starts + nick_starts + inside)
    if found:
        return found[:limit]

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
