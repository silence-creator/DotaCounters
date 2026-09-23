"""Проверка и установка обновлений из релизов на GitHub.

Установка на Windows устроена так: заменить работающий .exe поверх себя
нельзя, но переименовать его можно. Поэтому новый файл скачивается рядом,
сверяется по контрольной сумме, текущий переименовывается в .old, новый
встаёт на его место, программа перезапускается, а .old удаляется при
следующем запуске.

Обновляется только собранный .exe. При запуске из исходников установка
недоступна — остаётся ссылка на страницу релиза.
"""

import hashlib
import os
import re
import sys
from dataclasses import dataclass

from .net import create_scraper
from .version import APP_VERSION

REPO = "silence-creator/DotaCounters"
LATEST_API = "https://api.github.com/repos/%s/releases/latest" % REPO
RELEASES_PAGE = "https://github.com/%s/releases/latest" % REPO

#: Расширение, которым помечается прежняя версия до удаления.
OLD_SUFFIX = ".old"

_VERSION_RE = re.compile(r"\d+(?:\.\d+)*")


@dataclass
class Update:
    """Доступная версия и файл к ней."""
    version: str
    url: str
    size: int
    sha256: str | None
    notes: str
    page: str = RELEASES_PAGE


def parse_version(text: str) -> tuple:
    """«v1.2» -> (1, 2). Непонятный текст даёт пустой кортеж."""
    found = _VERSION_RE.search(text or "")
    return tuple(int(p) for p in found.group(0).split(".")) if found else ()


def is_newer(remote: str, local: str = APP_VERSION) -> bool:
    """Строго ли remote новее local. Разная длина номера не мешает: 1.2 < 1.2.1."""
    a, b = parse_version(remote), parse_version(local)
    if not a or not b:
        return False
    length = max(len(a), len(b))
    return a + (0,) * (length - len(a)) > b + (0,) * (length - len(b))


def _pick_asset(assets) -> dict | None:
    """Файл релиза для установки: собранный .exe."""
    for asset in assets or []:
        if str(asset.get("name", "")).lower().endswith(".exe"):
            return asset
    return None


def check(scraper=None) -> Update | None:
    """Узнать про новую версию. None — если её нет или GitHub недоступен."""
    try:
        resp = (scraper or create_scraper()).get(LATEST_API, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
    except Exception:
        return None  # нет сети — молча живём дальше

    version = str(data.get("tag_name") or data.get("name") or "")
    if not is_newer(version):
        return None
    asset = _pick_asset(data.get("assets"))
    if not asset:
        return None
    digest = str(asset.get("digest") or "")
    return Update(
        version=_VERSION_RE.search(version).group(0),
        url=asset.get("browser_download_url", ""),
        size=int(asset.get("size") or 0),
        sha256=digest.split("sha256:")[-1] if digest.startswith("sha256:") else None,
        notes=str(data.get("body") or ""),
        page=data.get("html_url") or RELEASES_PAGE,
    )


# ── Установка ─────────────────────────────────────────────────────────────────

def current_exe() -> str | None:
    """Путь к собранному .exe; None при запуске из исходников."""
    return os.path.abspath(sys.executable) if getattr(sys, "frozen", False) else None


def can_install() -> bool:
    """Можно ли заменить файл: это сборка и папка доступна на запись."""
    exe = current_exe()
    return bool(exe) and os.access(os.path.dirname(exe), os.W_OK)


def cleanup_old(exe: str | None = None) -> None:
    """Удалить файл прежней версии, оставшийся после обновления."""
    exe = exe or current_exe()
    if not exe:
        return
    try:
        os.unlink(exe + OLD_SUFFIX)
    except OSError:
        pass  # его либо нет, либо он ещё занят — попробуем в другой раз


def download(update: Update, dest: str, scraper=None, progress=None) -> str:
    """Скачать файл обновления в dest и сверить контрольную сумму.

    progress(получено, всего) вызывается по ходу скачивания.
    Несовпадение суммы — ValueError, файл не сохраняется.
    """
    resp = (scraper or create_scraper()).get(update.url, timeout=120, stream=True)
    if resp.status_code != 200:
        raise IOError("HTTP %d" % resp.status_code)

    digest, received = hashlib.sha256(), 0
    with open(dest, "wb") as out:
        for chunk in resp.iter_content(chunk_size=256 * 1024):
            if not chunk:
                continue
            out.write(chunk)
            digest.update(chunk)
            received += len(chunk)
            if progress:
                progress(received, update.size)

    if update.sha256 and digest.hexdigest() != update.sha256:
        os.unlink(dest)
        raise ValueError("контрольная сумма не совпала: файл повреждён или подменён")
    return dest


def install(downloaded: str, exe: str | None = None) -> str:
    """Поставить скачанный файл на место текущего. Возвращает путь к нему.

    Текущий .exe переименовывается: работающий файл заменить нельзя, а
    переименовать Windows позволяет.
    """
    exe = exe or current_exe()
    if not exe:
        raise RuntimeError("обновление возможно только для собранной версии")
    backup = exe + OLD_SUFFIX
    try:
        os.unlink(backup)
    except OSError:
        pass
    os.replace(exe, backup)
    try:
        os.replace(downloaded, exe)
    except OSError:
        os.replace(backup, exe)  # вернуть как было
        raise
    return exe
