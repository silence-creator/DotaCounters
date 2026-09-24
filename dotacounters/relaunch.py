"""Перезапуск новой версии после обновления с чистым окружением.

Модуль нарочно лёгкий — только стандартная библиотека: main.py зовёт его
раньше, чем грузятся tkinter и сетевой клиент.

Сборка одним файлом распаковывается во временную папку и передаёт путь к ней
своим потомкам через переменные _PYI_*. Новый .exe, унаследовав их, считает
себя потомком и работает из чужой папки, а её удаляет выходящая старая версия —
вместе с сертификатами для HTTPS. Так после обновления до 1.5 сеть не работала
до следующего ручного запуска, и в шапке висел запасной номер патча.
"""

import os
import subprocess
import sys

#: Расширение, которым помечается прежняя версия до удаления.
OLD_SUFFIX = ".old"

#: Метка «запущен с чистым окружением»: второй раз перезапускаться не нужно.
CLEAN_MARK = "DOTACOUNTERS_CLEAN_START"


def relaunch_env(environ=None) -> dict:
    """Окружение для запуска новой версии: без следов распаковки старой."""
    env = {k: v for k, v in (os.environ if environ is None else environ).items()
           if not k.upper().startswith(("_PYI_", "_MEIPASS"))}
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    env[CLEAN_MARK] = "1"
    return env


def launch(exe: str) -> None:
    """Запустить сборку отдельной программой, а не потомком текущей."""
    subprocess.Popen([exe], cwd=os.path.dirname(exe), close_fds=True,
                     env=relaunch_env())


def needs_clean_restart(exe: str | None, environ=None) -> bool:
    """Запустила ли нас старая версия, не очистив окружение.

    Рядом лежит .old — значит, файл только что заменило обновление. Если при
    этом нет метки чистого запуска, перезапускала версия без этого модуля
    (1.5 и старше), и мы живём в её папке распаковки.
    """
    environ = os.environ if environ is None else environ
    return (bool(exe) and environ.get(CLEAN_MARK) != "1"
            and os.path.exists(exe + OLD_SUFFIX))


def heal_inherited_launch() -> bool:
    """Если нужно — перезапуститься начисто. True: этот процесс должен выйти."""
    exe = os.path.abspath(sys.executable) if getattr(sys, "frozen", False) else None
    if not needs_clean_restart(exe):
        return False
    try:
        launch(exe)
    except OSError:
        return False  # не вышло — работаем как есть, это лучше, чем ничего
    return True
