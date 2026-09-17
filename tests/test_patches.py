"""Разбор заметок к патчу на сохранённом ответе API. Сеть не нужна.

Фикстура — настоящий ответ /datafeed/patchnotes для 7.41, урезанный до
нескольких записей каждого вида: таланты с пояснениями, улучшения от Аганима,
значки характеристик, заголовки уровней, нейтральные крипы.

Запуск:  python -m unittest discover -s tests -v
"""

import copy
import io
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotacounters.patches import (  # noqa: E402
    BADGE_MARK, ICON_CDN, INFO_MARK, TALENT_ICON, _note_rows, ability_icon_url,
    build_sections, item_icon_url, stat_icon_url,
)
from dotacounters.ui.patch_notes import PatchNotesModal  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "fixtures", "patchnotes_7.41_trimmed.json")


def load_fixture() -> dict:
    with io.open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)


def stub_lookup(data):
    """Справочники без сети: имена и ключи выводятся из идентификаторов."""
    maps = {"heroes": {}, "abilities": {}, "items": {}}
    for hero in data.get("heroes") or []:
        hid = hero["hero_id"]
        maps["heroes"][hid] = ("Hero %d" % hid, "npc_dota_hero_h%d" % hid)
        for ab in hero.get("abilities") or []:
            aid = ab["ability_id"]
            maps["abilities"][aid] = ("Ability %d" % aid, "ab_%d" % aid)
    for entry in (data.get("items") or []) + (data.get("neutral_items") or []):
        iid = entry.get("ability_id")
        maps["items"][iid] = ("Item %s" % iid, "item_i%s" % iid)
    calls = []

    def lookup(kind):
        calls.append(kind)
        return maps[kind]
    lookup.calls = calls
    return lookup


def section(sections, title):
    return next(s for s in sections if s["title"] == title)


def line_index(sec, text):
    return next(i for i, line in enumerate(sec["notes"]) if text in line)


class BuildSectionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_fixture()
        cls.sections = build_sections(cls.data, stub_lookup(cls.data))

    def test_parallel_lists_have_equal_length(self):
        for sec in self.sections:
            n = len(sec["notes"])
            self.assertEqual(len(sec["icons"]), n, sec["title"])
            self.assertEqual(len(sec["groups"]), n, sec["title"])

    def test_talents_are_shown(self):
        """Раньше таланты не показывались вовсе — ни в одном патче."""
        lina = section(self.sections, "HERO 25")
        self.assertTrue(any("Level 15 Talent Light Strike Array Damage" in line
                            for line in lina["notes"]))

    def test_talents_come_after_abilities(self):
        am = section(self.sections, "HERO 1")
        last_ability = max(i for i, line in enumerate(am["notes"]) if line.startswith("["))
        first_talent = line_index(am, "Level 15 Talent")
        self.assertGreater(first_talent, last_ability)

    def test_info_follows_its_note_in_the_same_group(self):
        lina = section(self.sections, "HERO 25")
        talent = line_index(lina, "Combustion Overheat")
        info = talent + 1
        self.assertIn(INFO_MARK + "This increases additional damage", lina["notes"][info])
        self.assertEqual(lina["groups"][info], lina["groups"][talent])
        self.assertIsNone(lina["icons"][info], "у пояснения своей иконки нет")

    def test_aghanims_lines_get_their_icon(self):
        am = section(self.sections, "HERO 1")
        i = line_index(am, "Now upgraded with Aghanim's Scepter")
        self.assertEqual(am["icons"][i], ICON_CDN + "/items/ultimate_scepter.png")
        lina = section(self.sections, "HERO 25")
        i = line_index(lina, "Aghanim's Shard upgrade reworked")
        self.assertEqual(lina["icons"][i], ICON_CDN + "/items/aghanims_shard.png")

    def test_consecutive_same_stat_lines_are_separate_groups(self):
        """Два изменения урона подряд — оба со значком, а не только первое."""
        zeus = section(self.sections, "HERO 22")
        damage = [i for i, url in enumerate(zeus["icons"]) if url == stat_icon_url("damage")]
        self.assertGreaterEqual(len(damage), 2)
        self.assertNotEqual(zeus["groups"][damage[0]], zeus["groups"][damage[1]])

    def test_ability_lines_share_one_group_and_icon(self):
        lina = section(self.sections, "HERO 25")
        ab_id = self.data["heroes"][0]["abilities"][0]["ability_id"]
        url = ability_icon_url("ab_%d" % ab_id)
        own = [i for i, line in enumerate(lina["notes"])
               if line.startswith("[Ability %d] " % ab_id) and lina["icons"][i] == url]
        self.assertTrue(own, "у строк способности — иконка способности")
        self.assertEqual(len({lina["groups"][i] for i in own}), 1)

    def test_neutral_creeps_section(self):
        creeps = section(self.sections, "NEUTRAL CREEPS")
        self.assertTrue(creeps["notes"][0].startswith("KOBOLD FOREMAN: "))
        self.assertEqual(len(creeps["notes"]), 3)

    def test_tier_headers(self):
        neutral = section(self.sections, "NEUTRAL ITEMS")
        self.assertEqual(neutral["notes"][0], "— General changes —")

    def test_hero_heading_icon(self):
        self.assertEqual(section(self.sections, "HERO 1")["icon"],
                         ICON_CDN + "/heroes/icons/h1.png")


