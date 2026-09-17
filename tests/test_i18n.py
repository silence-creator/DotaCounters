"""Строки интерфейса и история изменений. Сеть не нужна.

Запуск:  python -m unittest discover -s tests -v
"""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotacounters.i18n import I18N  # noqa: E402
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

    def test_version_labels_follow_app_version(self):
        for table in I18N.values():
            self.assertEqual(table["set_ver_val"], APP_VERSION)
            self.assertTrue(table["welcome_title"].endswith("v" + APP_VERSION))
            self.assertTrue(table["app_subtitle"].endswith("v " + " ".join(APP_VERSION)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
