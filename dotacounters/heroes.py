"""Список героев для встроенного браузера и подсказок ввода."""

import re

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


def _key(name: str) -> str:
    """«Anti-Mage» -> «antimage»: дефисы и апострофы при вводе пропускают."""
    return _NOT_LETTERS.sub("", name.lower())


def suggest(query: str, limit: int = SUGGEST_LIMIT, heroes=None) -> list:
    """Герои, подходящие под ввод: сначала начинающиеся с запроса.

    Пустой запрос подсказок не даёт. Регистр, дефисы и апострофы не важны,
    поэтому «antimage» находит «Anti-Mage», а «natures» — «Nature's Prophet».
    """
    key = _key(query)
    if not key:
        return []
    starts, inside = [], []
    for hero in (ALL_HEROES if heroes is None else heroes):
        name = _key(hero)
        if name.startswith(key):
            starts.append(hero)
        elif key in name:
            inside.append(hero)
    return (starts + inside)[:limit]