class BadgesTest(unittest.TestCase):
    """Метки из поля title: «New Item», «Item Reworked», «New Tier 1 Artifact»."""

    @classmethod
    def setUpClass(cls):
        cls.data = load_fixture()
        cls.sections = build_sections(cls.data, stub_lookup(cls.data))

    def test_new_item_badge_heads_its_item(self):
        items = section(self.sections, "ITEMS")
        i = items["notes"].index(BADGE_MARK + "New Miscellaneous Item")
        self.assertEqual(items["icons"][i], item_icon_url("item_i1872"),
                         "иконка предмета — у метки, первой строки группы")
        # у нового предмета заметки идут со вторым уровнем вложенности — с отступом
        self.assertTrue(items["notes"][i + 1].lstrip().startswith("ITEM 1872: "))
        self.assertEqual(items["groups"][i], items["groups"][i + 1])

    def test_reworked_and_artifact_badges(self):
        self.assertIn(BADGE_MARK + "Item Reworked", section(self.sections, "ITEMS")["notes"])
        self.assertIn(BADGE_MARK + "New Tier 1 Artifact",
                      section(self.sections, "NEUTRAL ITEMS")["notes"])

    def test_html_is_stripped_from_badge(self):
        for sec in self.sections:
            for line in sec["notes"]:
                self.assertNotIn("<span", line)

    def test_items_without_title_have_no_badge(self):
        items = section(self.sections, "ITEMS")
        badges = [line for line in items["notes"] if line.startswith(BADGE_MARK)]
        self.assertEqual(len(badges), 2)

    def test_hero_badge(self):
        data = copy.deepcopy(load_fixture())
        data["heroes"][0]["title"] = '<span class="New">New Hero?</span>'
        lina = section(build_sections(data, stub_lookup(data)), "HERO 25")
        self.assertEqual(lina["notes"][0], BADGE_MARK + "New Hero?")
        self.assertIsNone(lina["icons"][0])
        self.assertNotEqual(lina["groups"][0], lina["groups"][1])

    def test_filter_keeps_badge_with_its_item(self):
        """Поиск по тексту заметки не должен терять метку нового предмета."""
        fake = type("Modal", (), {"_all_sections": self.sections})()
        filtered = PatchNotesModal._filtered(fake, "ITEM 1872")
        items = section(filtered, "ITEMS")
        self.assertEqual(items["notes"][0], BADGE_MARK + "New Miscellaneous Item")
        self.assertTrue(all(len(items[k]) == len(items["notes"]) for k in ("icons", "groups")))


