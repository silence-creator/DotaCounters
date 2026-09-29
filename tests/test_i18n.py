"""Строки интерфейса и история изменений. Сеть не нужна.

Запуск:  python -m unittest discover -s tests -v
"""

import glob
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotacounters.draft import FILTERS, GROUPS, SIDES  # noqa: E402
from dotacounters.i18n import I18N  # noqa: E402
from dotacounters.meta import RANKS  # noqa: E402
from dotacounters.ui.app import TABS  # noqa: E402
from dotacounters.version import APP_VERSION  # noqa: E402


class I18nTest(unittest.TestCase):
    def test_languages_have_the_same_keys(self):
        self.assertEqual(set(I18N["en"]) ^ set(I18N["ru"]), set())

    def test_changelog_starts_with_current_version(self):
        """Подняли APP_VERSION — не забудьте запись в истории изменений."""
        for lang, table in I18N.items():
            first = table["upd_text"].split("\n", 1)[0]
            self.assertEqual(first, "v" + APP_VERSION, "язык %s" % lang)

    def test_changelog_versions_match_between_languages(self):
        headers = {lang: re.findall(r"^v\d[\d.]*$", table["upd_text"], re.M)
                   for lang, table in I18N.items()}
        self.assertEqual(headers["en"], headers["ru"])

    def test_changelog_versions_go_newest_first(self):
        headers = re.findall(r"^v(\d[\d.]*)$", I18N["en"]["upd_text"], re.M)
        as_tuples = [tuple(int(p) for p in h.split(".")) for h in headers]
        self.assertEqual(as_tuples, sorted(as_tuples, reverse=True))
        self.assertEqual(len(set(as_tuples)), len(as_tuples), "версии не повторяются")

    def test_version_label_takes_app_version(self):
        for table in I18N.values():
            self.assertIn(APP_VERSION, table["set_version"].format(version=APP_VERSION))


# Ключи, которые код собирает из частей: tr["role_" + позиция]. Новый составной
# ключ нужно вписать сюда — иначе тест не поймёт, какие строки он использует.
_KINDS = ("ban", "pick")
PREFIX_KEYS = {
    "tab_": TABS, "role_": FILTERS, "side_": SIDES,
    "cm_": _KINDS, "cm_your_": _KINDS, "cm_their_": _KINDS, "cm_phase_": _KINDS,
    "cm_entry_": _KINDS,
    "draft_to_": GROUPS, "draft_row_": GROUPS, "draft_next_": ("enemies", "allies"),
    "ov_group_": GROUPS, "rank_": RANKS, "rank_short_": RANKS,
}
_SOURCES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "dotacounters")


def used_keys():
    """Ключи строк, к которым обращается код: tr["ключ"] и tr["префикс_" + …]."""
    keys, unknown = set(), set()
    for path in glob.glob(os.path.join(_SOURCES, "**", "*.py"), recursive=True):
        if os.path.basename(path) == "i18n.py":
            continue
        with open(path, encoding="utf-8") as f:
            src = f.read()
        keys |= set(re.findall(r"""tr\[\s*["']([a-z0-9_]+)["']\s*\]""", src))
        for prefix in re.findall(r"""tr\[\s*["']([a-z0-9_]+)["']\s*\+""", src):
            if prefix in PREFIX_KEYS:
                keys |= {prefix + suffix for suffix in PREFIX_KEYS[prefix]}
            else:
                unknown.add(prefix)
    return keys, unknown


class KeysMatchCodeTest(unittest.TestCase):
    """Файл строк и код не расходятся: нет ни KeyError, ни мёртвых строк."""

    @classmethod
    def setUpClass(cls):
        cls.used, cls.unknown = used_keys()

    def test_no_keys_in_conditional_expressions(self):
        """tr["a" if x else "b"] сканер не видит: писать tr["a"] if x else tr["b"]."""
        bad = []
        for path in glob.glob(os.path.join(_SOURCES, "**", "*.py"), recursive=True):
            with open(path, encoding="utf-8") as f:
                for n, line in enumerate(f, 1):
                    if re.search(r"""tr\[\s*["'][a-z0-9_]+["']\s+if\b""", line):
                        bad.append("%s:%d" % (os.path.basename(path), n))
        self.assertEqual(bad, [])

    def test_compound_keys_are_known(self):
        self.assertEqual(self.unknown, set(), "впишите префикс в PREFIX_KEYS")

    def test_every_used_key_exists(self):
        for lang, table in I18N.items():
            self.assertEqual(sorted(self.used - set(table)), [], "язык %s" % lang)

    def test_no_unused_strings(self):
        self.assertEqual(sorted(set(I18N["en"]) - self.used), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
