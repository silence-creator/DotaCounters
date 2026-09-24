"""Проверка и установка обновлений. Сеть подменяется заглушкой.

Запуск:  python -m unittest discover -s tests -v
"""

import hashlib
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotacounters import updates  # noqa: E402
from dotacounters.updates import (  # noqa: E402
    OLD_SUFFIX, Update, check, cleanup_old, download, install, is_newer,
    parse_version, relaunch_env,
)
from dotacounters.version import APP_VERSION  # noqa: E402

#: Заведомо более новая версия, чем текущая, — чтобы тест не ломался при выпуске.
NEWER = "%d.0" % (parse_version(APP_VERSION)[0] + 1)


class FakeResponse:
    def __init__(self, payload=None, status=200, body=b""):
        self.status_code = status
        self._payload = payload
        self._body = body

    def json(self):
        return self._payload

    def iter_content(self, chunk_size=1):
        for i in range(0, len(self._body), chunk_size):
            yield self._body[i:i + chunk_size]


class FakeScraper:
    """Отдаёт заранее заданный ответ и запоминает запрошенные адреса."""

    def __init__(self, response):
        self.response = response
        self.urls = []

    def get(self, url, **kwargs):
        self.urls.append(url)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def release(tag="v" + NEWER, assets=None, body="что нового"):
    return {"tag_name": tag, "body": body, "html_url": "https://example/releases/tag/" + tag,
            "assets": assets if assets is not None else [
                {"name": "DotaCounters%s.exe" % NEWER, "size": 123,
                 "browser_download_url": "https://example/DotaCounters.exe",
                 "digest": "sha256:" + "ab" * 32}]}


class VersionTest(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_version("v1.2"), (1, 2))
        self.assertEqual(parse_version("1.1.1"), (1, 1, 1))
        self.assertEqual(parse_version("DotaCounters1.2"), (1, 2))
        self.assertEqual(parse_version("нет цифр"), ())

    def test_newer(self):
        self.assertTrue(is_newer("v1.3", "1.2"))
        self.assertTrue(is_newer("v1.2.1", "1.2"), "1.2.1 новее 1.2")
        self.assertTrue(is_newer("v2.0", "1.9.9"))
        self.assertTrue(is_newer("v1.10", "1.9"), "числа сравниваются как числа")

    def test_not_newer(self):
        self.assertFalse(is_newer("v1.2", "1.2"))
        self.assertFalse(is_newer("v1.2", "1.2.1"))
        self.assertFalse(is_newer("v1.1", "1.2"))
        self.assertFalse(is_newer("мусор", "1.2"), "непонятный тег обновлением не считается")


class CheckTest(unittest.TestCase):
    def test_finds_newer_release(self):
        scraper = FakeScraper(FakeResponse(release()))
        found = check(scraper)
        self.assertIsInstance(found, Update)
        self.assertEqual(found.version, NEWER)
        self.assertEqual(found.sha256, "ab" * 32)
        self.assertEqual(found.url, "https://example/DotaCounters.exe")

    def test_same_version_is_not_an_update(self):
        self.assertIsNone(check(FakeScraper(FakeResponse(release(tag="v" + APP_VERSION)))))

    def test_release_without_exe_is_ignored(self):
        assets = [{"name": "notes.txt", "browser_download_url": "https://example/notes.txt"}]
        self.assertIsNone(check(FakeScraper(FakeResponse(release(assets=assets)))))

    def test_network_trouble_is_quiet(self):
        self.assertIsNone(check(FakeScraper(FakeResponse(status=503))))
        self.assertIsNone(check(FakeScraper(OSError("сеть недоступна"))))


class DownloadTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.body = b"x" * 5000
        self.dest = os.path.join(self.dir, "new.exe")

    def _read(self, path):
        with open(path, "rb") as f:
            return f.read()

    def _update(self, sha):
        return Update(version=NEWER, url="https://example/x.exe", size=len(self.body),
                      sha256=sha, notes="")

    def test_saves_and_checks_sum(self):
        sha = hashlib.sha256(self.body).hexdigest()
        seen = []
        download(self._update(sha), self.dest, FakeScraper(FakeResponse(body=self.body)),
                 progress=lambda got, total: seen.append(got))
        self.assertEqual(self._read(self.dest), self.body)
        self.assertEqual(seen[-1], len(self.body), "прогресс доходит до конца")

    def test_wrong_sum_raises_and_removes_file(self):
        with self.assertRaises(ValueError):
            download(self._update("00" * 32), self.dest,
                     FakeScraper(FakeResponse(body=self.body)))
        self.assertFalse(os.path.exists(self.dest), "битый файл не остаётся на диске")

    def test_http_error(self):
        with self.assertRaises(IOError):
            download(self._update(None), self.dest,
                     FakeScraper(FakeResponse(status=404, body=b"")))


class InstallTest(unittest.TestCase):
    def _read(self, path):
        with open(path, "rb") as f:
            return f.read()

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.exe = os.path.join(self.dir, "DotaCounters.exe")
        with open(self.exe, "wb") as f:
            f.write(b"old build")
        self.new = os.path.join(self.dir, "DotaCounters.exe.new")
        with open(self.new, "wb") as f:
            f.write(b"new build")

    def test_replaces_and_keeps_backup(self):
        install(self.new, self.exe)
        self.assertEqual(self._read(self.exe), b"new build")
        self.assertEqual(self._read(self.exe + OLD_SUFFIX), b"old build")
        self.assertFalse(os.path.exists(self.new), "временный файл переехал на место")

    def test_cleanup_removes_backup(self):
        install(self.new, self.exe)
        cleanup_old(self.exe)
        self.assertFalse(os.path.exists(self.exe + OLD_SUFFIX))

    def test_cleanup_without_backup_is_harmless(self):
        cleanup_old(self.exe)  # не должно бросать

    def test_second_update_overwrites_old_backup(self):
        install(self.new, self.exe)
        with open(self.new, "wb") as f:
            f.write(b"newer build")
        install(self.new, self.exe)
        self.assertEqual(self._read(self.exe), b"newer build")
        self.assertEqual(self._read(self.exe + OLD_SUFFIX), b"new build")

    def test_from_source_install_is_refused(self):
        self.assertIsNone(updates.current_exe(), "тесты идут не из сборки")
        with self.assertRaises(RuntimeError):
            install(self.new)


class RelaunchEnvTest(unittest.TestCase):
    PARENT = {
        "PATH": r"C:\Windows",
        "_PYI_APPLICATION_HOME_DIR": r"C:\Temp\_MEI123",
        "_PYI_ARCHIVE_FILE": r"D:\DotaCounters.exe",
        "_PYI_PARENT_PROCESS_LEVEL": "1",
        "_MEIPASS2": r"C:\Temp\_MEI123",
    }

    def test_drops_parent_unpack_dir(self):
        env = relaunch_env(self.PARENT)
        self.assertFalse([k for k in env if k.startswith(("_PYI_", "_MEIPASS"))],
                         "новая версия не должна жить в папке старой")

    def test_asks_bootloader_to_start_fresh(self):
        self.assertEqual(relaunch_env(self.PARENT)["PYINSTALLER_RESET_ENVIRONMENT"], "1")

    def test_keeps_the_rest(self):
        self.assertEqual(relaunch_env(self.PARENT)["PATH"], r"C:\Windows")


if __name__ == "__main__":
    unittest.main(verbosity=2)