class TalentIconTest(unittest.TestCase):
    def test_every_talent_line_has_its_own_icon(self):
        data = load_fixture()
        lina = section(build_sections(data, stub_lookup(data)), "HERO 25")
        talents = [i for i, line in enumerate(lina["notes"])
                   if line.startswith("Level ") and "Talent" in line]
        self.assertEqual(len(talents), 3)
        self.assertTrue(all(lina["icons"][i] == TALENT_ICON for i in talents))
        self.assertEqual(len({lina["groups"][i] for i in talents}), 3,
                         "каждый талант — своя группа, значок у каждого")

    def test_talent_info_line_has_no_icon(self):
        data = load_fixture()
        lina = section(build_sections(data, stub_lookup(data)), "HERO 25")
        info = next(i for i, line in enumerate(lina["notes"]) if INFO_MARK in line
                    and "additional damage" in line)
        self.assertIsNone(lina["icons"][info])
        self.assertEqual(lina["icons"][info - 1], TALENT_ICON)


class FacetsSkippedTest(unittest.TestCase):
    """Аспекты убраны из игры в 7.41: раздел subsections старых патчей пропускается."""

    def test_subsections_are_ignored(self):
        data = copy.deepcopy(load_fixture())
        data["heroes"][0]["subsections"] = [{
            "title": "Some Facet", "style": "hero_facet", "facet": "x",
            "general_notes": [{"indent_level": 1, "note": "FACET NOTE MUST NOT APPEAR"}],
            "talent_notes": [{"indent_level": 1, "note": "FACET TALENT MUST NOT APPEAR"}],
        }]
        sections = build_sections(data, stub_lookup(data))
        text = "\n".join(line for sec in sections for line in sec["notes"])
        self.assertNotIn("FACET NOTE", text)
        self.assertNotIn("FACET TALENT", text)


class LabelsAndLookupTest(unittest.TestCase):
    def test_custom_labels(self):
        data = load_fixture()
        sections = build_sections(data, stub_lookup(data), labels={
            "items": "ПРЕДМЕТЫ", "neutral_items": "НЕЙТРАЛЬНЫЕ ПРЕДМЕТЫ",
            "neutral_creeps": "НЕЙТРАЛЬНЫЕ КРИПЫ"})
        titles = [s["title"] for s in sections]
        for label in ("ПРЕДМЕТЫ", "НЕЙТРАЛЬНЫЕ ПРЕДМЕТЫ", "НЕЙТРАЛЬНЫЕ КРИПЫ"):
            self.assertIn(label, titles)

    def test_lookup_is_lazy(self):
        """Справочники тяжёлые (abilitylist ~750 КБ) — без нужды не запрашиваются."""
        data = {"general_notes": load_fixture()["general_notes"]}
        lookup = stub_lookup(load_fixture())
        build_sections(data, lookup)
        self.assertEqual(lookup.calls, [])

    def test_empty_response(self):
        self.assertEqual(build_sections({}, stub_lookup({})), [])


class NoteRowsTest(unittest.TestCase):
    def test_tag_only_note_dropped_with_its_icon(self):
        lines, icons, groups = _note_rows([
            {"note": "Base Agility decreased from 20 to 18", "icon": "agility"},
            {"note": "<br>", "icon": "damage"},
            {"note": "Damage at level 1 increased by 1", "icon": "damage", "indent_level": 2},
            {"note": "Some change without an icon"},
        ], "t")
        self.assertEqual(len(lines), 3)
        self.assertEqual(icons, [stat_icon_url("agility"), stat_icon_url("damage"), None])
        self.assertTrue(lines[1].startswith("    Damage"), "вложенность — отступом")
        self.assertEqual(len(set(groups)), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
